#!/usr/bin/env bun
/**
 * streak-validate
 *
 * Validates the project structure against streak.sitemap.json:
 *   1. Unique renderIds
 *   2. All handler / layout / widget files exist on disk
 *   3. Valid loadingStrategy values
 *   4. Every sitemap widget has a WidgetPlaceholder in its layout
 *   5. Handler source conventions (export default, status: 200)
 *   6. Widget source conventions (export default, optional-chaining on data)
 *
 * Exit code 0 = pass  |  Exit code 1 = one or more errors
 *
 * Usage:
 *   bun run src/scripts/streak-validate.ts
 *   (or add "validate": "bun run src/scripts/streak-validate.ts" to package.json)
 */

import { existsSync, readFileSync } from "fs";
import { resolve, join } from "path";

// ── Paths ─────────────────────────────────────────────────────────────────────
const ROOT = resolve(import.meta.dir, "../../");
const SRC  = join(ROOT, "src");

// ── Load sitemap ──────────────────────────────────────────────────────────────
const sitemapPath = join(ROOT, "streak.sitemap.json");
if (!existsSync(sitemapPath)) {
  console.error("✖  streak.sitemap.json not found at project root");
  process.exit(1);
}

type Widget = { id: string; type: string; loadingStrategy?: string };
type PageConfig = {
  renderId: string;
  dataHandler: string;
  rootLayout: string;
  widgets: Widget[];
};
type Page = { url: string; renderConfig: PageConfig };

const sitemap: Page[] = JSON.parse(readFileSync(sitemapPath, "utf-8"));

let errors   = 0;
let warnings = 0;

const err  = (msg: string) => { console.error(`  ✖  ${msg}`); errors++;   };
const warn = (msg: string) => { console.warn( `  ⚠  ${msg}`); warnings++; };
const ok   = (msg: string) => { console.info( `  ✓  ${msg}`);             };
const hr   = ()            => { console.info("  " + "─".repeat(60));      };

// ── 1. Unique renderIds ───────────────────────────────────────────────────────
console.info("\n[1] renderId uniqueness");
hr();
const seen = new Set<string>();
for (const page of sitemap) {
  const id = page.renderConfig?.renderId;
  if (!id) {
    err(`Page "${page.url}" is missing renderConfig.renderId`);
    continue;
  }
  if (seen.has(id)) {
    err(`Duplicate renderId: "${id}" (url: ${page.url})`);
  } else {
    seen.add(id);
    ok(`renderId "${id}" is unique`);
  }
}

// ── 2. File existence + valid loadingStrategy ─────────────────────────────────
console.info("\n[2] Handler / layout / widget file existence");
hr();
const VALID_STRATEGIES = new Set(["lazy"]);

for (const page of sitemap) {
  const cfg = page.renderConfig;
  if (!cfg) { err(`Page "${page.url}" is missing renderConfig`); continue; }

  // Handler
  const handlerFile = `${cfg.dataHandler}.ts`;
  const handlerPath = join(SRC, "handlers", handlerFile);
  if (!existsSync(handlerPath)) {
    err(`Handler not found: src/handlers/${handlerFile}  (url: ${page.url})`);
  } else {
    ok(`Handler: src/handlers/${handlerFile}`);
  }

  // Layout
  const layoutFile = `${cfg.rootLayout}.tsx`;
  const layoutPath = join(SRC, "layouts", layoutFile);
  if (!existsSync(layoutPath)) {
    err(`Layout not found: src/layouts/${layoutFile}  (url: ${page.url})`);
  } else {
    ok(`Layout: src/layouts/${layoutFile}`);
  }

  // Widgets
  for (const w of (cfg.widgets ?? [])) {
    if (!w.id)   { err(`Widget entry under "${page.url}" is missing "id"`);   continue; }
    if (!w.type) { err(`Widget entry under "${page.url}" is missing "type"`); continue; }

    const widgetFile = `${w.type}.tsx`;
    const widgetPath = join(SRC, "widgets", widgetFile);
    if (!existsSync(widgetPath)) {
      err(`Widget not found: src/widgets/${widgetFile}  (id="${w.id}", url: ${page.url})`);
    } else {
      ok(`Widget: src/widgets/${widgetFile}`);
    }

    if (w.loadingStrategy !== undefined && !VALID_STRATEGIES.has(w.loadingStrategy)) {
      err(
        `Invalid loadingStrategy "${w.loadingStrategy}" for widget "${w.id}" — ` +
        `only "lazy" is supported (url: ${page.url})`
      );
    }
  }
}

