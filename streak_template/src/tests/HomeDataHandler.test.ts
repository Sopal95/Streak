/**
 * Tests for HomeDataHandler
 *
 * Run with:  bun test
 * Watch:     bun test --watch
 *
 * Bun ships a built-in Jest-compatible test runner — no extra packages needed.
 * Import from "bun:test" instead of "jest".
 */

import { describe, test, expect, beforeAll } from "bun:test";
import getHomeData from "../handlers/HomeDataHandler";

// ─── Shared fixture ───────────────────────────────────────────────────────────
// Call the handler once and reuse across all assertions.
let data: Awaited<ReturnType<typeof getHomeData>>;

beforeAll(async () => {
  data = await getHomeData();
});

// ─── Top-level shape ──────────────────────────────────────────────────────────
describe("HomeDataHandler — top-level shape", () => {
  test("returns status 200", () => {
    expect(data.status).toBe(200);
  });

  test("contains all required widget keys", () => {
    const requiredKeys = [
      "common",
      "PageHead",
      "HelloNav",
      "HelloBanner",
      "HelloFeatures",
      "HelloMessage",
      "HelloFooter",
    ];
    for (const key of requiredKeys) {
      expect(data).toHaveProperty(key);
    }
  });
});

// ─── PageHead ─────────────────────────────────────────────────────────────────
describe("HomeDataHandler — PageHead", () => {
  test("has a non-empty title", () => {
    expect(data.PageHead.title).toBeTruthy();
    expect(typeof data.PageHead.title).toBe("string");
  });

  test("has a non-empty description", () => {
    expect(data.PageHead.description).toBeTruthy();
  });
});

// ─── HelloNav ─────────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloNav", () => {
  test("streakCount is a positive integer", () => {
    expect(data.HelloNav.streakCount).toBeGreaterThan(0);
    expect(Number.isInteger(data.HelloNav.streakCount)).toBe(true);
  });

  test("nav links live in common (not HelloNav widget data)", () => {
    expect((data.HelloNav as Record<string, unknown>).links).toBeUndefined();
    expect(Array.isArray(data.common.nav.links)).toBe(true);
    expect(data.common.nav.links.length).toBeGreaterThan(0);
  });
});

// ─── HelloBanner ─────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloBanner", () => {
  test("heading is a non-empty string", () => {
    expect(data.HelloBanner.heading).toBeTruthy();
  });

  test("accentColor is a valid hex string", () => {
    expect(data.HelloBanner.accentColor).toMatch(/^#[0-9a-fA-F]{3,8}$/);
  });

  test("animationMs is a positive number", () => {
    expect(data.HelloBanner.animationMs).toBeGreaterThan(0);
  });

  test("cta has label and href", () => {
    expect(data.HelloBanner.cta?.label).toBeTruthy();
    expect(data.HelloBanner.cta?.href).toBeTruthy();
  });
});

// ─── HelloFeatures ────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloFeatures", () => {
  test("has at least one feature", () => {
    expect(data.HelloFeatures.features.length).toBeGreaterThan(0);
  });

  test("every feature has id, title, description, image, imageAlt", () => {
    for (const feature of data.HelloFeatures.features) {
      expect(feature.id).toBeTruthy();
      expect(feature.title).toBeTruthy();
      expect(feature.description).toBeTruthy();
      expect(feature.image).toBeTruthy();
      expect(feature.imageAlt).toBeTruthy();
    }
  });

  test("feature ids are unique", () => {
    const ids = data.HelloFeatures.features.map((f) => f.id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });
});

