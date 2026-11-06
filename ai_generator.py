import os
import re
import json
import uuid
import base64
import zipfile
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL_TEXT = os.environ.get("OPENROUTER_MODEL_TEXT", "meta-llama/llama-3.3-70b-instruct")
MODEL_VISION = os.environ.get("OPENROUTER_MODEL_VISION", "qwen/qwen2.5-vl-72b-instruct")
SITE_URL = os.environ.get("OPENROUTER_SITE_URL", "http://localhost")
APP_NAME = os.environ.get("OPENROUTER_APP_NAME", "AI Website Generator")

AI_GENERATED_ROOT = Path("generated_ai_sites")
AI_GENERATED_ROOT.mkdir(exist_ok=True)


def _load_tailwind_rules() -> str:
    for p in (Path("tailwind.md"), Path(__file__).resolve().parent / "tailwind.md"):
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


TAILWIND_RULES = _load_tailwind_rules()

router = APIRouter()


class GenerateTextRequest(BaseModel):
    description: str
    site_name: Optional[str] = None


RESPONSE_SCHEMA_INSTRUCTIONS = """
Respond using EXACTLY this plain-text section format. Do NOT use JSON.
Do NOT wrap sections in markdown code fences (no ``` anywhere). Do NOT
add any commentary before, between, or after the sections -- your
entire response must be only the sections below, back to back.

Each section starts with its own marker on its own line, written
exactly as shown (these exact characters, nothing added):

===TITLE===
Short Site Title

===THEME===
--color-primary: #4f46e5;
--color-brand: #0ea5e9;

===COMPONENT: ComponentName===
<the full, literal JSX source code for this component>

===COMPONENT: AnotherComponent===
<full JSX source for this component>

===APP===
<full JSX source for src/App.jsx>

Rules for the section format:
- THEME holds ONLY CSS custom-property lines (`--color-*`, `--font-*`,
  `--spacing-*`, `--breakpoint-*`) that become Tailwind v4 @theme tokens,
  so you can write `bg-primary`, `text-brand`, etc. Keep it to a few lines.
  There is NO CSS section: do NOT write any CSS, any <style> tag, or any
  custom class. All styling is Tailwind utility classes in the JSX.
- Include one "===COMPONENT: Name===" section per component. Name must be
  a single PascalCase word and must match the component name in the code.
- Everything after a marker line, up to the next marker line, is taken
  completely literally as that file's contents. Write real newlines and
  quotes -- do NOT escape anything.
- TITLE, THEME, at least one COMPONENT, and APP must each be present
  (COMPONENT as many times as needed).

Hard rules for the generated code:
- Every component file is plain React: `import { useState } from "react";`
  (only if hooks are needed), icon imports from `react-icons` (see below),
  then `const Name = () => { ... };` or `function Name() { ... }`, then
  `export default Name;` at the end. In App.jsx only, you may also import
  your own components from "./components/X.jsx".
- ONLY these imports are allowed: "react", "react-icons/<pack>" (e.g.
  "react-icons/fi"), and "./components/X.jsx" in App.jsx. NO other npm
  package (no lucide-react, heroicons, fontawesome, chart libraries, UI
  kits).
- Icons: ONLY react-icons, e.g. `import { FiArrowRight } from "react-icons/fi";`.
  NEVER inline <svg> and never other icon libraries.
- Charts/graphs: build them with <div> elements styled with Tailwind
  utilities (bars, progress rings via conic gradients are NOT allowed;
  use bars/columns/stacked segments). A dynamic bar height/width taken from
  data may use inline `style={{ height: `${v}%` }}` -- that is the ONLY
  allowed inline style.
- All data is realistic mock data defined as JS arrays/objects INSIDE the
  component file that uses it (static site, no backend).
- Split the UI into multiple sensible components (Sidebar, Header, one per
  major section/page). App.jsx is the composition root; use useState for
  simple tab/page switching if the UI implies multiple views.
- CRITICAL -- every component section MUST be a complete, self-contained
  component file: start with `function Name() {` or `const Name = () => {`
  and end with `export default Name;`. NEVER return bare JSX with no
  surrounding function and no export. INVALID:
      <section id="skills"><h2>Skills</h2></section>
  REQUIRED:
      function Skills() {
        const skills = ["React", "Node.js", "SQL"];
        return (
          <section id="skills" className="py-10">
            <h2 className="text-2xl font-bold">Skills</h2>
            <ul>{skills.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </section>
        );
      }
      export default Skills;
- Each component must work with ZERO props (App renders `<ComponentName />`).
  Any data it needs is a local const INSIDE that file.
- Style EVERYTHING with Tailwind utility classes (responsive via sm:/md:/lg:,
  states via hover:/focus:). Polished, coherent palette, spacing, typography,
  hover states, responsive layout. Leave nothing unstyled.
- NEVER use arbitrary values: no `[...]` in any class (no text-[15px],
  w-[600px], bg-[#fff], shadow-[...], grid-cols-[...] etc.). Use the
  nearest Tailwind scale value or a THEME token.
- Do not truncate. Include full, working code for every component.
"""


