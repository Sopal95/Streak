# CLAUDE.md — hello-streak-app

This project is a **Streak.js** static site application. Read this file in full before making changes.

---

## Project overview

A reference "Hello World" app built with **Streak.js** (`streak-forge`), a React-based static site
generator that pre-renders every page to plain HTML at build time. No React or framework JS ships
to the browser by default.

| Concern | Tool |
|---|---|
| Runtime / package manager | **Bun** |
| Styling | **TailwindCSS v3** (compiled → `public/styles/tailwind.css`) |
| Language | **TypeScript** strict mode |
| Linting | **ESLint 9** flat config + inline Streak plugin (`eslint.config.js`) |
| Testing | **bun:test** (Jest-compatible, zero extra packages) |
| Validation | `bun run validate` → `src/scripts/streak-validate.ts` |

---

## Essential commands

```bash
# Development
bun run dev           # parallel: Tailwind watch + streak-forge dev server
bun run dev:streak    # streak-forge dev only
bun run css-dev       # Tailwind watch only

# Build
bun run build         # css-build + streak-forge pre-build  →  out/

# Preview build output  (serves out/ on http://localhost:8000)
bun run start

# Validation — run these before every build
bun run validate      # structural: sitemap ↔ file system consistency
bun run lint          # ESLint + custom Streak rules
bun run lint:fix      # ESLint auto-fix
bun run typecheck     # tsc --noEmit (no emit, type errors only)

# Testing
bun test              # run all tests once
bun test --watch      # watch mode
```

---

## Architecture

```
streak.sitemap.json              ← single source of truth for all pages
        │
        ├── dataHandler ──►  src/handlers/*.ts      async fn → data object
        ├── rootLayout  ──►  src/layouts/*.tsx       full <html> + WidgetPlaceholder slots
        └── widgets[]   ──►  src/widgets/*.tsx       stateless React; receive props.data
```

Build output: `out/<renderId>/index.html` — complete, self-contained static HTML.

**Nothing renders at runtime.** The browser receives finished HTML.

---

## Key files

| File | Purpose |
|---|---|
| `streak.sitemap.json` | Page registry — add/modify pages here |
| `src/handlers/HomeDataHandler.ts` | Async data provider for the home page |
| `src/layouts/MainLayout.tsx` | Full HTML document with WidgetPlaceholder slots |
| `src/widgets/*.tsx` | Individual page sections (stateless React) |
| `src/scripts/streak-validate.ts` | Structural validator (`bun run validate`) |
| `eslint.config.js` | ESLint 9 flat config + inline Streak-specific rules |
| `public/assets/js/motion.js` | Motion.js — committed to repo, loaded via Web Worker |
| `public/styles/tailwind.css` | Compiled CSS — gitignored, regenerated on every build |

---

## Streak.js rules — always follow these

### Widgets (`src/widgets/*.tsx`)

- Props type: `{ data?: YourType }` — `data` is always optional
- **Always** use optional chaining: `props?.data?.field ?? defaultValue`
  Never: `props.data.field` (data is undefined when handler omits that key)
- Must have `export default` — Streak imports by default export
- **No React hooks** (`useState`, `useEffect`, `useRef`, etc.) — widgets are stateless at runtime
- Filename (no extension) must exactly match `type` in sitemap **and** `type` in `WidgetPlaceholder`

### Data handlers (`src/handlers/*.ts`)

- Must be `export default` async function returning `{ status: 200, WidgetId: data, ... }`
- Each key in the return object maps to a widget `id` in the sitemap
- Filename (no extension) must match `dataHandler` in sitemap
- Runs **once at build time** — any async operation is allowed (API calls, file reads, DB queries)

### Layouts (`src/layouts/*.tsx`)

- Must render a complete `<html>` document (not a fragment)
- Every widget in `sitemap.widgets[]` must have a matching `<WidgetPlaceholder id="..." type="..." />`
- `id` and `type` on `WidgetPlaceholder` must exactly match sitemap entries
- Filename (no extension) must match `rootLayout` in sitemap

### Script component (client interactivity)

