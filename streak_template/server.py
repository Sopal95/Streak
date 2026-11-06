#!/usr/bin/env python3
"""
Local preview server for hello-streak-app, with real Cache-Control headers,
ETag-based conditional GET (304), and gzip — so `bun run start` actually
shows the caching behavior a browser would see, instead of a bare directory
listing with no cache headers at all (what stdlib `http.server` gives you by
default).

Serving: dual-root.
  - public/  is mounted at "/" — this is what's real and cacheable today:
    images, public/styles/tailwind.css, public/assets/js/*.js (the loadPackage
    targets used via <Script>'s gDom.loadPackage()).
  - out/     is the fallback for anything not found under public/ — today
    that's per-page out/<version>/raw-content.json; classified generically by
    extension below so this keeps working as the build pipeline's output
    format evolves.

Usage:
  python3 server.py [port] [directory]

Both are optional — edit PORT/PUBLIC_DIR/OUT_DIR below to change the
defaults without passing CLI args every time. `directory`, if passed,
overrides PUBLIC_DIR only (kept for parity with `python3 -m http.server`'s
own [directory] argument).
"""

import gzip
import hashlib
import http.server
import mimetypes
import os
import sys
import time
from http import HTTPStatus
from io import BytesIO
from pathlib import Path

# ---- Edit these to change the defaults ----
PORT = 8000
ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"
OUT_DIR = ROOT / "out"

# ---- Cache-Control rules ----
# hello-streak-app doesn't content-hash its filenames (no "?v=" query string,
# no per-build path segment) - every rule below is a deliberate tradeoff
# between "cache for real speed" and "don't serve something stale for too
# long", tuned per asset class. Tighten/loosen freely; nothing here depends
# on how the app is actually built.

# Images/fonts under public/ - referenced by filename only (e.g.
# "/images/streak-logo.svg"), never versioned. Bounded staleness window
# rather than `immutable`: if one of these changes without a filename change,
# it'll still serve stale for up to MEDIA_MAX_AGE_SECONDS. ETag is the
# insurance policy for exactly that case - a revalidating client still gets
# the new content once the cache entry expires, without waiting a full year.
MEDIA_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
)
MEDIA_MAX_AGE_SECONDS = 86400  # 1 day

# public/assets/js/*.js - loadPackage() targets (e.g. motion.js), committed
# to the repo and loaded off-thread via Streak's asset worker. Same
# reasoning/tradeoff as media above: filename-stable, not content-hashed.
SCRIPT_ASSET_PREFIX = "/assets/js/"
SCRIPT_ASSET_MAX_AGE_SECONDS = 86400  # 1 day

# Anything served out of out/ (today: raw-content.json; later: whatever the
# build pipeline emits) - this is page content, must always be fresh.
OUT_DIR_CACHE_CONTROL = "no-cache"

NO_CACHE_CACHE_CONTROL = "no-cache"
MEDIA_CACHE_CONTROL = f"public, max-age={MEDIA_MAX_AGE_SECONDS}"
SCRIPT_ASSET_CACHE_CONTROL = f"public, max-age={SCRIPT_ASSET_MAX_AGE_SECONDS}"


def classify_cache_control(url_path: str, served_from_out: bool) -> str:
    url_path = url_path.split("?", 1)[0]

    if served_from_out:
        return OUT_DIR_CACHE_CONTROL
    if url_path.startswith(SCRIPT_ASSET_PREFIX) and url_path.endswith(".js"):
        return SCRIPT_ASSET_CACHE_CONTROL

    filename = url_path.rsplit("/", 1)[-1]
    if filename.lower().endswith(MEDIA_EXTENSIONS):
        return MEDIA_CACHE_CONTROL

    # Conservative default - anything unrecognized always revalidates rather
    # than risk silently serving something stale.
    return NO_CACHE_CACHE_CONTROL


def compute_etag(file_path: Path) -> str:
    stat = file_path.stat()
    # Cheap, stable-per-content-and-mtime identity - not a content hash (that
    # would mean reading the whole file on every request just to build a
    # header), but changes whenever the file is actually rewritten, which is
    # all a local preview server needs to demonstrate real 304 behavior.
    raw = f"{stat.st_mtime_ns}-{stat.st_size}".encode()
    return '"' + hashlib.sha1(raw).hexdigest()[:16] + '"'


def resolve_path(url_path: str):
    """Dual-root lookup: public/ first, then out/. Returns (Path, served_from_out) or None."""
    clean = url_path.split("?", 1)[0].lstrip("/")
    if clean == "":
        clean = "index.html"

    public_candidate = PUBLIC_DIR / clean
    if public_candidate.is_file():
        return public_candidate, False

    out_candidate = OUT_DIR / clean
    if out_candidate.is_dir():
        out_candidate = out_candidate / "index.html"
    if out_candidate.is_file():
        return out_candidate, True

    return None


class CachingGzipHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "HelloStreakCacheServer/1.0"

    def do_GET(self):
        self._handle(send_body=True)

    def do_HEAD(self):
        self._handle(send_body=False)

    def _handle(self, send_body: bool):
        start = time.monotonic()
        resolved = resolve_path(self.path)

        if resolved is None:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            self._log(self.path, HTTPStatus.NOT_FOUND, 0, start, "MISS")
            return

        file_path, served_from_out = resolved
        etag = compute_etag(file_path)

        if_none_match = self.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            self.send_response(HTTPStatus.NOT_MODIFIED)
            self.send_header("Cache-Control", classify_cache_control(self.path, served_from_out))
            self.send_header("ETag", etag)
            self.end_headers()
            self._log(self.path, HTTPStatus.NOT_MODIFIED, 0, start, "HIT (304)")
            return

        self._serve_file(file_path, etag, served_from_out, start, send_body)

    def _serve_file(self, file_path: Path, etag: str, served_from_out: bool, start: float, send_body: bool):
        mime_type, _ = mimetypes.guess_type(str(file_path))
        cache_control = classify_cache_control(self.path, served_from_out)
        accept_encoding = self.headers.get("Accept-Encoding", "")

        raw_content = file_path.read_bytes()

        if "gzip" in accept_encoding:
            compressed = BytesIO()
            with gzip.GzipFile(fileobj=compressed, mode="wb") as gz:
                gz.write(raw_content)
            body = compressed.getvalue()
            content_encoding = "gzip"
        else:
            body = raw_content
            content_encoding = None

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        if content_encoding:
            self.send_header("Content-Encoding", content_encoding)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("ETag", etag)
        self.end_headers()
        if send_body:
            self.wfile.write(body)

        self._log(self.path, HTTPStatus.OK, len(body), start, "MISS")

    def _log(self, path: str, status: int, bytes_sent: int, start: float, verdict: str):
        elapsed_ms = (time.monotonic() - start) * 1000
        # verdict: "HIT (304)" = revalidated, no body sent; "MISS" = full
        # transfer. This is the server-side story - the source of truth for
        # whether caching actually saved a transfer, as opposed to reading
        # tea leaves out of a browser's network panel.
        print(f"[{status}] {verdict:10s} {path}  {bytes_sent}B  {elapsed_ms:.1f}ms", flush=True)

    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        pass  # replaced by _log above


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    if len(sys.argv) > 2:
        PUBLIC_DIR = Path(sys.argv[2]).resolve()

    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, CachingGzipHTTPRequestHandler)
    print(f"Serving {PUBLIC_DIR} (+ {OUT_DIR} fallback) on port {port} (Ctrl+C to stop)...")
    httpd.serve_forever()