def _tailwind_rules_block() -> str:
    if not TAILWIND_RULES:
        return ""
    return (
        "\n\nThe following TailwindCSS rules are MANDATORY. Violating them is "
        "incorrect code generation.\n\n"
        "<tailwind_rules>\n" + TAILWIND_RULES + "\n</tailwind_rules>\n"
        "\nOverride notes (these take precedence over anything above): this "
        "project uses Tailwind CSS v4 (no tailwind.config file -- custom tokens "
        "go in the THEME section) and only `react`, `react-dom` and "
        "`react-icons` are installed.\n"
    )


def _text_system_prompt() -> str:
    return (
        "You are an expert React + Tailwind CSS developer who builds clean, "
        "modern, production-quality static websites from a natural-language "
        "description. You always output a complete, runnable, multi-component "
        "React project styled ONLY with Tailwind utility classes.\n"
        + RESPONSE_SCHEMA_INSTRUCTIONS
        + _tailwind_rules_block()
    )


def _vision_system_prompt() -> str:
    return (
        "You are an expert React + Tailwind CSS developer and UI cloner. "
        "You are given a screenshot of a website or app UI. Reproduce it as "
        "closely as you can as a React project styled ONLY with Tailwind "
        "utility classes: same overall layout, sections/columns/cards, "
        "approximate colors, typography, spacing and proportions, same visible "
        "text/labels where readable. Approximate to the nearest Tailwind scale "
        "value instead of chasing pixel-exactness. Where content is cut off or "
        "ambiguous, make a reasonable, visually consistent guess.\n"
        + RESPONSE_SCHEMA_INSTRUCTIONS
        + _tailwind_rules_block()
    )


async def _call_openrouter(messages: list, model: str) -> str:
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not set on the server environment.",
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 12000,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"OpenRouter request failed: {e}")

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter returned {resp.status_code}: {resp.text[:500]}",
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail=f"Unexpected OpenRouter response: {data}")


_SECTION_MARKER_RE = re.compile(
    r"^[ \t]*===\s*(TITLE|APP|CSS|THEME|COMPONENT\s*:\s*([A-Za-z_][A-Za-z0-9_]*))\s*===[ \t]*$",
    re.MULTILINE,
)