- `options` prop is the **only bridge** from server values to browser code
  The function is serialized via `.toString()` — it cannot close over widget-scope variables.

  ```tsx
  // WRONG — variable vanishes after serialization
  const color = props?.data?.color ?? "#fff";
  <Script id="x">{() => { el.style.color = color; }}</Script>

  // CORRECT — pass everything through options
  const color = props?.data?.color ?? "#fff";
  <Script id="x" options={{ color }}>
    {(gDom: any, options: any) => { el.style.color = options.color; }}
  </Script>
  ```

- Children signature must be `(gDom: any, options: any) => void`
- No `import` statements inside Script — runs in a plain browser context
- `gDom` is `window` extended with: `loadPackage`, `loadDynamicComponent`, `onVisible`,
  `stall`, `debounce`, `geById`, `setCookie`, `getCookie`, `ftr`, `addResourceToBody`

### Dynamic component (deferred content)

- Content in `<Dynamic id="panel-id">` is **removed** from initial HTML
- Inject it with `gDom.loadDynamicComponent("panel-id", callback)` on user interaction
- Set `style={{ opacity: 0 }}` on injected content, fade in via `requestAnimationFrame` in the callback

### loadPackage (third-party JS via Web Worker)

- Place the file at `public/assets/js/yourlib.js` — **commit it to git** (not gitignored)
- Load from Script: `gDom.loadPackage("js/yourlib.js").then(() => { const lib = (gDom as any).LibGlobal; })`
- Path is relative to `/assets/` — `"js/motion.js"` → fetches `/assets/js/motion.js`

### Motion.js specific rules

| Correct | Wrong (crashes) |
|---|---|
| `scroll(animate(el, { scaleX: [0,1] }))` | `scroll(({ y }) => { y.progress })` |
| `inView(el, callback)` | `inView(el, cb, { margin: "-40px" })` |
| `spring({ stiffness, damping, restSpeed: 0.5 })` | `spring({ stiffness, damping })` — infinite oscillation |
| `.finished.then(...)` for sequencing | `async/await` inside Script (no top-level await) |

### Sitemap rules

- `renderId` must be **globally unique** across the entire sitemap
- `widgets[].id` → matches handler return key **and** `WidgetPlaceholder id`
- `widgets[].type` → matches widget filename **and** `WidgetPlaceholder type`
- `loadingStrategy: "lazy"` — JS loads after DOMContentLoaded; HTML is still present initially

---

## Validation workflow

After any structural change (new widget / layout / handler / sitemap entry), run **all three**:

```bash
bun run validate   # sitemap ↔ file system: missing files, duplicate renderIds, missing WidgetPlaceholders
bun run lint       # code-level Streak violations: hooks in widgets, missing default exports, unsafe data access
bun run typecheck  # TypeScript errors
```

All three must pass clean before `bun run build`.

---

## Common mistakes reference

| Mistake | Correct pattern |
|---|---|
| `props.data.field` | `props?.data?.field ?? default` |
| Closing over widget variables in Script | Pass via `options={{ value }}` |
| `useState` / `useEffect` in a widget | Widgets are stateless — use `Script` for client logic |
| Missing `export default` | Every widget, layout, and handler must `export default` |
| `scroll(({ y }) => y.progress)` | `scroll(animate(el, { scaleX: [0,1] }))` |
| `inView(el, cb, { margin: "..." })` | `inView(el, cb)` — omit the options argument |
| Referencing an image in handler that doesn't exist in `public/` | Add the file or remove the reference |
| Duplicate `renderId` in sitemap | Each page must have a unique `renderId` |
| Widget in sitemap but no `WidgetPlaceholder` in layout | Add the placeholder to the layout |
| `public/assets/js/*.js` in `.gitignore` | These files must be committed — they are static assets |

---

## Testing conventions

- Tests live in `src/tests/`
- Test handlers: call the handler directly, assert on return shape and data integrity
- Test widgets: extract pure logic (formatters, validators, defaults) into helpers and test those
- No DOM tests — widgets produce static HTML; test handler data integrity instead
- Test file naming: `*.test.ts` or `*.test.tsx`

---

## Code style

- Prefer `const` over `let`; never `var`
- Use `===` not `==`
- `console.log` is not allowed in production code (`console.info` / `console.error` / `console.warn` are OK)
- `any` is allowed only inside `Script` children (`gDom: any`, `options: any`) — everywhere else prefer explicit types
- No unused variables — prefix intentionally unused params with `_`
- Imports: use `type` imports where possible (`import type { Foo } from "..."`)
