import re
import io
import os
import json
import uuid
import shutil
import hashlib
import zipfile
import asyncio
from collections import Counter
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
import tinycss2
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PreformattedString, Comment
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from html import escape as _esc
from template_transfer import router as transfer_router
from ai_generator import router as ai_router

GENERATED_ROOT = Path("generated_sites")
GENERATED_ROOT.mkdir(exist_ok=True)

TEMPLATE_DIR = Path(os.getenv("STREAK_TEMPLATE_DIR", "streak_template"))

app = FastAPI(title="HTML → Streak.js Exact-Copy Cloner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

KNOWN_LIB_PATTERNS = {
    "aos": "AOS (scroll reveal)",
    "wow.min": "WOW.js (scroll reveal)",
    "wow.js": "WOW.js (scroll reveal)",
    "scrollreveal": "ScrollReveal",
    "sal.js": "sal.js (scroll animations)",
    "gsap": "GSAP",
    "scrolltrigger": "GSAP ScrollTrigger",
    "swiper": "Swiper (carousel)",
    "slick": "Slick (carousel)",
    "splide": "Splide (carousel)",
    "tiny-slider": "Tiny Slider (carousel)",
    "owl.carousel": "Owl Carousel",
    "glightbox": "GLightbox",
    "fancybox": "Fancybox (lightbox)",
    "magnific-popup": "Magnific Popup (lightbox)",
    "lightgallery": "LightGallery",
    "isotope": "Isotope (filtering/masonry)",
    "masonry": "Masonry",
    "particles": "particles.js",
    "typed.min": "Typed.js",
    "typed.js": "Typed.js",
    "lottie": "Lottie animations",
    "jquery": "jQuery",
    "bootstrap.bundle": "Bootstrap JS",
    "bootstrap.min.js": "Bootstrap JS",
}

THIRD_PARTY_SKIP = ("googletagmanager", "google-analytics", "gtag", "fbevents", "facebook.net", "hotjar",
                    "clarity.ms", "doubleclick", "zoho", "zsiq", "intercom", "clevertap", "moengage",
                    "webengage", "talkbot", "gtm.start", "googlesyndication", "tawk.to", "crisp.chat",
                    "hs-scripts", "segment.com", "mixpanel")

TRACKER_IFRAME_HINTS = ("googletagmanager", "doubleclick", "facebook", "google-analytics")

MAX_IMG_WIDTH = 1080
IMG_QUALITY = 70

CALLBACK_RETRIES = 3


class FetchRequest(BaseModel):
    url: str


class ConvertRequest(BaseModel):
    url: str
    tailwind: bool = True
    compare_confidence: bool = True
    confidence_threshold: Optional[float] = None
    build_check: bool = False
    keep_js: bool = False
    callbackUrl: Optional[str] = None


@app.get("/")
async def root():
    return FileResponse("static/index.html")

async def render_page(
    url: str,
    timeout_ms: int = 45000,
    networkidle_timeout_ms: int = 8000,
) -> tuple[str, int]:
    """Render the live page with a real browser and return the final,
    post-JS DOM plus the navigation's HTTP status."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            context = await browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900})
            page = await context.new_page()
            response = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("load", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                pass
            try:
                await page.wait_for_load_state("networkidle", timeout=networkidle_timeout_ms)
            except PlaywrightTimeoutError:
                pass
            try:
                await page.wait_for_timeout(800)
            except Exception:
                pass
            try:
                await page.evaluate("""
                    async () => {
                        await new Promise((resolve) => {
                            let total = 0;
                            const step = 400;
                            const timer = setInterval(() => {
                                window.scrollBy(0, step);
                                total += step;
                                if (total >= document.body.scrollHeight) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 150);
                        });
                    }
                """)
                await page.wait_for_timeout(600)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(300)
            except Exception:
                pass
            html = await page.content()
            status_code = response.status if response else 200
            return html, status_code
        finally:
            await browser.close()


@app.post("/api/fetch")
async def fetch_html(req: FetchRequest):
    """Lightweight stats probe for the UI before the real clone happens in
    /api/convert (which re-renders the page itself with Playwright)."""
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    }

    html, status_code, used_playwright = None, None, False
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(url, headers=headers)
        status_code = response.status_code
        html = response.text
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
        html = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    needs_fallback = html is None or (status_code is not None and status_code >= 400)
    if not needs_fallback:
        soup = BeautifulSoup(html, "html.parser")
        if len(soup.get_text(strip=True)) < 200 and len(soup.find_all()) > 20:
            needs_fallback = True

    if needs_fallback:
        try:
            html, status_code = await render_page(url)
            used_playwright = True
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch {url}: {e}")

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Untitled"
    scripts_preview = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    return {
        "url": url,
        "statusCode": status_code,
        "title": title,
        "htmlLength": len(html),
        "htmlPreview": html[:800],
        "usedPlaywright": used_playwright,
        "tags": {
            "hasNav": bool(soup.find("nav")),
            "hasFooter": bool(soup.find("footer")),
            "hasImages": bool(soup.find("img")),
            "linkCount": len(soup.find_all("a")),
            "tagCount": len(soup.find_all()),
        },
        "detectedLibraries": _detect_libraries(scripts_preview, html),
    }


def _detect_libraries(script_srcs: list[str], html: str) -> list[str]:
    found = set()
    haystacks = [s.lower() for s in script_srcs] + [html.lower()[:200000]]
    for pattern, label in KNOWN_LIB_PATTERNS.items():
        if any(pattern in h for h in haystacks):
            found.add(label)
    return sorted(found)

CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)")
FONT_EXTS = {".woff", ".woff2", ".ttf", ".otf", ".eot"}


def _resolve_lazy_attrs(soup: BeautifulSoup) -> None:
    """Copy lazy-load data-* image URLs into src/srcset/background-image.
    Runs BEFORE URL absolutization."""
    for tag in soup.find_all(["img", "source"]):
        for attr in ("data-src", "data-lazy-src", "data-lazysrc", "data-original"):
            if tag.get(attr):
                tag["src"] = tag[attr]
                break
        for attr in ("data-srcset", "data-lazy-srcset"):
            if tag.get(attr):
                tag["srcset"] = tag[attr]
                break

    for tag in soup.find_all(True):
        for attr in ("data-bg", "data-background", "data-background-image", "data-parallax-bg"):
            val = tag.get(attr)
            if val:
                existing = tag.get("style", "")
                sep = "; " if existing and not existing.strip().endswith(";") else ""
                tag["style"] = f"{existing}{sep}background-image: url('{val}')"
                break


def _absolutize_css_urls(css: str, css_base_url: str) -> str:
    def repl(m):
        quote, path = m.group(1), m.group(2)
        if path.startswith(("data:", "http://", "https://")):
            return m.group(0)
        return f"url({quote}{urljoin(css_base_url, path)}{quote})"
    return CSS_URL_RE.sub(repl, css)


async def _fetch_stylesheet(client: httpx.AsyncClient, href: str) -> str:
    try:
        r = await client.get(href, timeout=10)
        if r.status_code < 400:
            return r.text
    except Exception:
        pass
    return ""


async def inline_all_css(soup: BeautifulSoup, base_url: str) -> str:
    """Fetch every linked stylesheet, absolutize its url() references, and
    return one combined CSS string plus inline <style> blocks, preserving the
    ORIGINAL DOCUMENT ORDER (cascade order matters)."""
    css_nodes = soup.find_all(["link", "style"])

    def _is_stylesheet_link(node: Tag) -> bool:
        rel = node.get("rel")
        return node.name == "link" and bool(rel) and "stylesheet" in rel and bool(node.get("href"))

    hrefs_in_order = [urljoin(base_url, n["href"]) for n in css_nodes if _is_stylesheet_link(n)]

    fetched: dict[str, str] = {}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for href in hrefs_in_order:
            if href in fetched:
                continue
            css = await _fetch_stylesheet(client, href)
            if css:
                fetched[href] = _absolutize_css_urls(css, href)

    combined = []
    for node in css_nodes:
        if _is_stylesheet_link(node):
            href = urljoin(base_url, node["href"])
            if href in fetched:
                combined.append(fetched[href])
        elif node.name == "style":
            combined.append(node.get_text())

    return "\n\n".join(combined)


def _absolutize_dom_urls(soup: BeautifulSoup, base_url: str) -> None:
    for tag in soup.find_all(["img", "source", "video", "audio", "iframe", "embed"]):
        if tag.get("src"):
            tag["src"] = urljoin(base_url, tag["src"])
        if tag.get("srcset"):
            parts = []
            for entry in tag["srcset"].split(","):
                entry = entry.strip()
                if not entry:
                    continue
                bits = entry.split(" ")
                bits[0] = urljoin(base_url, bits[0])
                parts.append(" ".join(bits))
            tag["srcset"] = ", ".join(parts)

    for tag in soup.find_all("a"):
        if tag.get("href"):
            tag["href"] = urljoin(base_url, tag["href"])

    for tag in soup.find_all(style=True):
        tag["style"] = _absolutize_css_urls(tag["style"], base_url)


def _asset_subdir(u: str) -> str:
    ext = os.path.splitext(urlparse(u).path)[1].lower()
    return "assets/fonts" if ext in FONT_EXTS else "images"


def _recompress_image(local_name: str, data: bytes) -> bytes:
    """Shrink big raster images (max MAX_IMG_WIDTH px wide, quality IMG_QUALITY). Same
    extension, so no reference changes. Returns the original bytes if it doesn't get smaller."""
    ext = local_name.rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp") or len(data) <= 100_000:
        return data
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        if getattr(im, "is_animated", False):
            return data
        if im.width > MAX_IMG_WIDTH:
            im = im.resize((MAX_IMG_WIDTH, max(1, int(im.height * MAX_IMG_WIDTH / im.width))))
        fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}[ext]
        if fmt == "JPEG" and im.mode != "RGB":
            im = im.convert("RGB")
        buf = io.BytesIO()
        if fmt == "PNG":
            im.save(buf, fmt, optimize=True)
        else:
            im.save(buf, fmt, quality=IMG_QUALITY, optimize=True)
        return buf.getvalue() if buf.tell() < len(data) else data
    except Exception:
        return data


async def _download_and_localize_assets(soup: BeautifulSoup, css: str, project_dir: Path) -> str:
    """Download every image/media/font asset into public/images or
    public/assets/fonts and rewrite references to root-absolute local paths
    (/images/x.png). Returns the rewritten CSS; the soup is mutated in place."""

    def _local_name(u: str) -> str:
        base = os.path.basename(urlparse(u).path) or "asset"
        base = re.sub(r"[^A-Za-z0-9._-]", "-", base)
        stem, ext = os.path.splitext(base)
        if not ext:
            ext = ".bin"
        digest = hashlib.md5(u.encode()).hexdigest()[:8]
        return f"{stem or 'asset'}-{digest}{ext}"

    candidates: set[str] = set()

    for tag in soup.find_all(["img", "source", "video", "audio"]):
        if tag.get("src", "").startswith(("http://", "https://")):
            candidates.add(tag["src"])
        if tag.get("srcset"):
            for entry in tag["srcset"].split(","):
                u = entry.strip().split(" ")[0]
                if u.startswith(("http://", "https://")):
                    candidates.add(u)
        if tag.name == "video" and tag.get("poster", "").startswith(("http://", "https://")):
            candidates.add(tag["poster"])

    for tag in soup.find_all(style=True):
        for m in CSS_URL_RE.finditer(tag["style"]):
            if m.group(2).startswith(("http://", "https://")):
                candidates.add(m.group(2))

    for m in CSS_URL_RE.finditer(css):
        if m.group(2).startswith(("http://", "https://")):
            candidates.add(m.group(2))

    if not candidates:
        return css

    url_map: dict[str, str] = {}
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for u in candidates:
            try:
                r = await client.get(u, headers={"User-Agent": UA, "Referer": u})
                if r.status_code >= 400 or not r.content:
                    continue
                sub = _asset_subdir(u)
                out_dir = project_dir / "public" / sub
                out_dir.mkdir(parents=True, exist_ok=True)
                local_name = _local_name(u)
                data = r.content
                if sub == "images":
                    data = _recompress_image(local_name, data)
                (out_dir / local_name).write_bytes(data)
                url_map[u] = f"/{sub}/{local_name}"
            except Exception:
                continue

    if not url_map:
        return css

    for tag in soup.find_all(["img", "source", "video", "audio"]):
        if tag.get("src") in url_map:
            tag["src"] = url_map[tag["src"]]
        if tag.get("srcset"):
            parts = []
            for entry in tag["srcset"].split(","):
                entry = entry.strip()
                if not entry:
                    continue
                bits = entry.split(" ")
                bits[0] = url_map.get(bits[0], bits[0])
                parts.append(" ".join(bits))
            tag["srcset"] = ", ".join(parts)
        if tag.name == "video" and tag.get("poster") in url_map:
            tag["poster"] = url_map[tag["poster"]]

    def _swap(m):
        quote, u = m.group(1), m.group(2)
        local = url_map.get(u)
        return f"url({quote}{local}{quote})" if local else m.group(0)

    for tag in soup.find_all(style=True):
        tag["style"] = CSS_URL_RE.sub(_swap, tag["style"])

    return CSS_URL_RE.sub(_swap, css)


def _optimize_img_tags(soup: BeautifulSoup, project_dir: Path) -> None:
    """Performance: reserve space (width/height from the downloaded file),
    lazy-load below-the-fold images, prioritise the hero image."""
    try:
        from PIL import Image
    except Exception:
        Image = None

    for i, img in enumerate(soup.find_all("img")):
        img["decoding"] = "async"
        src = img.get("src", "")
        if Image is not None and src.startswith("/") and not (img.get("width") and img.get("height")):
            p = project_dir / "public" / src.lstrip("/")
            try:
                with Image.open(p) as im:
                    img["width"], img["height"] = str(im.width), str(im.height)
            except Exception:
                pass

        try:
            w = int(str(img.get("width", "0")).strip() or 0)
        except ValueError:
            w = 0

        if i < 3:
            img["loading"] = "eager"
        else:
            img["loading"] = "lazy"
        if i < 4 and w >= 600:  # hero / LCP candidate
            img["loading"] = "eager"
            img["fetchpriority"] = "high"
            img.attrs.pop("decoding", None)


def _find_hero_src(soup: BeautifulSoup) -> str:
    hero = next((i for i in soup.find_all("img") if i.get("fetchpriority") == "high"), None)
    src = hero.get("src", "") if hero else ""
    return src if src.startswith("/") else ""


def _optimize_css(css: str) -> str:
    """font-display: swap on every @font-face, then minify (render-blocking CSS => smaller = faster FCP)."""
    def _face(m):
        body = re.sub(r"font-display\s*:[^;}]*;?", "", m.group(2))
        return m.group(1) + body.rstrip(";") + ";font-display:swap}"
    css = re.sub(r"(@font-face\s*\{)([^}]*)\}", _face, css)
    try:
        import rcssmin  # pip install rcssmin
        return rcssmin.cssmin(css)
    except Exception:
        return css


class CapturedScript:
    __slots__ = ("kind", "src", "content", "attrs")

    def __init__(self, kind: str, src: str = "", content: str = "", attrs: Optional[dict] = None):
        self.kind = kind
        self.src = src
        self.content = content
        self.attrs = attrs or {}


def _capture_scripts(body: Tag, base_url: str) -> list[CapturedScript]:
    """Record every executable <script> in DOM order before tags are stripped.
    Trackers/analytics/chat widgets are skipped."""
    SKIP_TYPES = {"application/ld+json", "application/json", "text/template", "text/x-template"}
    captured: list[CapturedScript] = []
    for tag in body.find_all("script"):
        script_type = (tag.get("type") or "").lower()
        if script_type in SKIP_TYPES:
            continue
        attrs = {}
        if script_type in ("module", "text/javascript", "application/javascript", ""):
            if script_type == "module":
                attrs["type"] = "module"
        else:
            continue
        probe = (tag.get("src") or tag.get_text()[:500]).lower()
        if any(x in probe for x in THIRD_PARTY_SKIP):
            continue
        src = tag.get("src")
        if src:
            captured.append(CapturedScript(kind="external", src=urljoin(base_url, src), attrs=attrs))
        else:
            content = tag.get_text()
            if content.strip():
                captured.append(CapturedScript(kind="inline", content=content, attrs=attrs))
    return captured


def _filter_scripts(scripts: list[CapturedScript], body: Tag) -> list[CapturedScript]:
    """On SPA pages (React/Next/Vue root), the framework bundle would re-render
    over the captured DOM. Replay only known UI libraries, never the app bundle."""
    if body.find(id=["root", "__next", "app", "__nuxt"]) is None:
        return scripts
    keep = []
    for s in scripts:
        src = s.src.lower()
        if s.kind == "external" and any(p in src for p in KNOWN_LIB_PATTERNS) \
                and not any(x in src for x in ("react", "next", "vite", "chunk", "bundle")):
            keep.append(s)
    return keep


async def _download_and_localize_scripts(scripts: list[CapturedScript], project_dir: Path) -> list[dict]:
    """Write scripts into public/assets/js/ (the Streak convention for
    third-party JS). Returns an ordered [{"kind", "path"}] list where path is
    root-absolute (/assets/js/x.js)."""
    scripts_dir = project_dir / "public" / "assets" / "js"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    ordered: list[dict] = []
    inline_counter = 0

    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        for s in scripts:
            kind = "module" if s.attrs.get("type") == "module" else "classic"
            if s.kind == "external":
                local_name = None
                try:
                    r = await client.get(s.src, headers={"User-Agent": UA, "Referer": s.src})
                    if r.status_code < 400 and r.content:
                        base = os.path.basename(urlparse(s.src).path) or "script.js"
                        base = re.sub(r"[^A-Za-z0-9._-]", "-", base)
                        if not base.endswith(".js"):
                            base += ".js"
                        digest = hashlib.md5(s.src.encode()).hexdigest()[:8]
                        local_name = f"{os.path.splitext(base)[0]}-{digest}.js"
                        (scripts_dir / local_name).write_bytes(r.content)
                except Exception:
                    local_name = None
                path = f"/assets/js/{local_name}" if local_name else s.src  # fall back to live URL
                ordered.append({"kind": kind, "path": path})
            else:
                inline_counter += 1
                local_name = f"inline-{inline_counter}.js"
                (scripts_dir / local_name).write_text(s.content, encoding="utf-8")
                ordered.append({"kind": kind, "path": f"/assets/js/{local_name}"})

    return ordered

_WS = " \t\r\n\f"

_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
              "param", "source", "track", "wbr"}