def _parse_llm_bundle(raw: str) -> dict:
    """Parse the delimiter-based section format (no JSON escaping needed).
    Falls back to legacy JSON if a model ignores the format."""
    text = raw.strip()
    text = re.sub(r"^```(?:jsx?|javascript|text)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)

    matches = list(_SECTION_MARKER_RE.finditer(text))
    if matches:
        bundle = {"title": "", "components": {}, "appCode": "", "theme": ""}
        for i, m in enumerate(matches):
            kind = m.group(1)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip("\n").strip()
            content = _strip_code_fences(content)

            if kind == "TITLE":
                bundle["title"] = content.splitlines()[0].strip() if content else bundle["title"]
            elif kind == "APP":
                bundle["appCode"] = content
            elif kind == "THEME":
                bundle["theme"] = content
            elif kind == "CSS":
                pass
            elif kind.startswith("COMPONENT"):
                bundle["components"][m.group(2)] = content

        if bundle["components"] and bundle["appCode"]:
            return bundle

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise HTTPException(
        status_code=502,
        detail=(
            "LLM did not return a parseable response. "
            f"First 500 chars of what it returned: {text[:500]!r}"
        ),
    )


def _validate_bundle(bundle: dict) -> dict:
    required = ("title", "components", "appCode")
    missing = [k for k in required if k not in bundle]
    if missing:
        raise HTTPException(status_code=502, detail=f"LLM response missing keys: {missing}")
    if not isinstance(bundle["components"], dict) or not bundle["components"]:
        raise HTTPException(status_code=502, detail="LLM response 'components' must be a non-empty object.")
    bundle.setdefault("theme", "")
    return bundle

_IMPORT_RE = re.compile(
    r"^[ \t]*import\s+(?P<clause>[^'\"]*?)\s*from\s*['\"](?P<src>[^'\"]+)['\"]\s*;?[ \t]*$",
    re.MULTILINE,
)
_EXPORT_DEFAULT_RE = re.compile(r"^\s*export\s+default\s+\w+\s*;?\s*$", re.MULTILINE)
_EXPORT_DEFAULT_FN_RE = re.compile(r"\bexport\s+default\s+function\b")

_ARBITRARY_RE = re.compile(r"[^\s\"'`{}]*?-\[[^\]\s]*\]")


def _validate_component_code(name: str, code: str) -> bool:
    """True if `code` is a complete, self-contained component with a default export."""
    if re.search(rf"export\s+default\s+function\s+{re.escape(name)}\s*\(", code):
        return True
    has_decl = bool(re.search(
        rf"\b(function\s+{re.escape(name)}\s*\(|const\s+{re.escape(name)}\s*=)", code
    ))
    has_export = bool(re.search(rf"export\s+default\s+{re.escape(name)}\s*;?", code))
    return has_decl and has_export


def _component_issues(name: str, code: str, is_app: bool = False) -> list[str]:
    issues: list[str] = []
    if not _validate_component_code(name, code):
        issues.append(
            f"STRUCTURE: file is not a complete component `{name}` with a default export "
            f"(missing function wrapper and/or `export default {name};`, or it references "
            f"undefined data)."
        )
    if _ARBITRARY_RE.search(code):
        found = sorted(set(_ARBITRARY_RE.findall(code)))[:10]
        issues.append(f"TAILWIND: arbitrary [] values are forbidden: {', '.join(found)}")
    if re.search(r"<svg\b", code):
        issues.append("TAILWIND: inline <svg> is forbidden; use react-icons instead.")
    if re.search(r"<style\b", code):
        issues.append("TAILWIND: <style> tags/custom CSS are forbidden; use utility classes.")
    for m in _IMPORT_RE.finditer(code):
        src = m.group("src")
        ok = src == "react" or src.startswith("react-icons/") or (is_app and src.startswith("./components/"))
        if not ok:
            issues.append(f"IMPORT: disallowed import source '{src}' (only react, react-icons/*, and ./components/* in App).")
    return issues


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:jsx?|javascript)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _repair_system_prompt(name: str, issues: list[str]) -> str:
    issue_list = "\n".join(f"- {i}" for i in issues)
    return (
        f"You are an expert React + Tailwind CSS developer. You will be given the "
        f"source of a single React component file named `{name}` that has problems.\n\n"
        f"Problems found:\n{issue_list}\n\n"
        f"Fix ALL of them so the file is a complete, self-contained component:\n"
        f"- Wrap bare JSX in `function {name}() {{ ... return (...); }}` and end the "
        f"file with `export default {name};`.\n"
        f"- It must work with ZERO props. If it references undefined data, define "
        f"realistic mock data as a const inside the file. Do NOT add parameters.\n"
        f"- Style only with Tailwind default utilities. Replace EVERY arbitrary "
        f"value `[...]` with the nearest Tailwind scale value (e.g. text-[15px] -> "
        f"text-sm, rounded-[22px] -> rounded-xl, gap-[27px] -> gap-6, w-[600px] -> "
        f"w-150) or a default palette color (e.g. text-slate-900, bg-orange-500).\n"
        f"- Replace inline <svg> icons with `react-icons` imports "
        f"(e.g. `import {{ FiArrowRight }} from \"react-icons/fi\";`). Remove <style> "
        f"tags. Only allow imports from react, react-icons/*, and (App only) ./components/*.\n"
        f"- Keep all text, structure and class names that are already valid.\n\n"
        f"Respond with ONLY the corrected file's full source code as plain text. "
        f"No markdown code fences, no explanation, no commentary."
    )

