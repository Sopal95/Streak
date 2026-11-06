import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import globals from "globals";

// ── Inline Streak-specific ESLint plugin ──────────────────────────────────────
// No extra npm package required — rules are defined directly in this config.
// Rules are scoped to the file paths where violations are meaningful.
const streakPlugin = {
  rules: {
    /**
     * streak/no-hooks-in-widgets
     *
     * Widgets are stateless React components rendered to HTML at build time.
     * React hooks (useState, useEffect, useRef, …) have no effect at runtime
     * because the browser receives static HTML — no React runtime is present.
     * Use the Script component for any client-side logic.
     */
    "no-hooks-in-widgets": {
      meta: {
        type: "problem",
        docs: {
          description:
            "Disallow React hooks in Streak widget files — widgets are stateless at runtime.",
        },
        messages: {
          noHooks:
            "React hook '{{name}}' is not allowed in widgets. " +
            "Widgets are stateless — use the Script component for client-side logic.",
        },
      },
      create(context) {
        const filename = context.filename ?? context.getFilename?.() ?? "";
        if (!filename.includes("/widgets/")) return {};

        return {
          CallExpression(node) {
            const callee = node.callee;
            if (
              callee.type === "Identifier" &&
              /^use[A-Z]/.test(callee.name)
            ) {
              context.report({
                node,
                messageId: "noHooks",
                data: { name: callee.name },
              });
            }
          },
        };
      },
    },

    /**
     * streak/require-default-export
     *
     * Streak imports widgets, layouts, and handlers by their default export.
     * A missing default export causes a silent build failure where the component
     * renders as empty.
     */
    "require-default-export": {
      meta: {
        type: "problem",
        docs: {
          description:
            "Require a default export in Streak widget, layout, and handler files.",
        },
        messages: {
          missing:
            "Streak {{fileType}} must have a default export. " +
            "Streak imports this file by its default export.",
        },
      },
      create(context) {
        const filename = context.filename ?? context.getFilename?.() ?? "";
        let fileType = null;
        if (filename.includes("/widgets/"))  fileType = "widget";
        else if (filename.includes("/layouts/"))  fileType = "layout";
        else if (filename.includes("/handlers/")) fileType = "handler";
        if (!fileType) return {};

        let hasDefaultExport = false;
        return {
          ExportDefaultDeclaration() {
            hasDefaultExport = true;
          },
          "Program:exit"(node) {
            if (!hasDefaultExport) {
              context.report({
                node,
                messageId: "missing",
                data: { fileType },
              });
            }
          },
        };
      },
    },

    /**
     * streak/no-direct-data-access
     *
     * Widget data (`props.data`) may be undefined if the handler does not return
     * that widget's key — for example when a handler is updated but the widget
     * list is not. Always use optional chaining so the widget degrades gracefully.
     *
     * Wrong:   props.data.heading
     * Correct: props?.data?.heading ?? "Default"
     */
    "no-direct-data-access": {
      meta: {
        type: "suggestion",
        docs: {
          description:
            "Require optional chaining when accessing props.data in Streak widgets.",
        },
        messages: {
          useOptional:
            "Use optional chaining: 'props?.data?.{{prop}}' instead of 'props.data.{{prop}}'. " +
            "Widget data may be undefined if the handler omits this widget's key.",
        },
      },
      create(context) {
        const filename = context.filename ?? context.getFilename?.() ?? "";
        if (!filename.includes("/widgets/")) return {};

        return {
          MemberExpression(node) {
            // Detect: props.data.something  (no optional chaining on .data or .something)
            if (
              node.object.type === "MemberExpression" &&
              !node.object.optional &&
              node.object.object.type === "Identifier" &&
              node.object.object.name === "props" &&
              node.object.property.type === "Identifier" &&
              node.object.property.name === "data" &&
              !node.optional
            ) {
              const prop =
                node.property.type === "Identifier" ? node.property.name : "?";
              context.report({
                node,
                messageId: "useOptional",
                data: { prop },
              });
            }
          },
        };
      },
    },

    /**
     * streak/script-options-bridge
     *
     * The Script component's child function is serialized via .toString() and
     * executed as an IIFE in the browser. Variables from the widget's React
     * scope are NOT available inside the function after serialization.
     *
     * This rule warns when a Script child function's first parameter is NOT
     * named `gDom` — which is the conventional signal that the author knows
     * about the serialization constraint. It also warns when neither `gDom`
     * nor `options` parameters are typed as `any` via a comment or type.
     *
     * Heuristic: if <Script> JSX has children that are an arrow function or
     * function expression whose params don't include `gDom`, warn.
     */
    "script-options-bridge": {
      meta: {
        type: "suggestion",
        docs: {
          description:
            "Enforce the (gDom, options) signature in Script component children.",
        },
        messages: {
          missingGDom:
            "Script children should use the signature '(gDom: any, options: any) => { ... }'. " +
            "The first parameter (gDom) is window extended with Streak helpers.",
        },
      },
      create(context) {
        const filename = context.filename ?? context.getFilename?.() ?? "";
        if (!filename.includes("/widgets/")) return {};

        return {
          JSXElement(node) {
            const opening = node.openingElement;
            // Only check <Script ...> elements
            if (
              opening.name.type !== "JSXIdentifier" ||
              opening.name.name !== "Script"
            ) return;

            // Find the JSXExpressionContainer child that holds the function
            for (const child of node.children) {
              if (child.type !== "JSXExpressionContainer") continue;
              const expr = child.expression;
              if (
                expr.type !== "ArrowFunctionExpression" &&
                expr.type !== "FunctionExpression"
              ) continue;

              const params = expr.params;
              if (params.length === 0) return; // no params — not our concern
              const first = params[0];
              const firstName =
                first.type === "Identifier"
                  ? first.name
                  : first.type === "TSAsExpression" ||
                    first.type === "AssignmentPattern"
                  ? null
                  : null;
              if (firstName && firstName !== "gDom") {
                context.report({
                  node: first,
                  messageId: "missingGDom",
                });
              }
            }
          },
        };
      },
    },
  },
};