_BOOL_ATTRS = {"disabled", "checked", "selected", "required", "readonly", "multiple", "autoplay",
               "controls", "loop", "muted", "hidden", "async", "defer", "novalidate",
               "allowfullscreen", "playsinline", "open", "default", "reversed", "autofocus",
               "itemscope"}

_NUMERIC_JSX_ATTRS = {"tabIndex", "colSpan", "rowSpan", "maxLength", "minLength", "cols", "rows",
                      "size", "span", "start"}

_SVG_TAGS = {"clippath": "clipPath", "lineargradient": "linearGradient",
             "radialgradient": "radialGradient", "foreignobject": "foreignObject",
             "textpath": "textPath", "fegaussianblur": "feGaussianBlur", "feoffset": "feOffset",
             "feblend": "feBlend", "fecolormatrix": "feColorMatrix", "fecomposite": "feComposite",
             "femerge": "feMerge", "femergenode": "feMergeNode"}

_JSX_ATTRS = {"class": "className", "for": "htmlFor", "tabindex": "tabIndex", "viewbox": "viewBox",
              "readonly": "readOnly", "maxlength": "maxLength", "minlength": "minLength",
              "colspan": "colSpan", "rowspan": "rowSpan", "srcset": "srcSet",
              "autocomplete": "autoComplete", "autoplay": "autoPlay", "crossorigin": "crossOrigin",
              "frameborder": "frameBorder", "allowfullscreen": "allowFullScreen",
              "contenteditable": "contentEditable", "datetime": "dateTime", "enctype": "encType",
              "novalidate": "noValidate", "playsinline": "playsInline",
              "referrerpolicy": "referrerPolicy", "usemap": "useMap", "srclang": "srcLang",
              "charset": "charSet", "cellpadding": "cellPadding", "cellspacing": "cellSpacing",
              "preserveaspectratio": "preserveAspectRatio", "gradientunits": "gradientUnits",
              "gradienttransform": "gradientTransform", "patternunits": "patternUnits",
              "stddeviation": "stdDeviation", "filterunits": "filterUnits", "maskunits": "maskUnits",
              "markerwidth": "markerWidth", "markerheight": "markerHeight", "refx": "refX",
              "refy": "refY", "clippathunits": "clipPathUnits", "spreadmethod": "spreadMethod",
              "xml:space": "xmlSpace", "xlink:href": "xlinkHref", "xmlns:xlink": "xmlnsXlink",
              "http-equiv": "httpEquiv", "accept-charset": "acceptCharset",
              "fetchpriority": "fetchPriority"}

