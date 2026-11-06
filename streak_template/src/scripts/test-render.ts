#!/usr/bin/env bun
/**
 * test-render
 *
 * Local harness for the streak-forge/core `render()` contract - reads every
 * page out of streak.sitemap.json and calls render() the same way the real
 * external consumer does (explicit handlerOptions.srcDir, onProgress,
 * isBuild), so you can sanity-check the render flow without needing that
 * consumer's DB/blob-storage machinery. Mirrors:
 *   streakjs/apps/streak-forge-build/stage1/src/run-prebuild-v3.ts
 *
 * Usage:
 *   bun run test-render
 *   (or: bun run src/scripts/test-render.ts)
 */

import { existsSync, readFileSync, mkdirSync, writeFileSync } from "fs";
import { resolve, join, dirname } from "path";
import { render, type RenderConfig } from "streak-forge/core";

const ROOT = resolve(import.meta.dir, "../../");

const sitemapPath = join(ROOT, "streak.sitemap.json");
if (!existsSync(sitemapPath)) {
  console.error("✖  streak.sitemap.json not found at project root");
  process.exit(1);
}

interface SitemapEntry {
  url: string;
  renderConfig: RenderConfig;
}

const sitemap = JSON.parse(readFileSync(sitemapPath, "utf-8")) as SitemapEntry[];

const srcDir = {
  root: join(ROOT, "src"),
  handlerDir: join(ROOT, "src", "handlers"),
  widgetsDir: join(ROOT, "src", "widgets"),
  layoutsDir: join(ROOT, "src", "layouts"),
  publicDir: join(ROOT, "public"),
};

let failures = 0;
let total = 0;
const scriptStart = Date.now();

// label: what to print. renderConfig: the base config (irrelevant if
// Middleware.ts matches middlewareUrl and overrides it). outputUrl: where to
// save renderedPage[] under out/, same layout `build` uses. middlewareUrl:
// passed through to render() only when set - this is the one place in this
// script that deviates from mirroring the external consumer's contract,
// specifically to exercise Middleware.ts's route-resolution path (the
// external consumer never passes url, so it never triggers Middleware).
const renderAndReport = async (label: string, renderConfig: RenderConfig, outputUrl: string, middlewareUrl?: string) => {
  total += 1;
  console.log(`\n=== rendering "${label}" ===`);

  const steps: { st: string; ct: number; tc: number }[] = [];

  try {
    const response = await render(renderConfig, {
      isBuild: true,
      url: middlewareUrl,
      onProgress: (metadata, metaInfo) => {
        steps.push({ st: metaInfo.uuid, ct: metadata.currentTime, tc: metadata.timeTook });
        console.log(`  onProgress: ${metaInfo.uuid} (+${metadata.timeTook}ms)`);
      },
      handlerOptions: { srcDir },
    });

    const [firstPage] = response.renderedPage;
    const rawContent = JSON.parse(firstPage!.content) as Record<string, unknown>;

    console.log(`  renderedPage[0]: id=${firstPage!.id} path=${firstPage!.path} type=${firstPage!.type} bytes=${firstPage!.content.length}`);
    console.log(`  rawContent keys: ${Object.keys(rawContent).join(", ")}`);
    console.log(`  progress: startTime=${response.progress.startTime} totalTime=${response.progress.totalTime}ms steps=${steps.length}`);
    console.log(`  "${label}" took ${response.progress.totalTime}ms to render`);

    for (const file of response.renderedPage) {
      const outPath = join(ROOT, "out", outputUrl.replace(/^\//, ""), file.path);
      mkdirSync(dirname(outPath), { recursive: true });
      writeFileSync(outPath, file.content, "utf-8");
      console.log(`  wrote ${outPath}`);
    }
  } catch (err) {
    failures += 1;
    console.error(`  ✖ render failed for "${label}":`, err);
  }
};

for (const { url, renderConfig } of sitemap) {
  await renderAndReport(`${url} (renderId: ${renderConfig.renderId})`, renderConfig, url);
}

// Not a static sitemap entry at all - only resolvable via Middleware.ts's
// routeMap ("/dynamic/test" -> "/"), so the base renderConfig passed here is
// arbitrary (reusing "/"'s) and gets overridden entirely if Middleware.ts is
// present and matches.
const middlewareTestUrl = "/dynamic/test";
const homeConfig = sitemap.find((entry) => entry.url === "/")?.renderConfig;
if (homeConfig) {
  await renderAndReport(`${middlewareTestUrl} (via Middleware, not in streak.sitemap.json)`, homeConfig, middlewareTestUrl, middlewareTestUrl);
}

console.log(`\n${total - failures}/${total} page(s) rendered successfully. Total time: ${Date.now() - scriptStart}ms.`);
if (failures > 0) process.exit(1);
