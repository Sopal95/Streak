import re
import json
import uuid
import os
import zipfile
from collections import Counter
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup, Tag, Comment

router = APIRouter()

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
SOCIAL = ("facebook.", "instagram.", "twitter.", "x.com", "linkedin.", "youtube.", "wa.me", "t.me", "tiktok.")
CHROME = {"header", "footer", "nav", "aside"}
SKIP = {"script", "style", "noscript", "link", "meta"}
KEEP_ATTRS = {"href", "src", "srcset", "alt", "title", "type", "name", "placeholder", "required", "action",
              "method", "value", "for", "id", "rows", "cols", "colspan", "rowspan", "allowfullscreen",
              "loading", "width", "height", "target", "rel", "checked", "selected", "min", "max", "pattern"}


class TransferRequest(BaseModel):
    source_url: str
    template_url: Optional[str] = None
    template_html: Optional[str] = None       # alternative to template_url
    template_base_url: Optional[str] = None   # used to resolve assets when template_html is given
    instructions: str = ""                    # e.g. "keep the template's hero banner, use the source's phone in it"
    use_ai: bool = True


def _norm(u: str) -> str:
    u = u.strip()
    return u if u.startswith(("http://", "https://")) else "https://" + u


# ---------------- source extraction ----------------
def _clean_fragment(root: Tag) -> str:
    for t in root.find_all(["script", "style", "noscript", "svg", "canvas", "template", "link", "meta"]):
        t.decompose()
    for t in root.find_all("input", attrs={"type": "hidden"}):
        t.decompose()
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in root.find_all("iframe"):
        if any(x in (t.get("src") or "") for x in ("googletagmanager", "doubleclick", "facebook")):
            t.decompose()
    for t in root.find_all(True):
        t.attrs = {k: (" ".join(v) if isinstance(v, list) else v) for k, v in t.attrs.items() if k in KEEP_ATTRS}
    return re.sub(r"\n\s*\n+", "\n", root.decode_contents()).strip()


def _extract_source(html: str, url: str) -> dict:
    from main import _resolve_lazy_attrs, _absolutize_dom_urls
    soup = BeautifulSoup(html, "html.parser")
    _resolve_lazy_attrs(soup)
    _absolutize_dom_urls(soup, url)

    title = soup.title.get_text(strip=True) if soup.title else url
    md = soup.find("meta", attrs={"name": "description"})
    description = (md.get("content") if md else "") or ""

    body = soup.find("body") or soup
    main = body.find("main") or body.find(attrs={"role": "main"})
    if main is None:
        main = BeautifulSoup(str(body), "html.parser")
        for t in main.find_all(list(CHROME)):
            t.decompose()
        main = main.find("body") or main

    text = main.get_text(" ", strip=True)
    hrefs = [a.get("href", "") for a in body.find_all("a", href=True)]
    contacts = {
        "emails": sorted({h[7:].split("?")[0] for h in hrefs if h.startswith("mailto:")} | set(EMAIL_RE.findall(text))),
        "phones": sorted({h[4:] for h in hrefs if h.startswith("tel:")} | {p.strip() for p in PHONE_RE.findall(text)}),
        "addresses": [a.get_text(" ", strip=True) for a in body.find_all("address")],
        "socials": sorted({h for h in hrefs if any(s in h for s in SOCIAL)}),
        "maps": [i.get("src") for i in body.find_all("iframe") if "map" in (i.get("src") or "")],
    }
    main_html = _clean_fragment(main)
    return {"title": title, "description": description, "main_html": main_html, "contacts": contacts,
            "text": text}


# ---------------- template region ----------------
def _region_kids(body: Tag) -> list[Tag]:
    from main import _is_overlay
    container = body
    for _ in range(8):
        kids = [k for k in container.find_all(True, recursive=False) if k.name not in SKIP]
        if not kids:
            break
        big = max(kids, key=lambda k: len(str(k)))
        if big.name == "main" or big.get("role") == "main":
            container = big
            kids = [k for k in container.find_all(True, recursive=False) if k.name not in SKIP]
            break
        if big.name in ("div", "section", "article") and len(str(big)) >= 0.6 * len(str(container)):
            container = big
            continue
        break
    kids = [k for k in container.find_all(True, recursive=False) if k.name not in SKIP]
    return [k for k in kids if k.name not in CHROME and not _is_overlay(k)]