_JSX_IDENT_RE = re.compile(r"^[A-Za-z_][\w-]*$")


def _jsx_attr_name(n: str) -> str:
    n = n.lower()
    if n in _JSX_ATTRS:
        return _JSX_ATTRS[n]
    if n.startswith(("data-", "aria-")):
        return n
    if "-" in n:
        head, *rest = n.split("-")
        return head + "".join(p.capitalize() for p in rest)
    return n


def _css_prop(k: str) -> str:
    if k.startswith("--"):
        return k
    parts = k.lstrip("-").split("-")
    s = parts[0] + "".join(p.capitalize() for p in parts[1:])
    if k.startswith("-") and not k.startswith("-ms-"):
        s = s[:1].upper() + s[1:]
    return s


def _jsx_style_obj(css: str) -> str:
    items, needs_cast = [], False
    for decl in css.split(";"):
        if ":" not in decl:
            continue
        k, v = decl.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if not k:
            continue
        key = _css_prop(k)
        if _JSX_IDENT_RE.match(key) and "-" not in key:
            pass
        else:
            key = json.dumps(key)
            needs_cast = True  # custom properties aren't in React.CSSProperties
        items.append(f"{key}: {json.dumps(v, ensure_ascii=False)}")
    body = "{ " + ", ".join(items) + " }"
    return "{" + body + " as any}" if needs_cast else "{" + body + "}"


def _jsx_open_tag(node: Tag, tag: str) -> str:
    parts, spread = [], {}
    for k, v in node.attrs.items():
        if k.lower().startswith("on"):
            continue
        if isinstance(v, list):
            v = " ".join(v)
        v = str(v)
        name = _jsx_attr_name(k)
        if node.name in ("input", "textarea", "select"):
            name = {"value": "defaultValue", "checked": "defaultChecked"}.get(name, name)
        if not _JSX_IDENT_RE.match(name):
            spread[k] = v
            continue
        if name == "style":
            parts.append(f"style={_jsx_style_obj(v)}")
        elif name in _NUMERIC_JSX_ATTRS and re.fullmatch(r"-?\d+", v.strip()):
            parts.append(f"{name}={{{int(v)}}}")
        elif k.lower() in _BOOL_ATTRS and v in ("", k):
            parts.append(name)
        elif re.search(r'["\\&{}\n<>]', v):
            parts.append(f"{name}={{{json.dumps(v, ensure_ascii=False)}}}")
        else:
            parts.append(f'{name}="{v}"')
    if spread:
        parts.append("{..." + json.dumps(spread, ensure_ascii=False) + " as any}")
    return "<" + " ".join([tag] + parts)


def _jsx_lines(node, depth: int, raw: bool = False) -> list[str]:
    pad = "  " * depth

    if isinstance(node, PreformattedString):
        return []

    if isinstance(node, NavigableString):
        text = str(node)
        if raw:
            return [pad + "{" + json.dumps(text, ensure_ascii=False) + "}"]
        if not text.strip(_WS):
            return [pad + '{" "}'] if text and "\n" not in text else []
        text = re.sub(r"[ \t\r\n\f]+", " ", text)
        if re.search(r"[{}<>]", text) or text != text.strip(_WS):
            return [pad + "{" + json.dumps(text, ensure_ascii=False) + "}"]
        return [pad + text]

    if not isinstance(node, Tag):
        return []

    tag = _SVG_TAGS.get(node.name, node.name)
    head = _jsx_open_tag(node, tag)

    if node.name in _VOID_TAGS:
        return [f"{pad}{head} />"]

    if node.name in ("style", "script", "textarea"):
        body = node.get_text()
        if not body.strip():
            return [f"{pad}{head}></{tag}>"]
        return [f"{pad}{head}>{{{json.dumps(body, ensure_ascii=False)}}}</{tag}>"]

    raw_child = raw or node.name == "pre"
    kids: list[str] = []
    for c in node.contents:
        kids += _jsx_lines(c, depth + 1, raw_child)

    if not kids:
        return [f"{pad}{head}></{tag}>"]
    if (
        len(node.contents) == 1
        and isinstance(node.contents[0], NavigableString)
        and not kids[0].strip().startswith("{")
    ):
        return [f"{pad}{head}>{kids[0].strip()}</{tag}>"]
    return [f"{pad}{head}>", *kids, f"{pad}</{tag}>"]


def _widget_tsx(name: str, chunk_html: str) -> str:
    """Exact-copy widget: the captured markup emitted as real JSX inside a
    fragment (NO wrapper element, so the DOM matches the original)."""
    frag = BeautifulSoup(chunk_html, "html.parser")
    lines: list[str] = []
    for c in frag.contents:
        lines += _jsx_lines(c, 3)
    inner = "\n".join(lines)
    return f"""const {name} = () => {{
  return (
    <>
{inner}
    </>
  );
}};

export default {name};
"""

MIN_WIDGET_CHARS = 600
WRAPPER_TAGS = ("div", "main", "section", "article", "form")
SECTION_TAGS = {"header", "nav", "footer", "aside", "section", "article", "form", "main"}
OVERLAY_TOKENS = ("chakra-portal", "__chakra_env", "talkbot", "zsiq", "chat-widget", "cookie")
GENERIC_LABELS = {"joinhere", "readmore", "viewall", "register", "login", "search", "downloadnow",
                  "learnmore", "clickhere", "getstarted", "submit", "next", "previous"}

_NAME_HINTS = (
    ("breadcrumb", "Breadcrumb"), ("hero", "Hero"), ("banner", "Banner"), ("sidebar", "Sidebar"),
    ("newsletter", "Newsletter"), ("testimonial", "Testimonials"), ("faq", "Faq"),
    ("contact", "Contact"), ("footer", "Footer"), ("header", "Header"), ("menu", "Menu"),
)
_RESERVED_NAMES = {"PageHead", "LegacyScripts", "MainLayout", "WidgetPlaceholder"}


def _pascal(s: str, max_words: int = 3) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", s)
    return "".join(w[:1].upper() + w[1:].lower() for w in words[:max_words])


def _unique_name(base: str, used: dict) -> str:
    names = used.setdefault("__names__", set())
    name, n = base, 1
    while name in names or name in _RESERVED_NAMES:
        n += 1
        name = f"{base}{n}"
    names.add(name)
    return name


def _tag_children(tag: Tag) -> list[Tag]:
    return [c for c in tag.children if isinstance(c, Tag)]


def _has_direct_text(tag: Tag) -> bool:
    return any(isinstance(c, NavigableString) and not isinstance(c, PreformattedString)
               and c.strip("".join([_WS, "\u00a0\u200b\u200c\u200d\ufeff"])) for c in tag.children)


def _tokens(tag: Tag) -> list[str]:
    cls = tag.get("class") or []
    cls = cls if isinstance(cls, list) else [cls]
    return [t.lower() for t in ([tag.get("id") or ""] + cls) if t]


def _has_content(tag: Tag) -> bool:
    return bool(tag.get_text(strip=True)) or tag.find(["img", "svg", "video", "picture", "iframe", "canvas"]) is not None


def _is_overlay(tag: Tag) -> bool:
    return any(o in t for t in _tokens(tag) for o in OVERLAY_TOKENS)


def _is_page_wrapper(kid: Tag, depth: int, container_size: int) -> bool:
    if depth >= 12 or kid.name not in WRAPPER_TAGS:
        return False
    if not _tag_children(kid) or _has_direct_text(kid):
        return False
    return kid.name == "main" or len(str(kid)) >= 0.6 * container_size


def _label_text(kid: Tag) -> Optional[str]:
    """First short English label in the section, e.g. 'Quick Services', 'The Leadership'."""
    for s in kid.stripped_strings:
        words = s.split()
        name = _pascal(s)
        if 1 <= len(words) <= 4 and 4 <= len(s) <= 30 and len(name) >= 4 \
                and name.lower() not in GENERIC_LABELS:
            return name
    return None


def _widget_name(kid: Tag) -> str:
    """Base name from the section's own tag / classes / content. Never 'ContentN'."""
    base = {"header": "Header", "footer": "Footer", "nav": "Nav", "aside": "Sidebar", "form": "Form"}.get(kid.name)
    if base:
        return base
    words = {w for t in _tokens(kid) for w in re.split(r"[-_:\s]+", t)}
    for hint, label in _NAME_HINTS:
        if hint in words:
            return label
    if kid.find("h1") or kid.find("input", attrs={"placeholder": True}):
        return "Hero"
    h = kid.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if h is not None and len(_pascal(h.get_text(" ", strip=True))) >= 4:
        return _pascal(h.get_text(" ", strip=True))
    if kid.get("aria-label") and _pascal(str(kid["aria-label"])):
        return _pascal(str(kid["aria-label"]))
    label = _label_text(kid)
    if label:
        return label
    imgs, links = len(kid.find_all("img")), len(kid.find_all("a"))
    if imgs >= 4:
        return "Gallery"
    if links >= 4:
        return "Links"
    if imgs >= 1:
        return "Feature"
    return "Banner" if len(str(kid)) < 2500 else "Info"


