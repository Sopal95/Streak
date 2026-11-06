/**
 * Tests for Middleware — the reserved route-resolution hook that runs before
 * every page render. `routeMap` in Middleware.ts currently covers the "any
 * route" case: "/dynamic/test" isn't in streak.sitemap.json at all, but
 * still resolves to a real page's renderConfig via this hook.
 *
 * Run with:  bun test
 */

import { describe, test, expect } from "bun:test";
import { readFileSync } from "fs";
import { join } from "path";
import resolveMiddleware from "../handlers/Middleware";
import type { RenderConfig } from "streak-forge/core";

const sitemapPath = join(import.meta.dir, "../../streak.sitemap.json");
const sitemap = JSON.parse(readFileSync(sitemapPath, "utf-8")) as Array<{
  url: string;
  renderConfig: RenderConfig;
}>;
const homeConfig = sitemap.find((entry) => entry.url === "/")?.renderConfig;

describe("Middleware — any-route resolution", () => {
  test("/dynamic/test (not in the sitemap) resolves to the '/' page's renderConfig", async () => {
    const result = await resolveMiddleware("/dynamic/test");
    expect(result).toEqual(homeConfig);
  });
});

describe("Middleware — passthrough", () => {
  test("an unmapped URL resolves to undefined", async () => {
    const result = await resolveMiddleware("/this-route-does-not-exist");
    expect(result).toBeUndefined();
  });

  test("'/' itself is not in routeMap and resolves to undefined", async () => {
    const result = await resolveMiddleware("/");
    expect(result).toBeUndefined();
  });

  test("real listed pages (e.g. '/docs') are not in routeMap and resolve to undefined", async () => {
    const result = await resolveMiddleware("/docs");
    expect(result).toBeUndefined();
  });
});
