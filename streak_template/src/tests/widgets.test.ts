/**
 * Widget utility / pure-logic tests.
 *
 * Streak widgets are React components rendered server-side — we don't
 * instantiate them here. Instead we test the pure helper logic that
 * widgets depend on (data defaults, formatting, validation).
 *
 * Run with:  bun test
 */

import { describe, test, expect } from "bun:test";
import PageHead from "../widgets/PageHead";
import HelloNav from "../widgets/HelloNav";
import HelloBanner from "../widgets/HelloBanner";
import HelloFeatures from "../widgets/HelloFeatures";
import HelloTerminal from "../widgets/HelloTerminal";
import HelloAnimated from "../widgets/HelloAnimated";
import HelloMessage from "../widgets/HelloMessage";
import HelloFooter from "../widgets/HelloFooter";

// ─── Helpers extracted for testability ────────────────────────────────────────

/** Resolve a widget prop that falls back to a default when undefined. */
const withDefault = <T>(value: T | undefined, fallback: T): T =>
  value ?? fallback;

/** Check if a string is a valid hex color. */
const isValidHexColor = (value: string): boolean =>
  /^#[0-9a-fA-F]{3,8}$/.test(value);

/** Build a canonical page title. */
const buildPageTitle = (title?: string, siteName = "Streak.js"): string =>
  title ? `${title} — ${siteName}` : siteName;

/** Check that all items in an array have a unique `id` property. */
const allIdsUnique = (items: Array<{ id: string }>): boolean =>
  new Set(items.map((i) => i.id)).size === items.length;

// ─── withDefault ─────────────────────────────────────────────────────────────
describe("withDefault", () => {
  test("returns value when defined", () => {
    expect(withDefault("hello", "fallback")).toBe("hello");
  });

  test("returns fallback when undefined", () => {
    expect(withDefault(undefined, "fallback")).toBe("fallback");
  });

  test("returns value when falsy non-undefined (0)", () => {
    expect(withDefault(0, 99)).toBe(0);
  });

  test("returns value when empty string", () => {
    // empty string is a valid value, not undefined
    expect(withDefault("", "fallback")).toBe("");
  });
});

// ─── isValidHexColor ─────────────────────────────────────────────────────────
describe("isValidHexColor", () => {
  test("accepts 6-char hex", () => {
    expect(isValidHexColor("#6366f1")).toBe(true);
  });

  test("accepts 3-char hex", () => {
    expect(isValidHexColor("#fff")).toBe(true);
  });

  test("accepts 8-char hex with alpha", () => {
    expect(isValidHexColor("#6366f188")).toBe(true);
  });

  test("rejects string without hash", () => {
    expect(isValidHexColor("6366f1")).toBe(false);
  });

  test("rejects arbitrary string", () => {
    expect(isValidHexColor("indigo")).toBe(false);
  });

  test("rejects empty string", () => {
    expect(isValidHexColor("")).toBe(false);
  });
});

// ─── buildPageTitle ──────────────────────────────────────────────────────────
describe("buildPageTitle", () => {
  test("appends site name when title present", () => {
    expect(buildPageTitle("Hello Streak")).toBe("Hello Streak — Streak.js");
  });

  test("returns site name only when title absent", () => {
    expect(buildPageTitle(undefined)).toBe("Streak.js");
  });

  test("uses custom site name", () => {
    expect(buildPageTitle("Home", "My App")).toBe("Home — My App");
  });
});

// ─── allIdsUnique ─────────────────────────────────────────────────────────────
describe("allIdsUnique", () => {
  test("returns true for unique ids", () => {
    expect(allIdsUnique([{ id: "a" }, { id: "b" }, { id: "c" }])).toBe(true);
  });

  test("returns false for duplicate ids", () => {
    expect(allIdsUnique([{ id: "a" }, { id: "a" }])).toBe(false);
  });

  test("returns true for empty array", () => {
    expect(allIdsUnique([])).toBe(true);
  });

  test("returns true for single item", () => {
    expect(allIdsUnique([{ id: "only" }])).toBe(true);
  });
});

// ─── Nav link validation ──────────────────────────────────────────────────────
describe("NavLink shape validation", () => {
  const isValidNavLink = (link: unknown): boolean => {
    if (typeof link !== "object" || link === null) return false;
    const l = link as Record<string, unknown>;
    return typeof l["label"] === "string" && typeof l["href"] === "string";
  };

  test("valid link passes", () => {
    expect(isValidNavLink({ label: "Home", href: "/" })).toBe(true);
  });

  test("missing label fails", () => {
    expect(isValidNavLink({ href: "/" })).toBe(false);
  });

  test("missing href fails", () => {
    expect(isValidNavLink({ label: "Home" })).toBe(false);
  });

  test("null fails", () => {
    expect(isValidNavLink(null)).toBe(false);
  });
});

// ─── Widget defaults / optional-chaining safety ───────────────────────────────
// CLAUDE.md: "data is always optional — always use optional chaining." These
// call every real widget with {} and { data: undefined } and assert none
// throw, which is exactly what breaks if a widget regresses to unguarded
// `props.data.field` access.
describe("Widget defaults — every widget tolerates missing data", () => {
  // Each widget has its own distinct `data` shape — `any` here is fine, the
  // test only cares that calling with {} / undefined data never throws.
  const widgets: Array<[string, (props: any) => unknown]> = [
    ["PageHead", PageHead],
    ["HelloNav", HelloNav],
    ["HelloBanner", HelloBanner],
    ["HelloFeatures", HelloFeatures],
    ["HelloTerminal", HelloTerminal],
    ["HelloAnimated", HelloAnimated],
    ["HelloMessage", HelloMessage],
    ["HelloFooter", HelloFooter],
  ];

  for (const [name, Widget] of widgets) {
    test(`${name} does not throw with {} props`, () => {
      expect(() => Widget({})).not.toThrow();
    });

    test(`${name} does not throw with { data: undefined }`, () => {
      expect(() => Widget({ data: undefined })).not.toThrow();
    });

    test(`${name} does not throw with { common: undefined }`, () => {
      expect(() => Widget({ common: undefined })).not.toThrow();
    });
  }
});