def _finalize_names(nodes: list, used: dict) -> None:
    flat: list = []

    def walk(ns):
        for n in ns:
            flat.append(n) if n[0] == "widget" else walk(n[2])
    walk(nodes)
    for i, n in enumerate(flat):
        if i == 0 and len(flat) > 2 and n[2].count("<a ") >= 3:
            n[1] = "Header"
        elif i == len(flat) - 1 and len(flat) > 2:
            n[1] = "Footer"
        n[1] = _unique_name(n[1], used)


def _plan_nodes(container: Tag, used: dict, depth: int = 0) -> list:
    """Spine wrappers become layout tags; every other child is one widget."""
    total = len(str(container))
    nodes: list = []
    run: list[Tag] = []

    def flush():
        groups: list[list[Tag]] = []
        for k in run:
            if groups and len(str(k)) < MIN_WIDGET_CHARS and k.name not in SECTION_TAGS:
                groups[-1].append(k)  # tiny spacer/strip -> previous section
            else:
                groups.append([k])
        for g in groups:
            names = [_widget_name(k) for k in g]
            name = next((x for x in names if x not in ("Banner", "Info")), names[0])
            nodes.append(["widget", name, "".join(str(k) for k in g)])
        run.clear()

    for kid in _tag_children(container):
        if _is_overlay(kid) or not _has_content(kid):
            continue
        if _is_page_wrapper(kid, depth, total):
            inner = _plan_nodes(kid, used, depth + 1)
            if inner:
                flush()
                nodes.append(("wrap", kid, inner))
                continue
        run.append(kid)
    flush()
    if depth == 0:
        _finalize_names(nodes, used)
    return nodes


def _flatten_widgets(nodes: list):
    for n in nodes:
        if n[0] == "widget":
            yield n[1], n[2]
        else:
            yield from _flatten_widgets(n[2])

def _layout_node_lines(nodes: list, depth: int) -> list[str]:
    pad = "  " * depth
    out: list[str] = []
    for n in nodes:
        if n[0] == "widget":
            out.append(f'{pad}<WidgetPlaceholder id="{n[1]}" type="{n[1]}" />')
        else:
            tag = n[1]
            out.append(f"{pad}{_jsx_open_tag(tag, tag.name)}>")
            out += _layout_node_lines(n[2], depth + 1)
            out.append(f"{pad}</{tag.name}>")
    return out


def _layout_tsx(html_tag: Optional[Tag], body_tag: Tag, nodes: list, has_scripts: bool) -> str:
    html_open = _jsx_open_tag(html_tag, "html") if html_tag is not None else '<html dir="ltr" lang="en"'
    body_open = _jsx_open_tag(body_tag, "body")
    lines = _layout_node_lines(nodes, 4)
    if has_scripts:
        lines.append('        <WidgetPlaceholder id="LegacyScripts" type="LegacyScripts" />')
    body_inner = "\n".join(lines)
    return f"""import {{ WidgetPlaceholder }} from "streak-forge/components";

const MainLayout = () => {{
  return (
    {html_open}>
      <head>
        <WidgetPlaceholder id="PageHead" type="PageHead" />
      </head>
      {body_open}>
{body_inner}
      </body>
    </html>
  );
}};

export default MainLayout;
"""


def _tag_to_html_attr_str(tag: Tag) -> str:
    parts = []
    for k, v in tag.attrs.items():
        if isinstance(v, list):
            v = " ".join(v)
        v = str(v).replace('"', "&quot;")
        parts.append(f'{k}="{v}"')
    return " ".join(parts)


def _collect_head_tags(soup: BeautifulSoup) -> list[Tag]:
    head = soup.find("head")
    collected: list[Tag] = []
    seen_viewport = False
    if head:
        for m in head.find_all("meta"):
            if m.get("charset"):
                continue
            name = (m.get("name") or "").lower()
            prop = (m.get("property") or "").lower()
            if name in ("viewport", "description", "theme-color") or prop.startswith("og:"):
                collected.append(m)
                if name == "viewport":
                    seen_viewport = True
        for link in head.find_all("link"):
            rel_list = link.get("rel") or []
            if any(r in ("icon", "shortcut icon", "apple-touch-icon") for r in rel_list):
                collected.append(link)

    if not seen_viewport:
        vp = soup.new_tag("meta")
        vp.attrs["name"] = "viewport"
        vp.attrs["content"] = "width=device-width, initial-scale=1.0"
        collected.insert(0, vp)

    return collected


def _head_data(head_tags: list[Tag], base_url: str) -> tuple[list[dict], list[dict]]:
    meta, links = [], []
    for t in head_tags:
        a = {k: (" ".join(v) if isinstance(v, list) else str(v)) for k, v in t.attrs.items()}
        if t.name == "meta":
            m = {k: a[k] for k in ("name", "property", "content") if k in a}
            if m:
                meta.append(m)
        elif t.name == "link" and a.get("href"):
            l = {k: a[k] for k in ("rel", "href", "sizes", "type") if k in a}
            l["href"] = urljoin(base_url, l["href"])
            links.append(l)
    return meta, links

PAGE_HEAD_TSX = """type PageHeadProps = {
  data?: {
    title?: string;
    meta?: Record<string, any>[];
    links?: Record<string, any>[];
  };
};

const PageHead = (props: PageHeadProps) => {
  const title = props?.data?.title ?? "";
  const meta = props?.data?.meta ?? [];
  const links = props?.data?.links ?? [];
  return (
    <>
      <meta charSet="UTF-8" />
      <title>{title}</title>
      {meta.map((m, i) => (
        <meta key={i} {...m} />
      ))}
      {links.map((l, i) => (
        <link key={i} {...l} />
      ))}
      <link rel="stylesheet" href="/styles/site.css" />
      <link rel="stylesheet" href="/styles/tailwind.css" />
    </>
  );
};

export default PageHead;
"""

LEGACY_SCRIPTS_TSX = """import { Script } from "streak-forge/components";

type LegacyScriptsProps = {
  data?: { scripts?: { kind: string; path: string }[] };
};

const LegacyScripts = (props: LegacyScriptsProps) => {
  const scripts = props?.data?.scripts ?? [];
  return (
    <Script id="legacy-scripts" options={{ scripts }}>
      {(gDom: any, options: any) => {
        // gDom === window (+ Streak helpers)
        if (gDom.__legacyScriptsInjected) return;
        gDom.__legacyScriptsInjected = true;

        const entries: any[] = (options && options.scripts) || [];
        const classic = entries.filter((e: any) => e.kind === "classic");
        const modules = entries.filter((e: any) => e.kind === "module");

        const loadOne = (entry: any) =>
          new Promise<void>((resolve) => {
            const el = document.createElement("script");
            el.src = entry.path;
            el.async = false;
            el.onload = () => resolve();
            el.onerror = () => resolve(); // one broken script must not stop the rest
            document.body.appendChild(el);
          });

        classic
          .reduce((chain: Promise<void>, entry: any) => chain.then(() => loadOne(entry)), Promise.resolve())
          .then(() => {
            modules.forEach((entry: any) => {
              const el = document.createElement("script");
              el.type = "module";
              el.src = entry.path;
              document.body.appendChild(el);
            });
            // real DOMContentLoaded/load already fired; libraries wait for them to init
            document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true, cancelable: true }));
            window.dispatchEvent(new Event("load"));
          });
      }}
    </Script>
  );
};

export default LegacyScripts;
"""

HANDLER_TEST_TS = """import { expect, test } from "bun:test";
import handler from "../handlers/HomeDataHandler";

test("HomeDataHandler returns status 200 with PageHead data", async () => {
  const data: any = await handler();
  expect(data.status).toBe(200);
  expect(data.PageHead).toBeDefined();
  expect(typeof data.PageHead.title).toBe("string");
});
"""

TAILWIND_CONFIG_JS = """/** @type {import('tailwindcss').Config} */
const v = (n) => `hsl(var(--${n}) / <alpha-value>)`;
export default {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}", "./public/assets/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), surface: v("surface"), ink: v("ink"), muted: v("muted"), hair: v("hair"),
        teal: "#00b4a6", border: v("border"), input: v("input"), ring: v("ring"),
        background: v("background"), foreground: v("foreground"), card: v("card"), popover: v("popover"),
        primary: { DEFAULT: v("primary"), foreground: v("primary-foreground") },
        secondary: { DEFAULT: v("secondary"), foreground: v("secondary-foreground") },
        accent: { DEFAULT: v("accent"), foreground: v("accent-foreground") },
        destructive: { DEFAULT: v("destructive"), foreground: v("destructive-foreground") },
      },
      fontFamily: {
        display: ["Cabinet Grotesk", "Inter", "sans-serif"],
        sans: ["Satoshi", "Inter", "sans-serif"],
      },
      borderRadius: { sm: "4px", md: "6px", lg: "8px" },
      animation: {
        "accordion-down": "accordion-down .2s ease-out",
        "accordion-up": "accordion-up .2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
"""

TAILWIND_INPUT_CSS = "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"

PERF_CSS = """
/* perf (zero specificity so site classes like .h-12 / .w-10 always win) */
:where(img[width][height]) { height: auto; max-width: 100%; }
img[style*="opacity: 0"], img[style*="opacity:0"] { opacity: 1 !important; }
"""

NETLIFY_TOML = """[build]
  command = "echo 'static site, no build'"
  publish = "public"

[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"

[[headers]]
  for = "/images/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/styles/*"
  [headers.values]
    Cache-Control = "public, max-age=3600"
"""

EXACT_INPUT_CSS = (
    "/* Exact-copy mode: the original CSS lives in public/styles/site.css.\n"
    "   Add Tailwind directives here if you start converting widgets. */\n"
)