_TEXT_SIZES = [(12, "xs"), (14, "sm"), (16, "base"), (18, "lg"), (20, "xl"),
               (24, "2xl"), (30, "3xl"), (36, "4xl"), (48, "5xl"), (60, "6xl")]
_RADII = [(2, "sm"), (4, ""), (6, "md"), (8, "lg"), (12, "xl"), (16, "2xl"), (24, "3xl")]
_SPACING_UTILS = {
    "w", "h", "min-w", "min-h", "max-w", "max-h", "size",
    "p", "px", "py", "pt", "pr", "pb", "pl",
    "m", "mx", "my", "mt", "mr", "mb", "ml",
    "gap", "gap-x", "gap-y", "space-x", "space-y",
    "top", "left", "right", "bottom", "inset", "inset-x", "inset-y",
}
_ARB_PARTS_RE = re.compile(r"^((?:[\w-]+:)*)(.+?)-\[([^\]]*)\]$")
_PX_RE = re.compile(r"^(-?\d+(?:\.\d+)?)px$")


def _nearest(table, px):
    return min(table, key=lambda t: abs(t[0] - px))[1]


def _approx_arbitrary_token(tok: str) -> str:
    """Map an arbitrary-value class to the nearest scale utility, or '' to drop it."""
    m = _ARB_PARTS_RE.match(tok)
    if not m:
        return ""
    variants, util, val = m.groups()
    pm = _PX_RE.match(val)
    if not pm:
        return ""
    px = float(pm.group(1))
    if util == "text":
        return f"{variants}text-{_nearest(_TEXT_SIZES, px)}"
    if util == "rounded":
        suffix = "full" if px >= 999 else _nearest(_RADII, px)
        return f"{variants}rounded" + (f"-{suffix}" if suffix else "")
    if util in _SPACING_UTILS:
        units = round(px / 4 * 2) / 2
        units = int(units) if units == int(units) else units
        return f"{variants}{util}-{units}"
    return ""


def _sanitize_arbitrary(code: str) -> str:
    out = _ARBITRARY_RE.sub(lambda m: _approx_arbitrary_token(m.group(0)), code)
    return re.sub(r"[ \t]{2,}(?=[\"'`])", " ", out)


def _deterministic_wrap(name: str, code: str) -> str:
    """Mechanically wrap a bare JSX fragment in a function + export, stubbing
    undefined `.map(` lists as empty arrays so the app doesn't crash."""
    imports = "\n".join(m.group(0).strip() for m in _IMPORT_RE.finditer(code))
    body = _IMPORT_RE.sub("", code).strip()
    guessed_lists = sorted(set(re.findall(r"\b([a-z][a-zA-Z0-9_]*)\.(?:map|filter|forEach)\(", body)))
    stub_lines = "".join(f"  const {ident} = [];\n" for ident in guessed_lists)
    return (
        (imports + "\n\n" if imports else "")
        + f"function {name}() {{\n"
        + stub_lines
        + f"  return (\n{body}\n  );\n"
        + "}\n\n"
        + f"export default {name};\n"
    )


async def _repair_component(name: str, code: str, model: str, issues: list[str], is_app: bool = False) -> str:
    candidate = code
    try:
        raw = await _call_openrouter(
            messages=[
                {"role": "system", "content": _repair_system_prompt(name, issues)},
                {"role": "user", "content": f"Component name: {name}\n\nBroken file contents:\n\n{code}"},
            ],
            model=model,
        )
        repaired = _strip_code_fences(raw)
        if not _component_issues(name, repaired, is_app):
            return repaired
        if _validate_component_code(name, repaired):
            candidate = repaired
    except HTTPException:
        pass

    if not _validate_component_code(name, candidate):
        candidate = _deterministic_wrap(name, candidate)
    return _sanitize_arbitrary(candidate)


