/**
 * Tests for streak-forge's own primitives (Script, WidgetPlaceholder,
 * Dynamic, Preload) and — the main event — the Script "options" bridge:
 * the *only* way a server-derived value survives into browser-side code
 * (Script's child function is serialized via `.toString()`, so it cannot
 * close over widget-scope variables; see CLAUDE.md's Script section).
 *
 * Widgets are plain functions that return VNode objects (`{ type, props }`,
 * see streak-forge's src/jsx/element.ts) synchronously — no rendering
 * pipeline needed to inspect what a widget actually passed into `options`.
 *
 * Run with:  bun test
 */

import { describe, test, expect } from "bun:test";
import { Script, WidgetPlaceholder, Dynamic, Preload } from "streak-forge/components";
import HelloBanner from "../widgets/HelloBanner";
import HelloAnimated from "../widgets/HelloAnimated";
import HelloNav from "../widgets/HelloNav";
import HelloTerminal from "../widgets/HelloTerminal";

type VNode = { type: unknown; props: Record<string, any> };

/** Structural walk over a VNode tree — never invokes function components. */
const collectByType = (node: unknown, targetType: unknown, acc: VNode[] = []): VNode[] => {
  if (node === null || node === undefined || typeof node !== "object") return acc;
  if (Array.isArray(node)) {
    for (const child of node) collectByType(child, targetType, acc);
    return acc;
  }
  const vnode = node as VNode;
  if (vnode.type === targetType) acc.push(vnode);
  if (vnode.props && "children" in vnode.props) {
    collectByType(vnode.props.children, targetType, acc);
  }
  return acc;
};

// ─── Script — the options -> data-sf-opts bridge ──────────────────────────────
describe("Script — options bridge (framework-level)", () => {
  test("data-sf-opts equals JSON.stringify(options)", () => {
    const options = { color: "#ffffff", count: 3 };
    const vnode = Script({ id: "x", options, children: () => {} }) as VNode;
    expect(vnode.props["data-sf-opts"]).toBe(JSON.stringify(options));
  });

  test("defaults to '{}' when options is omitted", () => {
    const vnode = Script({ id: "x", children: () => {} }) as VNode;
    expect(vnode.props["data-sf-opts"]).toBe("{}");
  });

  test("throws when options isn't JSON-serializable", () => {
    // A plain function *value* inside options is silently dropped by
    // JSON.stringify (only a *top-level* non-serializable value, or an
    // object whose toJSON() returns undefined, makes JSON.stringify itself
    // return undefined) — so toJSON is the accurate way to trigger this.
    const options = { toJSON: () => undefined };
    expect(() => Script({ id: "x", options, children: () => {} })).toThrow(/JSON-serializable/);
  });
});

// ─── Per-widget bridge tests ───────────────────────────────────────────────────
// Each of these proves the value flows from widget `data` -> Script `options`
// (not a stale default / closured variable) by round-tripping through the
// same JSON.stringify the real build pipeline uses.

describe("HelloBanner — Script options bridge (accentColor / animationMs)", () => {
  test("options reflect the widget's actual data", () => {
    const accentColor = "#00ffaa";
    const animationMs = 4321;
    const vnode = HelloBanner({ data: { accentColor, animationMs } });
    const bannerScript = collectByType(vnode, Script).find((s) => s.props.id === "hello-banner-script");

    expect(bannerScript).toBeDefined();
    expect(bannerScript!.props.options).toEqual({ accentColor, animationMs });

    const rendered = Script(bannerScript!.props as Parameters<typeof Script>[0]) as VNode;
    expect(rendered.props["data-sf-opts"]).toBe(JSON.stringify({ accentColor, animationMs }));
  });
});

describe("HelloAnimated — Script options bridge (animationDuration / words)", () => {
  test("options reflect the widget's actual data", () => {
    const animationDuration = 1.23;
    const words = ["Alpha", "Beta"];
    const vnode = HelloAnimated({ data: { animationDuration, words, cards: [] } });
    const animatedScript = collectByType(vnode, Script).find((s) => s.props.id === "hello-animated-script");

    expect(animatedScript).toBeDefined();
    expect(animatedScript!.props.options).toEqual({ animationDuration, words });

    const rendered = Script(animatedScript!.props as Parameters<typeof Script>[0]) as VNode;
    expect(rendered.props["data-sf-opts"]).toBe(JSON.stringify({ animationDuration, words }));
  });
});

describe("HelloNav — Script options bridge (streakCount)", () => {
  test("options reflect the widget's actual data", () => {
    const streakCount = 42;
    const vnode = HelloNav({ data: { streakCount } });
    const navScript = collectByType(vnode, Script).find((s) => s.props.id === "hello-nav-script");

    expect(navScript).toBeDefined();
    expect(navScript!.props.options).toEqual({ streakCount });

    const rendered = Script(navScript!.props as Parameters<typeof Script>[0]) as VNode;
    expect(rendered.props["data-sf-opts"]).toBe(JSON.stringify({ streakCount }));
  });
});

describe("HelloTerminal — Script options bridge (lines / typeSpeedMs)", () => {
  test("options reflect the widget's actual data", () => {
    const lines = ["$ one", "$ two"];
    const typeSpeedMs = 10;
    const vnode = HelloTerminal({ data: { lines, typeSpeedMs } });
    const termScript = collectByType(vnode, Script).find((s) => s.props.id === "hello-terminal-script");

    expect(termScript).toBeDefined();
    expect(termScript!.props.options).toEqual({ lines, typeSpeedMs });

    const rendered = Script(termScript!.props as Parameters<typeof Script>[0]) as VNode;
    expect(rendered.props["data-sf-opts"]).toBe(JSON.stringify({ lines, typeSpeedMs }));
  });
});

// ─── Other streak-forge primitives ─────────────────────────────────────────────
describe("WidgetPlaceholder", () => {
  test("throws when id is missing", () => {
    expect(() => WidgetPlaceholder({ id: "", type: "Foo" })).toThrow();
  });

  test("throws when type is missing", () => {
    expect(() => WidgetPlaceholder({ id: "Foo" } as never)).toThrow();
  });

  test("returns a marker vnode carrying id/type when valid", () => {
    const vnode = WidgetPlaceholder({ id: "Foo", type: "Foo" }) as VNode;
    expect(vnode.props.id).toBe("Foo");
    expect(vnode.props.type).toBe("Foo");
  });
});

describe("Dynamic", () => {
  test("throws when id is missing", () => {
    expect(() => Dynamic({ id: "" })).toThrow();
  });

  test("wraps children under the given id", () => {
    const vnode = Dynamic({ id: "panel", children: "hello" }) as VNode;
    expect(vnode.props.id).toBe("panel");
    expect(vnode.props.children).toBe("hello");
  });
});

describe("Preload", () => {
  test("passes href/as/media through unchanged", () => {
    const vnode = Preload({ href: "/img.png", as: "image", media: "(min-width: 768px)" }) as VNode;
    expect(vnode.props.href).toBe("/img.png");
    expect(vnode.props.as).toBe("image");
    expect(vnode.props.media).toBe("(min-width: 768px)");
  });
});