FALLBACK_PKG = {
    "name": "streak-site",
    "version": "1.0.0",
    "type": "module",
    "main": "index.js",
    "scripts": {
        "start": "python3 server.py",
        "css-build": "tailwindcss -i ./src/common/styles/input.css -o ./public/styles/tailwind.css",
        "css-dev": "tailwindcss -i ./src/common/styles/input.css -o ./public/styles/tailwind.css --watch",
        "dev:streak": "streak-forge dev",
        "dev": 'concurrently -k -n TAILWIND,STREAK -c blue,green "bun run css-dev" "bun run dev:streak"',
        "build": "bun run css-build && streak-forge pre-build",
        "test": "bun test",
        "typecheck": "tsc --noEmit",
    },
    "dependencies": {"streak-forge": "beta"},
    "devDependencies": {
        "@types/bun": "^1.4.0",
        "bun": "^1.2.21",
        "concurrently": "^9.2.1",
        "tailwindcss": "^3.4.17",
        "tailwindcss-animate": "^1.0.7",
    },
}

FALLBACK_TSCONFIG = {
    "compilerOptions": {
        "target": "ESNext", "module": "ESNext", "moduleResolution": "bundler",
        "jsx": "react-jsx", "strict": True, "skipLibCheck": True, "noEmit": True,
        "types": ["bun"],
    },
    "include": ["src"],
}


def _common_handler_ts(source_url: str, title: str) -> str:
    data = {"site": {"title": title, "sourceUrl": source_url}}
    return (
        "const getCommonData = async () => {\n  return "
        + json.dumps(data, indent=2, ensure_ascii=False).replace("\n", "\n  ")
        + ";\n};\n\nexport default getCommonData;\n"
    )


def _bootstrap_project(project_dir: Path) -> dict:
    """Create the hello-streak-app skeleton. Prefers a copy of the real repo
    (STREAK_TEMPLATE_DIR) so tsconfig/eslint/server.py/validator match exactly;
    demo widgets, layout, tests and assets are removed. Returns package.json dict."""
    if TEMPLATE_DIR.is_dir():
        shutil.copytree(
            TEMPLATE_DIR, project_dir, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "node_modules", "out", "dist", ".DS_Store"),
        )
        for rel in ("src/widgets", "src/layouts", "src/tests"):
            shutil.rmtree(project_dir / rel, ignore_errors=True)
        for rel in ("src/handlers/HomeDataHandler.ts", "public/images/streak-logo.svg",
                    "public/assets/js/motion.js", "src/scripts/test-render.ts"):
            (project_dir / rel).unlink(missing_ok=True)
        pkg_path = project_dir / "package.json"
        pkg = json.loads(pkg_path.read_text(encoding="utf-8")) if pkg_path.exists() else json.loads(json.dumps(FALLBACK_PKG))
    else:
        pkg = json.loads(json.dumps(FALLBACK_PKG))
        (project_dir / "tsconfig.json").write_text(json.dumps(FALLBACK_TSCONFIG, indent=2), encoding="utf-8")
        (project_dir / ".gitignore").write_text("node_modules\nout\n", encoding="utf-8")

    pkg.get("scripts", {}).pop("test-render", None)

    for rel in ("src/widgets", "src/layouts", "src/handlers", "src/tests", "src/common/styles",
                "public/styles", "public/images", "public/assets/js"):
        (project_dir / rel).mkdir(parents=True, exist_ok=True)
    return pkg

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")
TAILWIND_RULES = Path("tailwind.md").read_text(encoding="utf-8") if Path("tailwind.md").exists() else ""


def _strip_fences(s: str) -> str:
    return re.sub(r"^```[a-zA-Z]*\n|\n```$", "", s.strip()).strip()


CSS_TW_BASE_PROMPT = """You convert plain CSS from a website into Tailwind CSS v3.4 component CSS for an `input.css` file.

Input: a chunk of CSS. Output: ONLY CSS. No markdown fences, no explanation, no @tailwind directives, no @layer wrapper.

Conversion rules:
- Rewrite each project-specific rule with the SAME selector (keep :hover, ::before, descendant selectors, attribute selectors exactly) and express its declarations with Tailwind utilities in `@apply`, e.g. `.cta { @apply inline-flex items-center gap-2 rounded-md px-6 py-3 font-semibold; }`.
- For @media (min-width) blocks, use sm:/md:/lg:/xl: variants inside @apply when the selector is a plain class; otherwise keep the @media block and put @apply inside it.
- Any declaration that @apply cannot express with a DEFAULT Tailwind utility stays as a plain CSS property in the SAME rule, after the @apply line. This includes exact values (min-height: 88vh; font-size: 1.05rem; width: 600px;), custom properties, hsl(var(--x)) colors, hex colors, clamp(), gradients, animation, content, mask, grid-template-areas and font-family. NEVER drop a declaration, and NEVER approximate a value that the page visibly depends on by using a non-equal utility.
- Use a Tailwind utility only when it is equal or the nearest default scale value for spacing/typography/radius/shadow that is not brand-critical; otherwise use plain CSS.
- Do not use `!important`, group-*, peer-*, or Tailwind v4-only utilities.
- DROP only rules that are standard Tailwind v3 DEFAULT output: preflight/base resets, `*,::before,::after{--tw-...}` variable blocks, and default-scale utility classes (e.g. `.flex{display:flex}`, `.md\\:p-8{...}`), because Tailwind regenerates them from the markup.
- KEEP as plain CSS, unchanged, any utility-looking class that uses a custom value (colors via var(--...) or hsl(var(--...)), custom hex colors, custom font families, sizes outside the default scale, e.g. `.bg-surface`, `.text-ink`, `.min-h-\\[88vh\\]`).
- Keep :root, html, body rules, CSS variables and @keyframes as plain CSS unchanged.
- Preserve rule order.
"""

CSS_TW_OVERRIDE = """
OVERRIDES (these win over anything above):
- This is a CSS-to-CSS conversion. The markup is NOT rewritten, so ignore the "Output Model" section's requirement to rename classes: KEEP the original selectors.
- NEVER use arbitrary values (`[...]`) inside `@apply`. Put exact values in plain CSS properties instead.
- Use only DEFAULT Tailwind tokens inside `@apply`. Do not invent tokens such as w-150, h-17, text-primary, text-ink, bg-teal.
- Do not use hex colors or `[]` colors inside `@apply`; use the nearest default palette color or a plain CSS declaration.
"""

CSS_TW_SYSTEM_PROMPT = (
    CSS_TW_BASE_PROMPT
    + "\nPROJECT RULES (tailwind.md):\n"
    + TAILWIND_RULES
    + "\n"
    + CSS_TW_OVERRIDE
)

PLAIN_AT_RULES = ("font-face", "keyframes", "-webkit-keyframes", "property")
APPLY_ARBITRARY_RE = re.compile(r"@apply[^;}]*\[")


def _split_css_for_llm(css: str, max_chars: int = 9000) -> tuple[list[str], list[str], list[str]]:
    """Returns (imports, plain_at_rules, chunks). @font-face/@keyframes/@property
    never go through the LLM; @import must stay at the top of the file."""
    imports, plain, chunks, cur = [], [], [], ""
    for r in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if r.type == "at-rule" and r.lower_at_keyword == "import":
            imports.append(r.serialize())
            continue
        if r.type == "at-rule" and r.lower_at_keyword == "charset":
            continue
        if r.type == "at-rule" and r.lower_at_keyword in PLAIN_AT_RULES:
            plain.append(r.serialize())
            continue
        if r.type not in ("qualified-rule", "at-rule"):
            continue
        s = r.serialize()
        if cur and len(cur) + len(s) > max_chars:
            chunks.append(cur)
            cur = ""
        cur += s + "\n"
    if cur:
        chunks.append(cur)
    return imports, plain, chunks


async def _css_chunk_to_tailwind(client: httpx.AsyncClient, idx: int, chunk: str) -> Optional[str]:
    user = chunk
    for attempt in range(3):
        try:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={
                    "model": OPENROUTER_MODEL,
                    "temperature": 0,
                    "max_tokens": 16000,
                    "messages": [
                        {"role": "system", "content": CSS_TW_SYSTEM_PROMPT},
                        {"role": "user", "content": user},
                    ],
                },
            )
            r.raise_for_status()
            out = _strip_fences(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"[css->tailwind chunk {idx}] attempt {attempt + 1} API error: {e}")
            continue

        problems = []
        if out.count("{") != out.count("}"):
            problems.append("unbalanced braces")
        if APPLY_ARBITRARY_RE.search(out):
            problems.append("arbitrary [] value inside @apply")
        if re.search(r"@tailwind|@layer", out):
            problems.append("@tailwind/@layer present")
        if not problems:
            return out
        print(f"[css->tailwind chunk {idx}] attempt {attempt + 1} rejected: {problems}")
        user = (
            chunk
            + "\n\nYour previous answer was rejected: "
            + ", ".join(problems)
            + ". Redo it. Put exact/arbitrary values in plain CSS properties, never inside @apply. Output balanced CSS only."
        )
    print(f"[css->tailwind chunk {idx}] failed, keeping original CSS for this chunk")
    return None
_PX2KEY = {0: "0", 1: "px", 2: "0.5", 4: "1", 6: "1.5", 8: "2", 10: "2.5", 12: "3", 14: "3.5",
           16: "4", 20: "5", 24: "6", 28: "7", 32: "8", 36: "9", 40: "10", 44: "11", 48: "12",
           56: "14", 64: "16", 80: "20", 96: "24", 112: "28", 128: "32", 144: "36", 160: "40",
           176: "44", 192: "48", 208: "52", 224: "56", 240: "60", 256: "64", 288: "72",
           320: "80", 384: "96"}

