// ─── Middleware ────────────────────────────────────────────────────────────
// Reserved, auto-discovered filename (Middleware.ts). Optional - if this
// file doesn't exist, nothing changes.
//
// Runs first on every page resolution attempt - every dev request, and every
// page in `build`/`dev-build` (called with the sitemap's own url, no live
// Request). Return undefined to skip ("use the normal streak.sitemap.json
// entry, or 404 if there isn't one"); return a RenderConfig to render that
// instead - this is what lets a URL that isn't statically listed in
// streak.sitemap.json still resolve to a real page ("any route"), or lets a
// URL that IS listed be swapped out for a different page's config.
// ─────────────────────────────────────────────────────────────────────────────

import { readFileSync } from "fs";
import { join } from "path";
import type { RenderConfig } from "streak-forge/core";

interface SitemapEntry {
  url: string;
  renderConfig: RenderConfig;
}

// Cached at module scope - read once, reused for every call, same as any
// other module-level setup work a real Middleware might do.
let sitemapCache: SitemapEntry[] | undefined;
const loadSitemap = (): SitemapEntry[] => {
  if (!sitemapCache) {
    const sitemapPath = join(import.meta.dir, "../../streak.sitemap.json");
    sitemapCache = JSON.parse(readFileSync(sitemapPath, "utf-8")) as SitemapEntry[];
  }
  return sitemapCache;
};

// Maps a trigger URL -> the streak.sitemap.json url whose render config it
// should use instead. "/dynamic/test" isn't in streak.sitemap.json at all -
// this is the "any route" case: a URL Middleware resolves to a real page
// even though nothing in the sitemap lists it.
const routeMap: Record<string, string> = {
  "/dynamic/test": "/",
};

const resolveMiddleware = async (url: string, _req?: Request): Promise<RenderConfig | undefined> => {
  console.info(`[Middleware] resolving URL: ${url}`);

  const targetUrl = routeMap[url];
  if (!targetUrl) return undefined;

  const targetEntry = loadSitemap().find((entry) => entry.url === targetUrl);
  if (!targetEntry) return undefined;

  console.info(`[Middleware] resolved "${url}" -> "${targetUrl}" page's render config (from streak.sitemap.json)`);

  return targetEntry.renderConfig;
};

export default resolveMiddleware;