def _swap_region(kids: list[Tag], body: Tag, new_html: str) -> None:
    frag = BeautifulSoup(new_html, "html.parser")
    if not kids:
        for n in list(frag.contents):
            body.append(n.extract())
        return
    anchor = kids[0]
    for n in list(frag.contents):
        anchor.insert_before(n.extract())
    for k in kids:
        k.decompose()


def _compact(s: str, limit: int) -> str:
    s = re.sub(r"<svg.*?</svg>", "<svg/>", s, flags=re.S)
    s = re.sub(r'data:[^"\')]{50,}', "data:", s)
    return s[:limit]


# ---------------- LLM ----------------
SYSTEM = """You rebuild a web page's main content area in a different site's design.
You get (1) TEMPLATE_REGION: the template page's main-content HTML (use it only as a design reference),
(2) SOURCE: content extracted from another page.
Output ONLY the replacement HTML for the main-content area. No markdown fences, no explanation.
Rules:
- Reuse the template's exact class names, wrappers, section patterns, heading/button/form/card styles and layout.
- Use ALL of the source's text, headings, images (keep absolute src URLs), links, form fields and contact details verbatim. Never invent content.
- Remove all template placeholder text/images/links; none of the template's own copy may remain.
- If the template has a hero/banner pattern, use it for the source's page title. Map source sections to the closest template section patterns.
- A contact form must keep the source's fields (names, types, placeholders, required) styled with the template's input/button classes.
- No <script>, <style>, <header>, <nav> or <footer>."""

def _strip_fences(s: str) -> str:
    return re.sub(r"^```[a-zA-Z]*\n|\n```$", "", s.strip()).strip()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")
async def _llm_region(template_region: str, source: dict, instructions: str) -> Optional[str]:
    # from main import OPENROUTER_API_KEY, OPENROUTER_MODEL, _strip_fences
    if not OPENROUTER_API_KEY:
        return None
    user = (
        "TEMPLATE_REGION:\n" + _compact(template_region, 14000)
        + "\n\nSOURCE_TITLE: " + source["title"]
        + "\nSOURCE_CONTACTS: " + json.dumps(source["contacts"], ensure_ascii=False)
        + "\nSOURCE_MAIN_HTML:\n" + source["main_html"][:16000]
        + (("\n\nEXTRA INSTRUCTIONS: " + instructions) if instructions else "")
    )
    try:
        async with httpx.AsyncClient(timeout=180) as c:
            r = await c.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={"model": OPENROUTER_MODEL, "temperature": 0, "max_tokens": 16000,
                      "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]},
            )
            r.raise_for_status()
            return _strip_fences(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"[transfer] LLM error: {e}")
        return None


def _keeps_source(out: str, source_text: str) -> bool:
    words = {w for w in re.findall(r"[A-Za-z0-9]{4,}", source_text.lower())}
    if not words or "<" not in out or len(out) < 200:
        return False
    out_words = Counter(re.findall(r"[A-Za-z0-9]{4,}", BeautifulSoup(out, "html.parser").get_text(" ").lower()))
    return sum(1 for w in words if w in out_words) / len(words) >= 0.6