_KW = {
    "display": {"block": "block", "inline-block": "inline-block", "inline": "inline", "flex": "flex",
                "inline-flex": "inline-flex", "grid": "grid", "none": "hidden", "table": "table"},
    "position": {k: k for k in ("static", "fixed", "absolute", "relative", "sticky")},
    "flex-direction": {"row": "flex-row", "column": "flex-col", "row-reverse": "flex-row-reverse",
                       "column-reverse": "flex-col-reverse"},
    "flex-wrap": {"wrap": "flex-wrap", "nowrap": "flex-nowrap"},
    "align-items": {"center": "items-center", "flex-start": "items-start", "flex-end": "items-end",
                    "stretch": "items-stretch", "baseline": "items-baseline"},
    "justify-content": {"center": "justify-center", "flex-start": "justify-start", "flex-end": "justify-end",
                        "space-between": "justify-between", "space-around": "justify-around",
                        "space-evenly": "justify-evenly"},
    "text-align": {k: f"text-{k}" for k in ("left", "center", "right", "justify")},
    "font-weight": {"100": "font-thin", "200": "font-extralight", "300": "font-light", "400": "font-normal",
                    "500": "font-medium", "600": "font-semibold", "700": "font-bold", "800": "font-extrabold",
                    "900": "font-black", "bold": "font-bold", "normal": "font-normal"},
    "font-style": {"italic": "italic", "normal": "not-italic"},
    "text-transform": {"uppercase": "uppercase", "lowercase": "lowercase", "capitalize": "capitalize",
                       "none": "normal-case"},
    "text-decoration": {"none": "no-underline", "underline": "underline", "line-through": "line-through"},
    "overflow": {k: f"overflow-{k}" for k in ("hidden", "auto", "visible", "scroll")},
    "overflow-x": {k: f"overflow-x-{k}" for k in ("hidden", "auto", "visible", "scroll")},
    "overflow-y": {k: f"overflow-y-{k}" for k in ("hidden", "auto", "visible", "scroll")},
    "cursor": {"pointer": "cursor-pointer", "default": "cursor-default", "not-allowed": "cursor-not-allowed"},
    "list-style": {"none": "list-none"},
    "list-style-type": {"none": "list-none"},
    "white-space": {"nowrap": "whitespace-nowrap", "normal": "whitespace-normal", "pre": "whitespace-pre"},
    "text-overflow": {"ellipsis": "text-ellipsis", "clip": "text-clip"},
    "visibility": {"hidden": "invisible", "visible": "visible"},
    "box-sizing": {"border-box": "box-border", "content-box": "box-content"},
    "object-fit": {k: f"object-{k}" for k in ("cover", "contain", "fill")},
    "pointer-events": {"none": "pointer-events-none", "auto": "pointer-events-auto"},
    "flex": {"1": "flex-1", "1 1 0%": "flex-1", "none": "flex-none", "auto": "flex-auto"},
    "flex-shrink": {"0": "shrink-0", "1": "shrink"},
    "flex-grow": {"0": "grow-0", "1": "grow"},
    "z-index": {str(z): f"z-{z}" for z in (0, 10, 20, 30, 40, 50)},
    "border-radius": {"0": "rounded-none", "2px": "rounded-sm", "4px": "rounded", "6px": "rounded-md",
                      "8px": "rounded-lg", "12px": "rounded-xl", "16px": "rounded-2xl",
                      "24px": "rounded-3xl", "9999px": "rounded-full"},
}

_SP_PROPS = {"margin": "m", "margin-top": "mt", "margin-right": "mr", "margin-bottom": "mb",
             "margin-left": "ml", "padding": "p", "padding-top": "pt", "padding-right": "pr",
             "padding-bottom": "pb", "padding-left": "pl", "gap": "gap", "column-gap": "gap-x",
             "row-gap": "gap-y", "width": "w", "height": "h"}


def _tw_space(prefix: str, val: str) -> Optional[str]:
    if val == "auto":
        return f"{prefix}-auto" if prefix[0] in "mwh" else None
    if val == "100%" and prefix in ("w", "h"):
        return f"{prefix}-full"
    m = re.fullmatch(r"(-?)(\d*\.?\d+)(px|rem)?", val)
    if not m:
        return None
    neg, num, unit = m.groups()
    n = float(num)
    if unit == "rem":
        n *= 16
    elif unit is None and n != 0:
        return None
    key = _PX2KEY.get(int(n)) if n == int(n) else None
    if key is None:
        return None
    if neg:
        return None if prefix[0] not in "m" else (f"{prefix}-{key}" if key == "0" else f"-{prefix}-{key}")
    return f"{prefix}-{key}"


_NO_APPLY_PROPS = {"display", "position", "visibility", "text-decoration", "text-transform", "font-style"}


def _tw_decl(prop: str, val: str) -> Optional[str]:
    if prop in _NO_APPLY_PROPS:
        return None
    if prop in _KW:
        return _KW[prop].get(val)
    if prop in _SP_PROPS:
        parts = val.split()
        pre = _SP_PROPS[prop]
        if len(parts) == 1:
            return _tw_space(pre, parts[0])
        if len(parts) == 2 and prop in ("margin", "padding"):
            y, x = _tw_space(pre + "y", parts[0]), _tw_space(pre + "x", parts[1])
            return f"{y} {x}" if y and x else None
    return None

_UTIL_RE = re.compile(
    r"^\.-?(?:[mp][trblxy]?|gap(?:-[xy])?|[wh]|(?:min|max)-[wh]|z|inset(?:-[xy])?|top|left|right|bottom|"
    r"col-span|grid-cols|space-[xy]|duration|opacity|rounded(?:-[a-z]{1,2})?|border(?:-[trblxy])?|text|font|"
    r"leading|tracking|bg|shadow|ring|flex|basis|translate-[xy]|rotate|items|justify|self|overflow(?:-[xy])?|"
    r"object|outline|backdrop|cursor|list|fill|ease|transition|animate|aspect|shrink|grow|whitespace|pointer-events|"
    r"underline-offset|fade-in|fade-out|zoom-in|zoom-out|slide-in|slide-out)-[\w.-]+$"
    r"|^\.(?:block|inline|inline-flex|flex|grid|table|hidden|visible|invisible|static|fixed|absolute|relative|"
    r"sticky|underline|uppercase|container|sr-only|transform|filter|border|outline|resize|running|grow|shrink|"
    r"select-none|touch-none|break-words|border-collapse|caption-bottom|align-middle|self-start|shadow|rounded|"
    r"transition)$"
)


def _is_util_sel(sel: str) -> bool:
    parts = [p.strip().split(">")[0] for p in sel.split(",")]
    return all(
        ("\\" in p or _UTIL_RE.match(p)) and not p.startswith(".cursor-dot")
        for p in parts
    )

def _selector_classes(sel: str) -> set[str]:
    """All class names in a selector, including escaped ones (.md\\:flex -> md:flex)."""
    out = set()
    for m in re.finditer(r"\.((?:\\.|[A-Za-z0-9_-])+)", sel):
        out.add(re.sub(r"\\(.)", r"\1", m.group(1)))
    return out


def _convert_rule(rule, compiled: bool = False) -> str:
    if rule.type == "at-rule":
        if rule.lower_at_keyword == "layer":
            if rule.content is None:
                return ""
            return "\n".join(filter(None, (_convert_rule(r, compiled) for r in tinycss2.parse_rule_list(
                rule.content, skip_comments=True, skip_whitespace=True))))
        if rule.lower_at_keyword in ("media", "supports") and rule.content is not None:
            inner = "\n".join(filter(None, (_convert_rule(r, compiled) for r in tinycss2.parse_rule_list(
                rule.content, skip_comments=True, skip_whitespace=True))))
            if not inner.strip():
                return ""
            return f"@{rule.at_keyword} {tinycss2.serialize(rule.prelude).strip()} {{\n{inner}\n}}"
        if rule.content is None and rule.lower_at_keyword not in ("import", "charset"):
            return ""
        return rule.serialize()
    if rule.type != "qualified-rule":
        return ""
    sel = tinycss2.serialize(rule.prelude).strip()
    if compiled:
        return rule.serialize()
    sel_classes = _selector_classes(sel)
    decls = [d for d in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
             if d.type == "declaration"]
    counts = Counter(d.lower_name for d in decls)
    utils, plain = [], []
    for d in decls:
        val = tinycss2.serialize(d.value).strip().lower()
        u = None
        if not d.important and counts[d.lower_name] == 1 and not d.name.startswith("--"):
            u = _tw_decl(d.lower_name, val)
        if u and any(tok in sel_classes for tok in u.split()):
            u = None
        if u:
            utils.append(u)
        else:
            plain.append(f"{d.name}: {tinycss2.serialize(d.value).strip()}{' !important' if d.important else ''};")
    body = ([f"@apply {' '.join(utils)};"] if utils else []) + plain
    return f"{sel} {{\n  " + "\n  ".join(body) + "\n}"

_APPLY_RE = re.compile(r"@apply\s+([^;]+);")
_RULE_RE = re.compile(r"([^{}@]+)\{([^{}]*)\}")

def _drop_circular_applies(css: str) -> str:
    """Last line of defense: remove only the @apply tokens that name a class
    present in the rule's own selector. Other tokens and plain CSS stay."""
    def fix(m):
        sel, body = m.group(1), m.group(2)
        classes = _selector_classes(sel)

        def ap(a):
            toks = a.group(1).split()
            keep = [t for t in toks
                    if t not in classes and t.split(":")[-1].lstrip("-") not in classes]
            if len(keep) == len(toks):
                return a.group(0)
            print(f"[input.css] removed circular tokens in `{sel.strip()}`: {sorted(set(toks) - set(keep))}")
            return f"@apply {' '.join(keep)};" if keep else ""

        return f"{sel}{{{_APPLY_RE.sub(ap, body)}}}"
    return _RULE_RE.sub(fix, css)

async def _convert_css_to_input_css(css: str) -> tuple[str, list[int]]:
    compiled = "--tw-border-spacing-x" in css  # site already ships compiled Tailwind
    imports, plain, body = [], [], []
    for r in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if r.type == "at-rule" and r.lower_at_keyword == "import":
            imports.append(r.serialize())
        elif r.type == "at-rule" and r.lower_at_keyword == "charset":
            continue
        elif r.type == "at-rule" and r.lower_at_keyword in PLAIN_AT_RULES:
            plain.append(r.serialize())
        elif r.type in ("qualified-rule", "at-rule"):
            out = _convert_rule(r, compiled)
            if out:
                body.append(out)
    input_css = (
        ("\n".join(imports) + "\n\n" if imports else "")
        + TAILWIND_INPUT_CSS + "\n" + "\n".join(plain) + "\n\n" + "\n\n".join(body) + "\n"
    )
    input_css = _drop_circular_applies(input_css)
    return input_css, []

