# Streak.js Code Generation Rules (Strict)

These rules are mandatory. Violating any of them is incorrect code generation.

---

## 1. Widgets (render-time, stateless)

- Widgets render ONCE at build time. No browser re-render.
- NEVER use `useState`, `useEffect`, `useRef`, or any React hook in a widget.
- A widget is a pure function of `props`. All client-side behavior lives in `<Script>` components.
- ALWAYS read data with optional chaining + nullish coalescing. `props.data` is undefined when the handler returns nothing for the widget.

```tsx
// WRONG
const heading = props.data.heading;

// CORRECT
const heading = props?.data?.heading ?? "Default Heading";
```

Applies to EVERY field read from `props.data`.

---

## 2. Script blocks

- Script children are serialized with `.toString()`. Closures do NOT survive. Outer-scope variables are undefined in the browser.
- Any server/build value needed at runtime MUST go through `options` (JSON-serialized, passed as the 2nd IIFE argument).

```tsx
// WRONG
const accentColor = props?.data?.accentColor ?? "#818cf8";
<Script id="banner-init">
  {(gDom: any) => {
    document.getElementById("banner")!.style.color = accentColor; // undefined at runtime
  }}
</Script>

// CORRECT
<Script id="banner-init" options={{ color: props?.data?.accentColor ?? "#818cf8" }}>
  {(gDom: any, options: any) => {
    const el = document.getElementById("banner");
    if (el) el.style.color = options.color;
  }}
</Script>
```

- Never reference imports, constants, helper functions, or `props` inside the Script function. Define helpers INSIDE the function body.

---

## 3. IDs and IDs matching

- Set explicit, stable `id` attributes on every element a script touches. No generated/random IDs.
- IDs must be unique per page. NEVER use generic IDs: `modal`, `container`, `header`, `banner`, `content`, `wrapper`.
- Scope IDs to the widget: `` id={`share-modal-${props.widgetId}`} `` or prefix with the widget name (`hero-heading`).
- Widget `id` (instance key) must match EXACTLY, case-sensitive, in:
  - `streak.sitemap.json` → `widgets[].id`
  - Layout → `<WidgetPlaceholder id="..." />`
  - Handler return object key → `{ helloBanner: { ... } }`
- Widget `type` (component name) must match EXACTLY, case-sensitive, in:
  - `streak.sitemap.json` → `widgets[].type`
  - Layout → `<WidgetPlaceholder type="..." />`
  - Filename → `src/widgets/<Type>.tsx`
- `id` and `type` need not equal each other. Each `id` is unique within a page's `widgets[]`; the same `type` may repeat with different ids.
- Every sitemap entry needs a globally unique `renderConfig.renderId`.

---

## 4. Vanilla JS inside Script blocks

### Variables
- `const` by default, `let` for reassigned values. NEVER `var`.

### DOM queries
- ALWAYS null-check `getElementById`, `querySelector`, `closest`. Use `if (!el) return;` or `?.`.
- Scope queries to the widget root, never bare `document.querySelectorAll(".tab-item")`:

```ts
const root = document.getElementById("my-widget-root");
if (!root) return;
const tabs = root.querySelectorAll(".tab-item");
```

- Use widget-prefixed class names for anything queried by script.
- Cache DOM references OUTSIDE event handlers. Never query the DOM inside scroll/mousemove/resize/input handlers.

### Event listeners
- Script blocks re-run on every SPA navigation. Listeners accumulate unless removed.
- Always `removeEventListener` before `addEventListener` for named handlers:

```ts
window.removeEventListener("scroll", onScroll);
window.addEventListener("scroll", onScroll, { passive: true });
```

- One-time listeners: use `{ once: true }`.
- ALWAYS pass `{ passive: true }` for `scroll`, `mousemove`, `touchstart`, `touchmove` (unless calling `preventDefault()`).
- Listeners registered OUTSIDE managed Script scope (inside `sf:pageload` handlers, third-party callbacks, or on persistent elements such as `<html>`, sticky header, fixed overlay) MUST be removed before adding.
- Never bind the same event twice on one element: no JSX `onClick` AND `addEventListener`. Use `addEventListener` in Script blocks only.

### Timers
- `setInterval` / long `setTimeout` must be cleared on re-run. Store the id on `window` under a namespaced key:

```ts
const KEY = "__carousel_interval";
clearInterval((window as any)[KEY]);
(window as any)[KEY] = setInterval(updateSlide, 3000);
```

### Performance
- Debounce scroll/resize/input handlers that do DOM work: `gDom.debounce(fn, 16)`.
- Prefer ONE shared `IntersectionObserver` (layout script, re-observe on `sf:pageload`) over one per widget.

### Styling from scripts
- Toggle classes (`classList.add/remove/toggle`). Do NOT assign `el.style.display`, `backgroundColor`, `width`, etc.
- Direct `style` writes only for values computed at runtime that cannot be a class (e.g. `translateX(${offset}px)`).

### Scroll lock
- Never set `document.body.style.overflow` independently from multiple scripts. Use a shared counter:

```ts
const lock = () => {
  const n = parseInt(document.body.dataset.scrollLocks || "0") + 1;
  document.body.dataset.scrollLocks = String(n);
  document.body.style.overflow = "hidden";
};
const unlock = () => {
  const n = Math.max(0, parseInt(document.body.dataset.scrollLocks || "0") - 1);
  document.body.dataset.scrollLocks = String(n);
  if (n === 0) document.body.style.overflow = "";
};
```

### Safe content
- NEVER set `innerHTML` with CMS/user/data values. Use `textContent` or build nodes with `createElement`.
- `JSON.stringify` output is text, not markup.

### State
- Script variables are re-initialized on every run. For state that survives SPA navigation use `sessionStorage`; across reloads use `localStorage` or cookies.

---

## 5. Third-party JS

- Libraries loaded via `gDom.loadPackage()` MUST exist in `public/assets/js/` (e.g. `motion.js`, `lenis.min.js`).
- These files are NOT generated by a build step. They are committed to git.
- A missing file makes `loadPackage` resolve but the library global is `undefined`. Always guard: `if (typeof Lenis === "undefined") return;`.

---

## 6. Output checklist (self-verify before returning)

1. No React hooks in any widget.
2. Every `props.data.*` access uses `?.` and `??`.
3. No outer-scope variable referenced inside any Script function; all passed via `options`.
4. Every `getElementById` / `querySelector` result is null-checked.
5. No `var`. No generic IDs. IDs scoped to the widget.
6. Every `addEventListener` on window/document is preceded by `removeEventListener` (or uses `{ once: true }`).
7. Scroll/mousemove/touchstart/touchmove listeners have `{ passive: true }`.
8. Every `setInterval` is cleared before being re-created.
9. No `innerHTML` with dynamic data. No direct `el.style.*` unless runtime-computed.
10. Widget `id` / `type` identical across sitemap, layout, handler, and filename.
11. Unique `renderId` per sitemap entry.
12. All third-party JS referenced exists in `public/assets/js/`.
