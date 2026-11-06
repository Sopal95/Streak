# hello-streak-app

A reference "Hello World" application built with **Streak.js** (`streak-forge`) — a static site generator that pre-renders every page to plain HTML at build time. No framework JS ships to the browser by default.

---

## What this app demonstrates

| Feature | Widget |
|---|---|
| `Preload` — resource hinting | `HelloBanner` (hero image only — `tailwind.css` is a small render-blocking stylesheet the browser already discovers immediately, so it isn't preloaded) |
| `Script` — client interactivity via serialized IIFE | `HelloNav`, `HelloBanner`, `HelloTerminal` |
| `Dynamic` — deferred DOM injection on demand | `HelloFeatures`, `HelloMessage` |
| `loadPackage` — third-party JS via Web Worker | `HelloAnimated` (Motion.js) |
| `loadingStrategy: "lazy"` — deferred widget JS | `HelloFeatures`, `HelloTerminal`, `HelloAnimated`, `HelloMessage`, `HelloFooter` |

---

## Requirements

| Tool | Version |
|---|---|
| Bun | ≥ 1.2 |
| Node.js | ≥ 20 (for ESLint) |
| Python 3 | any (for `bun run start`) |

---

## Quick start

```bash
# 1. Install dependencies
bun install

# 2. Start development (Tailwind watch + streak-forge dev server, runs in parallel)
bun run dev

# 3. Open the local dev server URL printed by streak-forge
```

---

## All commands

```bash
# Development
bun run dev           # Tailwind watch + streak-forge dev server (parallel)
bun run dev:streak    # streak-forge dev server only
bun run css-dev       # Tailwind CSS watch only

# Production build
bun run build         # compile CSS + streak-forge pre-build  →  out/

# Preview the build
bun run start         # serve on http://localhost:8000 with real Cache-Control (see below)

# Quality checks  (run all three before every build)
bun run validate      # structural: sitemap ↔ file system consistency
bun run lint          # ESLint with custom Streak rules
bun run lint:fix      # ESLint auto-fix
bun run typecheck     # tsc --noEmit

# Testing
bun test              # run all tests once
bun test --watch      # watch mode
```

---

## Project structure

```
hello-streak-app/
├── streak.sitemap.json          # page registry — source of truth for all pages
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── eslint.config.js             # ESLint 9 flat config + inline Streak plugin
│
├── src/
│   ├── handlers/
│   │   ├── HomeDataHandler.ts   # async data provider — shared by "/", "/docs", "/about"
│   │   ├── CommonHandler.ts     # once-per-build shared data (branding, nav links)
│   │   └── Middleware.ts        # route resolution hook ("/dynamic/test" -> "/" demo)
│   ├── layouts/
│   │   └── MainLayout.tsx       # full <html> layout with WidgetPlaceholder slots
│   ├── widgets/
│   │   ├── PageHead.tsx         # <head> content — title, meta, stylesheet link
│   │   ├── HelloNav.tsx         # navigation bar (Script for mobile menu + streak badge)
│   │   ├── HelloBanner.tsx      # hero section (Preload of the hero image + Script)
│   │   ├── HelloFeatures.tsx    # feature cards (Dynamic + Script)
│   │   ├── HelloTerminal.tsx    # typewriter build-pipeline demo (Script)
│   │   ├── HelloAnimated.tsx    # Motion.js animations (loadPackage)
│   │   ├── HelloMessage.tsx     # testimonial / quote (Dynamic + Script)
│   │   └── HelloFooter.tsx      # site footer
│   ├── scripts/
│   │   ├── streak-validate.ts   # structural validator (bun run validate)
│   │   └── test-render.ts       # exercises the render() API directly (bun run test-render)
│   ├── common/styles/
│   │   └── input.css            # Tailwind entry point
│   └── tests/
│       ├── HomeDataHandler.test.ts
│       ├── CommonHandler.test.ts
│       ├── Middleware.test.ts
│       ├── streakComponents.test.ts   # Script "options" bridge coverage
│       └── widgets.test.ts
│
├── public/
│   ├── images/streak-logo.svg
│   └── assets/js/motion.js      # Motion.js — committed, loaded via Web Worker
│
├── server.py                    # local preview server with real Cache-Control (see below)
│
└── out/                         # build output (gitignored)
    └── <version>/
        └── raw-content.json
```

---

## How Streak.js works

```
streak.sitemap.json
       │
       ├── dataHandler ──►  HomeDataHandler.ts   runs once at build time
       │                    returns { status: 200, PageHead: {...}, HelloBanner: {...}, ... }
       │
       ├── rootLayout  ──►  MainLayout.tsx        full <html> doc with WidgetPlaceholder slots
       │
       └── widgets[]   ──►  src/widgets/*.tsx     each receives { data: handlerData[widgetId] }
                            rendered to HTML strings, injected into layout slots
```

**Build output:** `out/homeRenderId/index.html` — a complete, self-contained static HTML file. Nothing renders at runtime; the browser receives finished HTML.

---

## Local preview & caching

`bun run start` runs `server.py` — a small stdlib-only (`http.server`) preview
server that stands in for `python3 -m http.server` with real Cache-Control
headers, ETag-based conditional GET (`304`), and gzip. It serves `public/` at
`/` (the app's real, referenced-today assets), falling back to `out/` for
anything else.

Nothing here is content-hashed (no `?v=` query strings, no per-build path
segments), so every rule below is a deliberate tradeoff between "cache for
real speed" and "don't serve something stale for too long":

| Path | Cache-Control | Why |
|---|---|---|
| Images / fonts (`.svg .png .jpg .webp .ico .woff` …) | `public, max-age=86400` | Filename-stable, not content-hashed — a bounded (1 day) staleness window, with ETag as insurance if the content changes within it. |
| `/assets/js/*.js` (e.g. `motion.js`, loaded via `gDom.loadPackage`) | `public, max-age=86400` | Same reasoning as images — committed, not content-hashed. |
| Anything served from `out/` | `no-cache` | Page content — always revalidate. |
| Anything else | `no-cache` | Conservative default. |

Each request logs a line showing `HIT (304)` (revalidated, no body sent) vs
`MISS` (full transfer), with byte count and response time — so caching
behavior is directly observable instead of guessed at from a browser's
network panel:

```
[200] MISS       /images/streak-logo.svg  44005B  3.4ms
[304] HIT (304)  /images/streak-logo.svg  0B  0.6ms
```

```bash
python3 server.py           # default port 8000, serves public/ (+ out/ fallback)
python3 server.py 8010      # custom port
```

### The general pattern, for when a build is versioned

`server.py`'s rules above use bounded TTLs (1 day, or always-revalidate)
because this app's own build doesn't content-hash or version any of its
output paths today — the file on disk gets overwritten in place, so nothing
guarantees a stale cached copy is actually wrong to keep serving.

The moment a build *does* stamp a version into either the filename (a
`?v=<version>` query string) or the path itself (`/<page>/<version>/…`), the
correct policy for that file changes completely — instead of a bounded TTL,
it can be cached **forever**, because a real change always produces a new
URL rather than overwriting the old one. This is the general 3-group pattern
used elsewhere in the Streak.js toolchain once output reaches that stage:

| Group | Example | Versioned by | Cache-Control |
|---|---|---|---|
| 1. Fixed-path runtime files | a bundle referenced everywhere as `/app.js?v=<buildId>` | query string | `public, max-age=31536000, immutable` |
| 2. Per-page content files | `/<page>/<contentVersion>/common.js` | directory path | `public, max-age=31536000, immutable` |
| 3. Unversioned page entry points | `index.html`, `index.json` | not versioned — must revalidate | `no-cache` + `ETag`/`Last-Modified` |

The rule for matching a request path against these, in order:

1. Exact match against the known fixed-path runtime files → group 1's `immutable` rule.
2. Path ends in a per-page content filename, or matches a per-page content
   directory shape → group 2's `immutable` rule.
3. Filename is exactly `index.html` or `index.json` → group 3's `no-cache` +
   validator rule (without a validator, every request becomes a full
   re-download — safe, but wasteful).
4. Everything else (unversioned static assets, e.g. `public/` in this app
   today) → a bounded TTL, tuned to how often that content actually changes.

Groups 1 and 2 both resolve to `immutable` for the same underlying reason:
once a real content change always produces a brand-new URL, there is no
"stale" state left for a long `max-age` to cause — the old URL's content
genuinely never changes again, so there's nothing to revalidate. Group 3 is
the opposite case (fixed path, content *does* change) and must never get a
long `max-age`, or a returning visitor keeps seeing pre-deploy content until
it expires regardless of what the build actually produced.

---

## Validation

This project ships a structural validator (`src/scripts/streak-validate.ts`) and custom ESLint rules. They catch common Streak mistakes before `streak-forge pre-build` runs.

```bash
bun run validate
```

Checks performed:

| # | Check |
|---|---|
| 1 | `renderId` values are globally unique |
| 2 | All handler / layout / widget files referenced in the sitemap exist on disk |
| 3 | `loadingStrategy` values are valid (`"lazy"` only) |
| 4 | Every sitemap widget has a matching `WidgetPlaceholder` in its layout |
| 5 | Handler files have `export default` and return `status: 200` |
| 6 | Widget files have `export default`; warns on unsafe `props.data.` access and hook usage |
| 7 | Local asset paths referenced in handlers exist in `public/` |

### Custom ESLint rules (`eslint.config.js`)

| Rule | Level | What it catches |
|---|---|---|
| `streak/no-hooks-in-widgets` | error | `useState`, `useEffect`, etc. in `src/widgets/` |
| `streak/require-default-export` | error | Missing `export default` in widgets / layouts / handlers |
| `streak/no-direct-data-access` | warn | `props.data.x` without optional chaining in widgets |
| `streak/script-options-bridge` | warn | Script children whose first param isn't named `gDom` |

---

## Key concepts

### Script — passing data to the browser

The `Script` component's child function is serialized via `.toString()` and executed as an IIFE. It cannot close over component-scope variables. Use `options` to pass server-derived values:

```tsx
// Wrong — `color` is undefined after serialization
<Script id="x">{() => { el.style.color = color; }}</Script>

// Correct — pass through options
<Script id="x" options={{ color }}>
  {(gDom: any, options: any) => { el.style.color = options.color; }}
</Script>
```

### Dynamic — deferred DOM injection

Content inside `<Dynamic id="panel">` is stripped from the initial HTML and injected only when `gDom.loadDynamicComponent("panel", callback)` is called:

```tsx
<Dynamic id="my-panel">
  <div id="my-panel-content" style={{ opacity: 0 }}>...</div>
</Dynamic>

<Script id="my-script">
  {(gDom: any) => {
    document.getElementById("btn")?.addEventListener("click", () => {
      gDom.loadDynamicComponent("my-panel", () => {
        const el = document.getElementById("my-panel-content");
        if (el) requestAnimationFrame(() => { el.style.opacity = "1"; });
      });
    });
  }}
</Script>
```

### loadPackage — third-party JS via Web Worker

Loads a file from `public/assets/js/` off the main thread:

```tsx
<Script id="my-script">
  {(gDom: any) => {
    gDom.loadPackage("js/motion.js").then(() => {
      const { animate } = (gDom as any).Motion;
      animate("#el", { opacity: [0, 1] }, { duration: 0.5 });
    });
  }}
</Script>
```

---

## Testing

Tests use **bun:test** (Jest-compatible, zero extra packages).

```bash
bun test
```

Test files live in `src/tests/`. The pattern is to test handler data shape and integrity — not DOM output, since widgets produce static HTML.

---

## Tech stack

- **Streak.js / streak-forge** — static site generator
- **Bun** — runtime, package manager, test runner
- **TailwindCSS v3** — utility-first CSS
- **TypeScript** — strict mode
- **ESLint 9** — flat config with inline Streak plugin
- **Motion.js** — animation library (loaded via Web Worker)
- **concurrently** — parallel dev scripts

---

## License

MIT