/** @type {import("eslint").Linter.Config[]} */
export default [
  // ── Ignore patterns ──────────────────────────────────────────────────────────
  {
    ignores: [
      "out/**",
      "node_modules/**",
      "public/styles/**",
      "public/assets/**",
    ],
  },

  // ── TypeScript + TSX source files ────────────────────────────────────────────
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      streak: streakPlugin,
    },
    rules: {
      // ── TypeScript ──────────────────────────────────────────────────────────
      // Warn on `any` — intentionally allowed in Script children (gDom, options)
      // but discourage everywhere else.
      "@typescript-eslint/no-explicit-any": "warn",

      // Unused variables are errors; prefix with _ to intentionally ignore.
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],

      // Prefer type-only imports where the value is only used as a type.
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports" },
      ],

      // ── General JS quality ──────────────────────────────────────────────────
      "no-var": "error",
      "prefer-const": "error",
      "no-console": ["warn", { allow: ["info", "error", "warn"] }],
      eqeqeq: ["error", "always"],
      "no-unused-expressions": "error",

      // ── Streak-specific rules (inline plugin) ───────────────────────────────
      // Widgets must not use React hooks — they are stateless at runtime.
      "streak/no-hooks-in-widgets": "error",

      // Widgets, layouts, and handlers must have a default export.
      "streak/require-default-export": "error",

      // Always use optional chaining on props.data in widgets.
      "streak/no-direct-data-access": "warn",

      // Script children should follow the (gDom, options) signature convention.
      "streak/script-options-bridge": "warn",
    },
  },

  // ── Test files — relaxed rules ────────────────────────────────────────────────
  {
    files: ["src/tests/**/*.{ts,tsx}", "**/*.test.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "no-console": "off",
      "streak/require-default-export": "off",
    },
  },

  // ── Validation scripts — relaxed rules ────────────────────────────────────────
  {
    files: ["src/scripts/**/*.{ts,tsx}"],
    rules: {
      "no-console": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "streak/require-default-export": "off",
    },
  },
];