_PREVIEW_FORCE_VISIBLE_CSS = """
/* static-preview-only: no JS runtime here, so force reveal-on-scroll content visible.
   Does NOT ship in the Streak project (LegacyScripts replays the real libraries). */
*, *::before, *::after {
  animation-play-state: paused !important;
  animation-delay: 0s !important;
  animation-duration: 0s !important;
  transition: none !important;
}
[style*="opacity: 0"], [style*="opacity:0"],
[class*="fade"], [class*="reveal"], [class*="animate"], [class*="aos-"],
.hidden, .invisible, [data-aos], [data-animate] {
  opacity: 1 !important;
  visibility: visible !important;
  transform: none !important;
}
"""


def _build_preview_html(title: str, head_tags: list[Tag], css: str, body_html: str,
                        html_tag: Optional[Tag], body_tag: Tag) -> str:
    head_extra = "\n".join(str(t) for t in head_tags)
    html_attrs = _tag_to_html_attr_str(html_tag) if html_tag is not None else 'lang="en"'
    body_attrs = _tag_to_html_attr_str(body_tag)
    return f"""<!DOCTYPE html>
<html {html_attrs}>
<head>
<meta charset="UTF-8">
<title>{title}</title>
{head_extra}
<style>{css}</style>
<style>{_PREVIEW_FORCE_VISIBLE_CSS}</style>
</head>
<body {body_attrs}>
{body_html}
</body>
</html>"""

DEFAULT_MIN_CONFIDENCE = float(os.getenv("CLONE_MIN_CONFIDENCE", "80"))

CONFIDENCE_BANDS = [
    (90.0, "excellent"),
    (75.0, "good"),
    (60.0, "fair"),
    (0.0, "poor"),
]

METRIC_THRESHOLDS = {"visual": 80.0, "text": 90.0, "structure": 85.0, "layout": 85.0}
METRIC_WEIGHTS = {"visual": 0.50, "text": 0.20, "structure": 0.20, "layout": 0.10}

PIXEL_TOLERANCE = 24
MAX_COMPARE_HEIGHT = 10000

_PAGE_METRICS_JS = """
() => {
  const text = (document.body.innerText || "").replace(/\\s+/g, " ").trim();
  const imgs = Array.from(document.images);
  return {
    text: text.slice(0, 300000),
    elements: document.body.querySelectorAll("*:not(script):not(style):not(noscript)").length,
    images: imgs.length,
    imagesLoaded: imgs.filter(i => i.complete && i.naturalWidth > 0).length,
    links: document.links.length,
    headings: document.querySelectorAll("h1,h2,h3,h4,h5,h6").length,
    height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
  };
}
"""


def _ratio_score(a: float, b: float) -> float:
    if a == 0 and b == 0:
        return 1.0
    hi = max(a, b)
    return (min(a, b) / hi) if hi else 1.0


def _text_similarity(a: str, b: str) -> float:
    wa, wb = Counter(a.lower().split()), Counter(b.lower().split())
    na, nb = sum(wa.values()), sum(wb.values())
    if max(na, nb) == 0:
        return 1.0
    return sum((wa & wb).values()) / max(na, nb)


def _confidence_label(score: float) -> str:
    for floor, label in CONFIDENCE_BANDS:
        if score >= floor:
            return label
    return "poor"


def _visual_similarity(shot_a: bytes, shot_b: bytes) -> float:
    from PIL import Image, ImageChops  # pip install pillow

    a = Image.open(io.BytesIO(shot_a)).convert("RGB")
    b = Image.open(io.BytesIO(shot_b)).convert("RGB")
    w, h = max(a.width, b.width), min(max(a.height, b.height), MAX_COMPARE_HEIGHT)

    def _pad(img):
        canvas = Image.new("RGB", (w, h), (255, 255, 255))
        canvas.paste(img.crop((0, 0, min(img.width, w), min(img.height, h))), (0, 0))
        return canvas

    diff = ImageChops.difference(_pad(a), _pad(b)).convert("L")
    hist = diff.histogram()
    total = sum(hist) or 1
    return sum(hist[: PIXEL_TOLERANCE + 1]) / total


async def _capture_page(page, full_height_cap: int = MAX_COMPARE_HEIGHT) -> tuple[bytes, dict]:
    metrics = await page.evaluate(_PAGE_METRICS_JS)
    height = max(1, min(int(metrics["height"]), full_height_cap))
    shot = await page.screenshot(
        full_page=True,
        clip={"x": 0, "y": 0, "width": 1440, "height": height},
    )
    return shot, metrics


async def _scroll_through(page) -> None:
    try:
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let total = 0;
                    const timer = setInterval(() => {
                        window.scrollBy(0, 400);
                        total += 400;
                        if (total >= document.body.scrollHeight) { clearInterval(timer); resolve(); }
                    }, 100);
                });
            }
        """)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(600)
    except Exception:
        pass


async def _measure_clone_confidence(url: str, preview_html: str, min_confidence: float) -> dict:
    """Render the original URL and the static preview in the same 1440px
    viewport and score the match. Never raises."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                context = await browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900})

                orig = await context.new_page()
                await orig.goto(url, timeout=45000, wait_until="domcontentloaded")
                try:
                    await orig.wait_for_load_state("networkidle", timeout=8000)
                except PlaywrightTimeoutError:
                    pass
                await _scroll_through(orig)
                orig_shot, orig_m = await _capture_page(orig)

                clone = await context.new_page()
                await clone.set_content(preview_html, wait_until="load", timeout=45000)
                try:
                    await clone.wait_for_load_state("networkidle", timeout=8000)
                except PlaywrightTimeoutError:
                    pass
                await clone.wait_for_timeout(600)
                clone_shot, clone_m = await _capture_page(clone)
            finally:
                await browser.close()

        visual = _visual_similarity(orig_shot, clone_shot) * 100
        text = _text_similarity(orig_m["text"], clone_m["text"]) * 100
        structure = (
            sum(_ratio_score(orig_m[k], clone_m[k]) for k in ("elements", "images", "links", "headings")) / 4
        ) * 100
        layout = _ratio_score(orig_m["height"], clone_m["height"]) * 100

        scores = {"visual": visual, "text": text, "structure": structure, "layout": layout}
        overall = sum(scores[k] * METRIC_WEIGHTS[k] for k in scores)

        return {
            "score": round(overall, 2),
            "label": _confidence_label(overall),
            "threshold": min_confidence,
            "passed": overall >= min_confidence,
            "basis": "original page vs generated static preview (same markup + CSS as the Streak widgets, before Tailwind conversion)",
            "metrics": {
                k: {
                    "score": round(scores[k], 2),
                    "threshold": METRIC_THRESHOLDS[k],
                    "weight": METRIC_WEIGHTS[k],
                    "passed": scores[k] >= METRIC_THRESHOLDS[k],
                }
                for k in scores
            },
            "bands": {label: floor for floor, label in CONFIDENCE_BANDS},
            "details": {
                "original": {k: orig_m[k] for k in ("elements", "images", "imagesLoaded", "links", "headings", "height")},
                "clone": {k: clone_m[k] for k in ("elements", "images", "imagesLoaded", "links", "headings", "height")},
                "pixelTolerance": PIXEL_TOLERANCE,
                "maxCompareHeight": MAX_COMPARE_HEIGHT,
            },
        }
    except Exception as e:
        return {"error": f"confidence measurement failed: {e}", "threshold": min_confidence}


async def _build_streak_project(project_dir: Path) -> Optional[str]:
    """bun install + bun run build (css-build + streak-forge pre-build).
    Returns None on success, else the error tail."""
    bun = shutil.which("bun")
    if not bun:
        return "bun not found on the server (https://bun.sh)"
    try:
        for cmd in ([bun, "install"], [bun, "run", "build"]):
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=str(project_dir),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            )
            try:
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
            except asyncio.TimeoutError:
                proc.kill()
                return f"`{' '.join(cmd[1:])}` timed out"
            if proc.returncode != 0:
                return out.decode(errors="ignore")[-1500:]
        return None
    finally:
        shutil.rmtree(project_dir / "node_modules", ignore_errors=True)

def _static_index_html(title, head_tags, html_tag, body_tag, body_html, script_entries, preload: str = "") -> str:
    head_extra = "\n".join(str(t) for t in head_tags)
    html_attrs = _tag_to_html_attr_str(html_tag) if html_tag is not None else 'lang="en"'
    body_attrs = _tag_to_html_attr_str(body_tag)
    scripts = []
    for e in script_entries:
        mod = ' type="module"' if e["kind"] == "module" else ""
        scripts.append(f'<script{mod} src="{e["path"]}"></script>')
    scripts_html = "\n".join(scripts)
    pre = f'<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ""
    return f"""<!DOCTYPE html>
<html {html_attrs}>
<head>
<meta charset="UTF-8">
<title>{_esc(title)}</title>
{head_extra}
{pre}
<link rel="stylesheet" href="/styles/original.css">
</head>
<body {body_attrs}>
{body_html}
{scripts_html}
</body>
</html>"""


def _strip_tracker_markup(body: Tag) -> None:
    """Remove scripts, noscript, tracker iframes, comments and leaked GTM text."""
    for tag in body.find_all(["script", "noscript"]):
        tag.decompose()
    for tag in body.find_all("iframe"):
        if any(x in (tag.get("src") or "") for x in TRACKER_IFRAME_HINTS):
            tag.decompose()
    for c in body.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for s in body.find_all(string=re.compile(r"Google Tag Manager", re.I)):
        s.extract()