# ---------------- endpoint ----------------
@router.post("/api/transfer")
async def transfer_content(req: TransferRequest):
    from main import (render_page, inline_all_css, _absolutize_dom_urls, _resolve_lazy_attrs,
                      _strip_tracker_markup, _collect_head_tags, _head_data, _download_and_localize_assets,
                      _optimize_css, _optimize_img_tags, _build_preview_html, _tag_to_html_attr_str,
                      GENERATED_ROOT)
    from html import escape

    if not req.template_url and not req.template_html:
        raise HTTPException(status_code=400, detail="Provide template_url or template_html.")

    # 1) source content
    src_url = _norm(req.source_url)
    try:
        src_html, _ = await render_page(src_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to render source {src_url}: {e}")
    source = _extract_source(src_html, src_url)

    # 2) template shell
    if req.template_url:
        tpl_url = _norm(req.template_url)
        try:
            tpl_html, _ = await render_page(tpl_url)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to render template {tpl_url}: {e}")
    else:
        tpl_url = _norm(req.template_base_url) if req.template_base_url else "https://template.local/"
        tpl_html = req.template_html

    soup = BeautifulSoup(tpl_html, "html.parser")
    _resolve_lazy_attrs(soup)
    css = await inline_all_css(soup, tpl_url)
    _absolutize_dom_urls(soup, tpl_url)
    html_tag = soup.find("html")
    body = soup.find("body")
    if body is None:
        raise HTTPException(status_code=502, detail="Template has no <body>.")
    head_tags = [t for t in _collect_head_tags(soup)
                 if not (t.name == "meta" and (t.get("name") or "").lower() == "description"
                         or (t.get("property") or "").lower().startswith("og:"))]
    _strip_tracker_markup(body)
    for t in [t for t in body.find_all("style") if not t.find_parent("svg")]:
        t.decompose()
    for t in body.find_all("link"):
        if "stylesheet" in (t.get("rel") or []):
            t.decompose()

    # 3) rebuild region
    kids = _region_kids(body)
    tpl_region = "".join(str(k) for k in kids)
    new_html, used_ai = None, False
    if req.use_ai:
        out = await _llm_region(tpl_region, source, req.instructions)
        if out and _keeps_source(out, source["text"]):
            new_html, used_ai = out, True
    if new_html is None:
        new_html = f"<section>\n<h1>{escape(source['title'])}</h1>\n{source['main_html']}\n</section>"
    _swap_region(kids, body, new_html)

    # head: source title/description, template everything else
    title = source["title"]
    if source["description"]:
        m = soup.new_tag("meta")
        m.attrs["name"], m.attrs["content"] = "description", source["description"]
        head_tags.append(m)

    body_inner = "".join(str(c) for c in body.contents)
    preview_html = _build_preview_html(title, head_tags, css, body_inner, html_tag, body)

    # 4) write project
    slug = re.sub(r"[^a-z0-9-]", "-", (urlparse(tpl_url).netloc or "site").lower()).strip("-") or "site"
    site_id = f"{slug}-transfer-{uuid.uuid4().hex[:8]}"
    project_dir = GENERATED_ROOT / site_id
    (project_dir / "styles").mkdir(parents=True, exist_ok=True)

    css = await _download_and_localize_assets(soup, css, project_dir)
    _optimize_img_tags(soup, project_dir)

    # root-absolute local paths -> relative, so the zip opens straight from disk
    final_body = "".join(str(c) for c in body.contents)
    final_body = re.sub(r"""(["'(,\s])/(images|assets/fonts)/""", r"\1\2/", final_body)
    css = re.sub(r"url\((['\"]?)/(images|assets/fonts)/", r"url(\1../\2/", css)
    (project_dir / "styles" / "site.css").write_text(_optimize_css(css), encoding="utf-8")

    html_attrs = _tag_to_html_attr_str(html_tag) if html_tag is not None else 'lang="en"'
    index = f"""<!DOCTYPE html>
<html {html_attrs}>
<head>
<meta charset="UTF-8">
<title>{escape(title)}</title>
{chr(10).join(str(t) for t in head_tags)}
<link rel="stylesheet" href="styles/site.css">
</head>
<body {_tag_to_html_attr_str(body)}>
{final_body}
</body>
</html>"""
    (project_dir / "index.html").write_text(index, encoding="utf-8")

    zip_path = GENERATED_ROOT / f"{site_id}.zip"
    n = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in project_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(project_dir))
                n += 1

    return {
        "siteId": site_id,
        "downloadUrl": f"/api/download/{site_id}",
        "previewHtml": preview_html,
        "usedAI": used_ai,
        "fileCount": n,
        "source": {"title": source["title"], "contacts": source["contacts"]},
        "regionWidgetCount": len(kids),
    }