// ─── HelloAnimated ───────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloAnimated", () => {
  test("animationDuration is between 0 and 5 seconds", () => {
    expect(data.HelloAnimated.animationDuration).toBeGreaterThan(0);
    expect(data.HelloAnimated.animationDuration).toBeLessThanOrEqual(5);
  });

  test("has at least one word for the morphing headline", () => {
    expect(data.HelloAnimated.words.length).toBeGreaterThan(0);
    for (const word of data.HelloAnimated.words) {
      expect(typeof word).toBe("string");
      expect(word.length).toBeGreaterThan(0);
    }
  });

  test("has at least one card", () => {
    expect(data.HelloAnimated.cards.length).toBeGreaterThan(0);
  });

  test("every card has id, icon, title, and description", () => {
    for (const card of data.HelloAnimated.cards) {
      expect(card.id).toBeTruthy();
      expect(card.icon).toBeTruthy();
      expect(card.title).toBeTruthy();
      expect(card.description).toBeTruthy();
    }
  });

  test("card ids are unique", () => {
    const ids = data.HelloAnimated.cards.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

// ─── HelloTerminal ────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloTerminal", () => {
  test("has a promptLabel", () => {
    expect(data.HelloTerminal.promptLabel).toBeTruthy();
  });

  test("has at least one line", () => {
    expect(data.HelloTerminal.lines.length).toBeGreaterThan(0);
    for (const line of data.HelloTerminal.lines) {
      expect(typeof line).toBe("string");
    }
  });

  test("typeSpeedMs is a positive number", () => {
    expect(data.HelloTerminal.typeSpeedMs).toBeGreaterThan(0);
  });
});

// ─── HelloMessage ─────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloMessage", () => {
  test("has a quote string", () => {
    expect(data.HelloMessage.quote).toBeTruthy();
  });

  test("has an author string", () => {
    expect(data.HelloMessage.author).toBeTruthy();
  });

  test("has a bonusFact string", () => {
    expect(data.HelloMessage.bonusFact).toBeTruthy();
  });
});

// ─── HelloFooter ─────────────────────────────────────────────────────────────
describe("HomeDataHandler — HelloFooter", () => {
  test("branding and year live in common (not HelloFooter widget data)", () => {
    expect((data.HelloFooter as Record<string, unknown>).year).toBeUndefined();
    expect((data.HelloFooter as Record<string, unknown>).logoSrc).toBeUndefined();
    expect(data.common.year).toBe(new Date().getFullYear());
    expect(typeof data.common.branding.logoSrc).toBe("string");
  });
});

// ─── Per-page content (metadata.pageName) ──────────────────────────────────────
// The handler is shared across all 3 sitemap pages ("/", "/docs", "/about")
// - this proves metadata.pageName actually drives distinct content instead
// of every page silently rendering the same thing.
describe("HomeDataHandler — per-page content", () => {
  test("home (no metadata) uses the default 'home' content", async () => {
    const home = await getHomeData();
    expect(home.PageHead.title).toBe("Hello Streak — Minimal Starter");
    expect(home.HelloBanner.heading).toBe("Hello, World.");
  });

  test("docs and about pages render distinct heading/title/quote from home", async () => {
    const home = await getHomeData({ pageName: "home" });
    const docs = await getHomeData({ pageName: "docs" });
    const about = await getHomeData({ pageName: "about" });

    const pages = [home, docs, about];
    for (const page of pages) {
      expect(page.PageHead.title).toBeTruthy();
      expect(page.HelloBanner.heading).toBeTruthy();
      expect(page.HelloMessage.quote).toBeTruthy();
    }

    const titles = pages.map((p) => p.PageHead.title);
    const headings = pages.map((p) => p.HelloBanner.heading);
    const quotes = pages.map((p) => p.HelloMessage.quote);

    expect(new Set(titles).size).toBe(pages.length);
    expect(new Set(headings).size).toBe(pages.length);
    expect(new Set(quotes).size).toBe(pages.length);
  });

  test("an unrecognized pageName falls back to home content", async () => {
    const fallback = await getHomeData({ pageName: "does-not-exist" });
    const home = await getHomeData({ pageName: "home" });
    expect(fallback.PageHead.title).toBe(home.PageHead.title);
    expect(fallback.HelloBanner.heading).toBe(home.HelloBanner.heading);
  });

  test("shared/structural widgets (HelloFeatures, HelloTerminal) stay the same across pages", async () => {
    const home = await getHomeData({ pageName: "home" });
    const docs = await getHomeData({ pageName: "docs" });
    expect(docs.HelloFeatures.heading).toBe(home.HelloFeatures.heading);
    expect(docs.HelloTerminal.lines).toEqual(home.HelloTerminal.lines);
  });
});