async def _validate_and_repair_bundle(bundle: dict, model: str) -> dict:
    """Checks every component (and App.jsx) for structure + Tailwind-rule
    violations and repairs only the broken ones (clean generations cost
    nothing extra)."""
    components = bundle["components"]
    for name, code in list(components.items()):
        issues = _component_issues(name, code)
        if issues:
            components[name] = await _repair_component(name, code, model, issues)

    app_issues = _component_issues("App", bundle["appCode"], is_app=True)
    if app_issues:
        bundle["appCode"] = await _repair_component("App", bundle["appCode"], model, app_issues, is_app=True)

    return bundle


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", text.lower()).strip("-")
    return slug or "ai-site"


_THEME_LINE_RE = re.compile(r"--[a-z0-9-]+\s*:\s*[^;{}]+;", re.IGNORECASE)


def _theme_lines(theme: str) -> list[str]:
    return [l.strip() for l in _THEME_LINE_RE.findall(theme or "")]


def _build_index_css(theme: str) -> str:
    lines = _theme_lines(theme)
    css = '@import "tailwindcss";\n'
    if lines:
        css += "\n@theme {\n" + "\n".join(f"  {l}" for l in lines) + "\n}\n"
    return css


def _scaffold_and_zip(site_id: str, title: str, app_code: str, components: dict, css: str) -> Path:
    project_dir = AI_GENERATED_ROOT / site_id
    (project_dir / "src" / "components").mkdir(parents=True, exist_ok=True)
    (project_dir / "public").mkdir(parents=True, exist_ok=True)

    main_jsx = (
        "import React from 'react'\n"
        "import ReactDOM from 'react-dom/client'\n"
        "import App from './App.jsx'\n"
        "import './index.css'\n\n"
        "ReactDOM.createRoot(document.getElementById('root')).render(<App />)\n"
    )
    (project_dir / "src" / "main.jsx").write_text(main_jsx, encoding="utf-8")
    (project_dir / "src" / "App.jsx").write_text(app_code, encoding="utf-8")
    (project_dir / "src" / "index.css").write_text(css, encoding="utf-8")
    for name, code in components.items():
        safe_name = re.sub(r"[^A-Za-z0-9_]", "", name) or "Component"
        (project_dir / "src" / "components" / f"{safe_name}.jsx").write_text(code, encoding="utf-8")

    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""
    (project_dir / "index.html").write_text(index_html, encoding="utf-8")

    (project_dir / "package.json").write_text(json.dumps({
        "name": _slugify(title),
        "version": "1.0.0",
        "private": True,
        "type": "module",
        "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
        "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0", "react-icons": "^5.0.0"},
        "devDependencies": {
            "@vitejs/plugin-react": "^4.2.0",
            "vite": "^5.0.0",
            "tailwindcss": "^4.0.0",
            "@tailwindcss/vite": "^4.0.0",
        },
    }, indent=2), encoding="utf-8")

    vite_config = (
        "import { defineConfig } from 'vite'\n"
        "import react from '@vitejs/plugin-react'\n"
        "import tailwindcss from '@tailwindcss/vite'\n\n"
        "export default defineConfig({\n"
        "  plugins: [react(), tailwindcss()],\n"
        "})\n"
    )
    (project_dir / "vite.config.js").write_text(vite_config, encoding="utf-8")

    zip_path = AI_GENERATED_ROOT / f"{site_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(project_dir))

    return zip_path

_PREVIEW_BASE_REACT_NAMES = ["useState", "useEffect", "useMemo", "useRef", "useCallback"]


def _split_imports(code: str) -> tuple[dict[str, set[str]], str]:
    """Pull react / react-icons imports out of `code`; return
    ({module: {names}}, code_without_any_imports_or_exports)."""
    found: dict[str, set[str]] = {}
    for m in _IMPORT_RE.finditer(code):
        src = m.group("src")
        if src == "react" or src.startswith("react-icons/"):
            named = re.search(r"\{([^}]*)\}", m.group("clause"))
            if named:
                names = {n.strip() for n in named.group(1).split(",") if n.strip()}
                found.setdefault(src, set()).update(names)
    code = _IMPORT_RE.sub("", code)
    code = _EXPORT_DEFAULT_FN_RE.sub("function", code)
    code = _EXPORT_DEFAULT_RE.sub("", code)
    return found, code


