# TailwindCSS Rules (Strict)

These rules are mandatory. Violating them is incorrect code generation.

## Output Model (READ FIRST)

This project uses Tailwind CSS v3.4 with **semantic component classes defined via `@apply`**.

- In the TSX, `className` holds short semantic class names (e.g. `hero-card`, `hero-title`), prefixed with the widget name in kebab-case.
- In the CSS part, every semantic class is defined once with `@apply` and Tailwind utilities.
- Custom semantic classes defined with `@apply` are REQUIRED. Do not put long utility strings directly in `className`.
- If any rule below conflicts with the required output format given in the task prompt, the task prompt's output format wins.

Example:

```tsx
<div className="hero-card">
  <h1 className="hero-title">Title</h1>
</div>
```

```css
.hero-card { @apply flex items-center justify-center rounded-2xl p-8 md:p-10; }
.hero-title { @apply text-4xl font-bold tracking-tight md:text-5xl; }
```

## Core Principle

Inside `@apply`, always use:

- Tailwind default utility classes
- Tailwind design scale

Prefer approximation using the Tailwind scale over pixel-perfect precision.

## Universal Utility Rule

Do NOT use arbitrary Tailwind values (`utility-[value]`) in any category. This applies to every utility: text, leading, tracking, w, h, min/max sizes, margin, padding, gap, space, rounded, shadow, border, inset (top/left/right/bottom), translate, duration, delay, grid-cols, bg, from/via/to, z, aspect, flex, basis, blur, ring, outline, rotate, scale, skew.

Invalid: `text-[15px]`, `leading-[28px]`, `rounded-[22px]`, `shadow-[0_24px_50px_-12px_rgba(0,0,0,0.25)]`, `gap-[27px]`, `px-[31px]`, `w-[600px]`, `text-[#F26A2E]`

Valid equivalents: `text-sm`, `leading-7`, `rounded-xl`, `shadow-lg`, `gap-6`, `px-8`, `w-full`, `text-orange-500`

## Mandatory Decision Order

1. **Tailwind default utility.** Always check whether Tailwind already provides it.
2. **Approximate with the nearest Tailwind scale value.** ~15px font -> `text-sm`; ~26px spacing -> `gap-6`; ~18px radius -> `rounded-xl`.
3. **Plain CSS property in the same rule** (not `[]`) when `@apply` cannot express it. Use this for exact values that matter: `min-height: 88vh;`, `font-size: 1.05rem;`, `font-family: ...;`, `clamp(...)`, `url(...)`, `grid-template-areas`, `::before` / `::after` content, `@keyframes`, CSS variables.

Never put `[]` values inside `@apply`.

Only default Tailwind tokens exist. `tailwind.config.js` has no custom theme, so do NOT invent tokens such as `w-150`, `h-17`, `text-primary`, `bg-brand`, `text-ink`, `bg-teal`.

## Typography

Use the Tailwind scale: `text-xs` ... `text-5xl`, `font-normal|medium|semibold|bold`, `leading-none|tight|snug|normal|relaxed|loose`, `tracking-tight|normal|wide|wider|widest`.

For font families, use a plain CSS `font-family` declaration in the rule.

## Spacing

Use the Tailwind spacing scale: `p-4`, `p-6`, `p-8`, `px-*`, `py-*`, `gap-4|6|8`, `space-y-4|6`.

## Sizing

Use `w-full`, `w-auto`, `h-12`, `h-14`, `h-16`, `max-w-xl|2xl|3xl|7xl`, `min-h-screen`. For other exact sizes, use plain CSS (`width: 600px;`).

## Border Radius, Shadow, Effects

- Radius: `rounded-none|sm|md|lg|xl|2xl|3xl|full`
- Shadow: `shadow-sm|shadow|shadow-md|shadow-lg|shadow-xl|shadow-2xl|shadow-inner`
- Effects: `opacity-80`, `blur-sm`, `backdrop-blur-md`, `transition`, `duration-300`, `ease-in-out`

## Colors

Use the nearest default Tailwind palette color (`slate`, `zinc`, `orange`, `teal`, ...). Never use hex values or `[]` colors in `@apply`. If the original uses CSS variables (e.g. `hsl(var(--ink))`) and the exact value matters, keep it as a plain CSS declaration in the rule.

## Layout

Use `container`, `flex`, `grid`, `hidden`, `block`, `inline-flex`, `aspect-video`, `overflow-hidden`, `sticky`, `relative`, `absolute`. Responsive and state variants (`sm:`, `md:`, `lg:`, `xl:`, `hover:`, `focus:`) are allowed inside `@apply`.

## Icons and SVG

- Do NOT add imports or new icon libraries. Widgets have no imports.
- Keep existing inline `<svg>` exactly as-is.

## JS Hook Classes

Keep original class names only if JS libraries depend on them (swiper, slick, owl, aos, wow, glightbox, fancybox, etc.). Place them after the semantic classes.

## Custom CSS Rule

- Every semantic class used in the TSX MUST have a rule in the CSS part.
- One rule per class, using `@apply` first, then plain CSS properties for anything `@apply` cannot express.
- Do not wrap rules in `@layer`. Do not include `@tailwind` directives. The server does both.
- No `<style>` tags.

## Rule Priority

1. Output format from the task prompt
2. Tailwind default utility
3. Nearest Tailwind scale value
4. Plain CSS property (never `[]`)

If uncertain, choose the Tailwind default.