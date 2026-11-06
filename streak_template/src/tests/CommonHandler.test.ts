/**
 * Tests for CommonHandler — the reserved, once-per-build handler whose
 * output is threaded into every page handler as `{ common }`.
 *
 * Run with:  bun test
 */

import { describe, test, expect, beforeAll } from "bun:test";
import getCommonData from "../handlers/CommonHandler";

let data: Awaited<ReturnType<typeof getCommonData>>;

beforeAll(async () => {
  data = await getCommonData();
});

describe("CommonHandler — branding", () => {
  test("logoSrc is a non-empty string", () => {
    expect(data.branding.logoSrc).toBeTruthy();
    expect(typeof data.branding.logoSrc).toBe("string");
  });

  test("logoAlt is a non-empty string", () => {
    expect(data.branding.logoAlt).toBeTruthy();
  });

  test("tagline is a non-empty string", () => {
    expect(data.branding.tagline).toBeTruthy();
  });
});

describe("CommonHandler — nav", () => {
  test("has at least one link", () => {
    expect(data.nav.links.length).toBeGreaterThan(0);
  });

  test("every link has a label and href", () => {
    for (const link of data.nav.links) {
      expect(link.label).toBeTruthy();
      expect(link.href).toBeTruthy();
    }
  });
});