// ── 3. WidgetPlaceholders in layouts ─────────────────────────────────────────
console.info("\n[3] WidgetPlaceholder coverage in layouts");
hr();
for (const page of sitemap) {
  const cfg = page.renderConfig;
  if (!cfg) continue;

  const layoutPath = join(SRC, "layouts", `${cfg.rootLayout}.tsx`);
  if (!existsSync(layoutPath)) continue;

  const layoutSrc = readFileSync(layoutPath, "utf-8");

  for (const w of (cfg.widgets ?? [])) {
    if (!w.id || !w.type) continue;
    const hasId   = new RegExp(`id=["'\`]${w.id}["'\`]`).test(layoutSrc);
    const hasType = new RegExp(`type=["'\`]${w.type}["'\`]`).test(layoutSrc);
    if (!hasId || !hasType) {
      err(
        `Layout "${cfg.rootLayout}" is missing WidgetPlaceholder for ` +
        `id="${w.id}" type="${w.type}"  (url: ${page.url})`
      );
    } else {
      ok(`WidgetPlaceholder id="${w.id}" type="${w.type}" ✓ in ${cfg.rootLayout}.tsx`);
    }
  }
}

// ── 4. Handler source conventions ────────────────────────────────────────────
console.info("\n[4] Handler source conventions");
hr();
for (const page of sitemap) {
  const cfg = page.renderConfig;
  if (!cfg) continue;

  const handlerPath = join(SRC, "handlers", `${cfg.dataHandler}.ts`);
  if (!existsSync(handlerPath)) continue;

  const src = readFileSync(handlerPath, "utf-8");

  if (!/export\s+default/.test(src)) {
    err(`Handler "${cfg.dataHandler}" is missing "export default"`);
  } else {
    ok(`Handler "${cfg.dataHandler}" has export default`);
  }

  if (!/status\s*:\s*200/.test(src)) {
    warn(`Handler "${cfg.dataHandler}" does not appear to return { status: 200 }`);
  } else {
    ok(`Handler "${cfg.dataHandler}" returns status: 200`);
  }
}

// ── 5. Widget source conventions ─────────────────────────────────────────────
console.info("\n[5] Widget source conventions");
hr();

// Collect unique widget types across all pages
const widgetTypes = new Set<string>();
for (const page of sitemap) {
  for (const w of (page.renderConfig?.widgets ?? [])) {
    if (w.type) widgetTypes.add(w.type);
  }
}

for (const widgetType of widgetTypes) {
  const widgetPath = join(SRC, "widgets", `${widgetType}.tsx`);
  if (!existsSync(widgetPath)) continue;

  const src = readFileSync(widgetPath, "utf-8");

  // Must have export default
  if (!/export\s+default/.test(src)) {
    err(`Widget "${widgetType}" is missing "export default"`);
  } else {
    ok(`Widget "${widgetType}" has export default`);
  }

  // Warn on non-optional props.data access
  // Matches "props.data." but not "props?.data?." or "props?.data."
  const directAccess = /(?<!\?)props\.data\./.test(src);
  if (directAccess) {
    warn(
      `Widget "${widgetType}": found "props.data." — ` +
      `use optional chaining "props?.data?.field" (data may be undefined)`
    );
  }

  // Warn on React hooks
  const hookMatch = src.match(/\buse[A-Z]\w+\s*\(/g);
  if (hookMatch) {
    const hooks = [...new Set(hookMatch.map(h => h.replace(/\s*\($/, "")))];
    warn(
      `Widget "${widgetType}": found React hook(s): ${hooks.join(", ")} — ` +
      `widgets are stateless at runtime. Use Script for client-side logic.`
    );
  }

  // Warn on Script without options when children reference identifiers that look
  // like they could be closed-over server values (heuristic: non-trivial function body)
  const scriptNoOptions = src.match(/<Script\s+id=["'][^"']+["']\s*>/g);
  if (scriptNoOptions && scriptNoOptions.length > 0) {
    warn(
      `Widget "${widgetType}": Script tag(s) without "options" prop detected. ` +
      `If the script uses server-derived values, pass them via options={{ ... }}.`
    );
  }
}

// ── 6. Public assets referenced in handlers ───────────────────────────────────
console.info("\n[6] Handler-referenced local assets exist in public/");
hr();
for (const page of sitemap) {
  const cfg = page.renderConfig;
  if (!cfg) continue;

  const handlerPath = join(SRC, "handlers", `${cfg.dataHandler}.ts`);
  if (!existsSync(handlerPath)) continue;

  const src = readFileSync(handlerPath, "utf-8");

  // Find all string values that look like local paths (start with /)
  // but are not external URLs
  const localPaths = [...src.matchAll(/["'](\/(images|assets|styles)[^"']+)["']/g)]
    .map(m => m[1]);

  for (const assetPath of localPaths) {
    const diskPath = join(ROOT, "public", assetPath);
    if (!existsSync(diskPath)) {
      warn(
        `Handler "${cfg.dataHandler}" references "${assetPath}" ` +
        `but public${assetPath} does not exist`
      );
    } else {
      ok(`Asset exists: public${assetPath}`);
    }
  }
}

// ── Summary ───────────────────────────────────────────────────────────────────
console.info("\n" + "═".repeat(64));
if (errors === 0 && warnings === 0) {
  console.info("  ✓  All checks passed — project structure is valid.");
} else {
  if (errors > 0)   console.error(`  ✖  ${errors} error(s) found.`);
  if (warnings > 0) console.warn( `  ⚠  ${warnings} warning(s) found.`);
}
console.info("═".repeat(64) + "\n");

if (errors > 0) process.exit(1);