async def _run_conversion(req: ConvertRequest) -> dict:
    """Clone the rendered page into a Streak.js project

      streak.sitemap.json              one page ("/") listing PageHead + one widget per section
      src/handlers/HomeDataHandler.ts  (metadata, { common }) -> title/meta + ordered script list
      src/handlers/CommonHandler.ts    once-per-build shared site data
      src/layouts/MainLayout.tsx       real <html>/<body> attrs, wrapper tags, WidgetPlaceholders
      src/widgets/*.tsx                exact markup as JSX (fragments, no hooks)
      src/widgets/LegacyScripts.tsx    Script widget that replays the site's original JS (keep_js only)
      src/common/styles/input.css      site CSS converted to Tailwind @apply (rule-based)
      public/{images,assets,styles}    localized images, fonts, scripts and CSS
    """
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        html, _status_code = await render_page(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to render {url}: {e}")

    soup = BeautifulSoup(html, "html.parser")
    _resolve_lazy_attrs(soup)
    css = await inline_all_css(soup, url)
    _absolutize_dom_urls(soup, url)

    title = soup.title.get_text(strip=True) if soup.title else url
    head_tags = _collect_head_tags(soup)
    meta_tags, link_tags = _head_data(head_tags, url)
    html_tag = soup.find("html")

    body = soup.find("body")
    if body is None:
        raise HTTPException(status_code=502, detail="Rendered page had no <body>.")

    captured_scripts = _capture_scripts(body, url)
    captured_scripts = _filter_scripts(captured_scripts, body)
    detected_libraries = _detect_libraries(
        [s.src for s in captured_scripts if s.kind == "external"], html,
    )
    if not req.keep_js:
        captured_scripts = []

    _strip_tracker_markup(body)
    for tag in [t for t in body.find_all("style") if not t.find_parent("svg")]:
        tag.decompose()
    for tag in body.find_all("link"):
        if "stylesheet" in (tag.get("rel") or []):
            tag.decompose()

    preview_html = _build_preview_html(
        title, head_tags, css, "".join(str(c) for c in body.contents), html_tag, body,
    )

    site_slug = re.sub(r"[^a-z0-9-]", "-", (urlparse(url).netloc or "site").lower()).strip("-") or "cloned-site"
    site_id = f"{site_slug}-{uuid.uuid4().hex[:8]}"
    project_dir = GENERATED_ROOT / site_id
    pkg = _bootstrap_project(project_dir)

    css = await _download_and_localize_assets(soup, css, project_dir)
    css += "\n" + PERF_CSS
    script_entries = await _download_and_localize_scripts(captured_scripts, project_dir)

    _optimize_img_tags(soup, project_dir)

    hero_src = _find_hero_src(soup)
    if hero_src:
        link_tags.append({"rel": "preload", "as": "image", "href": hero_src, "fetchPriority": "high"})

    nodes = _plan_nodes(body, {})
    if not nodes:
        nodes = [["widget", "Content", "".join(str(c) for c in body.contents)]]
    sections = list(_flatten_widgets(nodes))
    section_names = [n for n, _ in sections]

    components: dict[str, str] = {name: _widget_tsx(name, chunk) for name, chunk in sections}

    use_tw = bool(req.tailwind)
    fell_back: list[str] = []
    if use_tw:
        input_css, failed_chunks = await _convert_css_to_input_css(css)
        fell_back = [f"css-chunk-{i}" for i in failed_chunks]
        site_css = "/* Styles live in src/common/styles/input.css and compile to tailwind.css */\n"
    else:
        input_css = EXACT_INPUT_CSS
        site_css = _optimize_css(css)

    original_css = _optimize_css(css)  # served by public/index.html (render-blocking, so keep it small)

    components["PageHead"] = PAGE_HEAD_TSX
    if script_entries:
        components["LegacyScripts"] = LEGACY_SCRIPTS_TSX

    layout_code = _layout_tsx(html_tag, body, nodes, has_scripts=bool(script_entries))

    handler_data = {
        "status": 200,
        "PageHead": {"title": title, "meta": meta_tags, "links": link_tags},
    }
    if script_entries:
        handler_data["LegacyScripts"] = {"scripts": script_entries}
    handler_code = (
        "const getHomeData = async (\n"
        "  metadata?: Record<string, unknown>,\n"
        "  { common }: { common?: any } = {}\n"
        ") => {\n"
        "  void metadata;\n"
        "  void common;\n"
        "  return "
        + json.dumps(handler_data, indent=2, ensure_ascii=False).replace("\n", "\n  ")
        + ";\n};\n\nexport default getHomeData;\n"
    )

    widget_entries = [{"id": "PageHead", "type": "PageHead"}]
    widget_entries += [{"id": n, "type": n} for n in section_names]
    if script_entries:
        widget_entries.append({"id": "LegacyScripts", "type": "LegacyScripts"})
    sitemap = [{
        "url": "/",
        "renderConfig": {
            "renderId": "homeRenderId",
            "metadata": {"pageName": "home", "seoTitle": title},
            "dataHandler": "HomeDataHandler",
            "rootLayout": "MainLayout",
            "widgets": widget_entries,
            "version": "1.0.0",
        },
    }]

    (project_dir / "streak.sitemap.json").write_text(json.dumps(sitemap, indent=2, ensure_ascii=False), encoding="utf-8")
    (project_dir / "src" / "handlers" / "HomeDataHandler.ts").write_text(handler_code, encoding="utf-8")
    (project_dir / "src" / "handlers" / "CommonHandler.ts").write_text(
        _common_handler_ts(url, title), encoding="utf-8"
    )
    (project_dir / "src" / "layouts" / "MainLayout.tsx").write_text(layout_code, encoding="utf-8")
    for name, code in components.items():
        (project_dir / "src" / "widgets" / f"{name}.tsx").write_text(code, encoding="utf-8")
    (project_dir / "src" / "tests" / "HomeDataHandler.test.ts").write_text(HANDLER_TEST_TS, encoding="utf-8")
    (project_dir / "src" / "common" / "styles" / "input.css").write_text(input_css, encoding="utf-8")
    (project_dir / "public" / "styles" / "site.css").write_text(site_css, encoding="utf-8")
    (project_dir / "public" / "styles" / "tailwind.css").write_text("/* generated by `bun run css-build` */\n", encoding="utf-8")
    (project_dir / "tailwind.config.js").write_text(TAILWIND_CONFIG_JS, encoding="utf-8")
    (project_dir / "public" / "styles" / "original.css").write_text(original_css, encoding="utf-8")
    (project_dir / "public" / "index.html").write_text(
        _static_index_html(title, head_tags, html_tag, body,
                           "".join(str(c) for c in body.contents), script_entries, preload=hero_src),
        encoding="utf-8",
    )
    (project_dir / "netlify.toml").write_text(NETLIFY_TOML, encoding="utf-8")

    pkg["name"] = site_slug
    (project_dir / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")

    build = None
    if req.build_check:
        err = await _build_streak_project(project_dir)
        build = {"ok": err is None, "error": err}

    zip_path = GENERATED_ROOT / f"{site_id}.zip"
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(project_dir))
                file_count += 1

    confidence = None
    if req.compare_confidence:
        min_conf = req.confidence_threshold if req.confidence_threshold is not None else DEFAULT_MIN_CONFIDENCE
        confidence = await _measure_clone_confidence(url, preview_html, min_conf)

    return {
        "format": "streak",
        "siteId": site_id,
        "downloadUrl": f"/api/download/{site_id}",
        "appCode": layout_code,
        "components": components,
        "handlerCode": handler_code,
        "sitemap": sitemap,
        "indexCssCode": site_css,
        "inputCssCode": input_css,
        "previewHtml": preview_html,
        "fileCount": file_count,
        "capturedScriptCount": len(script_entries),
        "detectedLibraries": detected_libraries,
        "tailwind": use_tw,
        "tailwindFallbackSections": fell_back,
        "confidence": confidence,
        "build": build,
    }

async def _post_callback(callback_url: str, payload: dict) -> None:
    job_id = payload.get("jobId")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for attempt in range(1, CALLBACK_RETRIES + 1):
            try:
                r = await client.post(callback_url, json=payload)
                if r.status_code < 300:
                    print(f"[callback] job {job_id}: DELIVERED to {callback_url} "
                          f"(HTTP {r.status_code}, attempt {attempt})")
                    return
                print(f"[callback] job {job_id}: attempt {attempt} got HTTP {r.status_code}")
            except Exception as e:
                print(f"[callback] job {job_id}: attempt {attempt} failed: {e}")
            if attempt < CALLBACK_RETRIES:
                await asyncio.sleep(2 ** attempt)
    print(f"[callback] job {job_id}: GAVE UP on {callback_url}")


async def _run_and_callback(req: ConvertRequest, job_id: str) -> None:
    print(f"[job {job_id}] started: {req.url}")
    try:
        result = await _run_conversion(req)
        payload = {"jobId": job_id, "status": "completed", **result}
        print(f"[job {job_id}] conversion COMPLETED (siteId={result['siteId']})")
    except HTTPException as e:
        payload = {"jobId": job_id, "status": "failed", "error": e.detail}
        print(f"[job {job_id}] conversion FAILED: {e.detail}")
    except Exception as e:
        payload = {"jobId": job_id, "status": "failed", "error": str(e)}
        print(f"[job {job_id}] conversion FAILED: {e}")
    await _post_callback(req.callbackUrl, payload)

@app.post("/api/convert")
async def convert_to_streak(req: ConvertRequest, background_tasks: BackgroundTasks):
    if not req.callbackUrl:
        return await _run_conversion(req)

    job_id = uuid.uuid4().hex
    background_tasks.add_task(_run_and_callback, req, job_id)
    return JSONResponse(
        status_code=200,
        content={"status": "accepted", "jobId": job_id},
    )


@app.get("/api/download/{site_id}")
async def download_react_project(site_id: str):
    if not re.fullmatch(r"[a-z0-9-]+", site_id):
        raise HTTPException(status_code=400, detail="Invalid site id.")
    zip_path = GENERATED_ROOT / f"{site_id}.zip"
    if not zip_path.is_file():
        raise HTTPException(status_code=404, detail="Generated project not found.")
    return FileResponse(zip_path, filename=f"{site_id}.zip", media_type="application/zip")

app.include_router(ai_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(transfer_router)