def _build_preview_html(title: str, theme: str, components: dict, app_code: str) -> str:
    merged: dict[str, set[str]] = {"react": set(_PREVIEW_BASE_REACT_NAMES)}
    blocks: list[str] = []
    for code in list(components.values()) + [app_code]:
        found, stripped = _split_imports(code)
        for src, names in found.items():
            merged.setdefault(src, set()).update(names)
        blocks.append(stripped.strip())

    import_lines = [
        f'import React, {{ {", ".join(sorted(merged.pop("react")))} }} from "react";',
        'import { createRoot } from "react-dom/client";',
    ]
    for src in sorted(merged):
        if merged[src]:
            import_lines.append(f'import {{ {", ".join(sorted(merged[src]))} }} from "{src}";')

    module_script = (
        "\n".join(import_lines)
        + "\n\n"
        + "\n\n".join(blocks)
        + "\n\ncreateRoot(document.getElementById('root')).render(<App />);\n"
    )

    import_map = json.dumps({
        "imports": {
            "react": "https://esm.sh/react@18.3.1",
            "react-dom/client": "https://esm.sh/react-dom@18.3.1/client",
            "react-icons/": "https://esm.sh/*react-icons@5.3.0/",
        }
    }, indent=2)

    theme_lines = _theme_lines(theme)
    theme_css = ("@theme {\n" + "\n".join(f"  {l}" for l in theme_lines) + "\n}\n") if theme_lines else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
<style type="text/tailwindcss">
{theme_css}</style>
<script type="importmap">
{import_map}
</script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
<div id="root"></div>
<script type="text/babel" data-type="module" data-presets="react">
{module_script}
</script>
</body>
</html>"""

@router.post("/api/ai/generate-from-text")
async def generate_from_text(req: GenerateTextRequest):
    description = req.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="description is required.")

    user_prompt = (
        f"Build the following as a React static site styled only with Tailwind utility classes: {description}\n\n"
        + (f"Suggested site name: {req.site_name}\n" if req.site_name else "")
    )
    raw = await _call_openrouter(
        messages=[
            {"role": "system", "content": _text_system_prompt()},
            {"role": "user", "content": user_prompt},
        ],
        model=MODEL_TEXT,
    )
    bundle = _validate_bundle(_parse_llm_bundle(raw))
    bundle = await _validate_and_repair_bundle(bundle, model=MODEL_TEXT)
    return _finalize_bundle(bundle)


@router.post("/api/ai/generate-from-image")
async def generate_from_image(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    media_type = file.content_type or "image/png"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{media_type};base64,{b64}"

    user_content = [
        {
            "type": "text",
            "text": (
                "Recreate this UI as a React project styled only with Tailwind utility classes."
                + (f" Additional notes from the user: {notes}" if notes else "")
            ),
        },
        {"type": "image_url", "image_url": {"url": data_url}},
    ]

    raw = await _call_openrouter(
        messages=[
            {"role": "system", "content": _vision_system_prompt()},
            {"role": "user", "content": user_content},
        ],
        model=MODEL_VISION,
    )
    bundle = _validate_bundle(_parse_llm_bundle(raw))
    bundle = await _validate_and_repair_bundle(bundle, model=MODEL_VISION)
    return _finalize_bundle(bundle)


def _finalize_bundle(bundle: dict) -> dict:
    title = bundle["title"] or "AI Site"
    components = bundle["components"]
    app_code = bundle["appCode"]
    theme = bundle.get("theme", "")
    css = _build_index_css(theme)

    site_id = f"{_slugify(title)}-{uuid.uuid4().hex[:8]}"
    _scaffold_and_zip(site_id, title, app_code, components, css)
    preview_html = _build_preview_html(title, theme, components, app_code)

    return {
        "siteId": site_id,
        "downloadUrl": f"/api/ai/download/{site_id}",
        "title": title,
        "appCode": app_code,
        "components": components,
        "indexCssCode": css,
        "previewHtml": preview_html,
        "tailwind": True,
    }


@router.get("/api/ai/download/{site_id}")
async def download_ai_project(site_id: str):
    if not re.fullmatch(r"[a-z0-9-]+", site_id):
        raise HTTPException(status_code=400, detail="Invalid site id.")
    zip_path = AI_GENERATED_ROOT / f"{site_id}.zip"
    if not zip_path.is_file():
        raise HTTPException(status_code=404, detail="Generated project not found.")
    return FileResponse(zip_path, filename=f"{site_id}.zip", media_type="application/zip")