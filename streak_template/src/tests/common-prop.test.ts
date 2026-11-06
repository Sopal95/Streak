/**
 * Tests for the handler `common` key contract.
 *
 * HomeDataHandler returns a `common` key — Streak passes this as props.common
 * to every widget on the page, giving all widgets access to shared data
 * (branding, nav, year) without repeating it in each widget's own key.
 *
 * Run with:  bun test
 */

import { describe, test, expect, beforeAll } from "bun:test";
import getHomeData from "../handlers/HomeDataHandler";
import HelloFooter from "../widgets/HelloFooter";
import HelloNav from "../widgets/HelloNav";

let data: Awaited<ReturnType<typeof getHomeData>>;

beforeAll(async () => {
  data = await getHomeData();
});

// ─── Handler returns common key ───────────────────────────────────────────────

describe("HomeDataHandler — common key shape", () => {
  test("returns a common key", () => {
    expect(data).toHaveProperty("common");
  });

  test("common.branding has logoSrc, logoAlt, tagline", () => {
    expect(typeof data.common.branding.logoSrc).toBe("string");
    expect(data.common.branding.logoSrc.length).toBeGreaterThan(0);
    expect(typeof data.common.branding.logoAlt).toBe("string");
    expect(data.common.branding.logoAlt.length).toBeGreaterThan(0);
    expect(typeof data.common.branding.tagline).toBe("string");
    expect(data.common.branding.tagline.length).toBeGreaterThan(0);
  });

  test("common.nav.links has at least one entry", () => {
    expect(Array.isArray(data.common.nav.links)).toBe(true);
    expect(data.common.nav.links.length).toBeGreaterThan(0);
  });

  test("every common nav link has label and href", () => {
    for (const link of data.common.nav.links) {
      expect(typeof link.label).toBe("string");
      expect(typeof link.href).toBe("string");
    }
  });

  test("common.year is the current calendar year", () => {
    expect(data.common.year).toBe(new Date().getFullYear());
  });
});

// ─── HelloNav reads from props.common ────────────────────────────────────────

describe("HelloNav — reads branding and nav from props.common", () => {
  const common = {
    branding: { logoSrc: "/logo.svg", logoAlt: "TestApp" },
    nav: { links: [{ label: "Home", href: "/" }, { label: "Docs", href: "/docs" }] },
  };

  test("does not throw when only common is provided (no data)", () => {
    expect(() => HelloNav({ common })).not.toThrow();
  });

  test("does not throw with no props at all", () => {
    expect(() => HelloNav({})).not.toThrow();
  });

  test("does not throw when common is undefined", () => {
    expect(() => HelloNav({ common: undefined })).not.toThrow();
  });
});

// ─── HelloFooter reads from props.common ─────────────────────────────────────

describe("HelloFooter — reads branding and year from props.common", () => {
  const common = {
    branding: { logoSrc: "/logo.svg", logoAlt: "TestApp", tagline: "Fast sites." },
    year: 2026,
  };

  test("does not throw when only common is provided (no data)", () => {
    expect(() => HelloFooter({ common })).not.toThrow();
  });

  test("does not throw with no props at all", () => {
    expect(() => HelloFooter({})).not.toThrow();
  });

  test("does not throw when common is undefined", () => {
    expect(() => HelloFooter({ common: undefined })).not.toThrow();
  });
});

// ─── common is stable across page variants ───────────────────────────────────

describe("HomeDataHandler — common is consistent across page variants", () => {
  test("all page variants return the same branding", async () => {
    const home  = await getHomeData({ pageName: "home" });
    const docs  = await getHomeData({ pageName: "docs" });
    const about = await getHomeData({ pageName: "about" });

    expect(home.common.branding).toEqual(docs.common.branding);
    expect(home.common.branding).toEqual(about.common.branding);
  });

  test("all page variants return the same nav links", async () => {
    const home  = await getHomeData({ pageName: "home" });
    const docs  = await getHomeData({ pageName: "docs" });

    expect(home.common.nav.links).toEqual(docs.common.nav.links);
  });
});
