import { WidgetPlaceholder } from "streak-forge/components";

// ─── WidgetPlaceholder ────────────────────────────────────────────────────────
// Marks a slot in the layout where a widget is injected at build time.
// id   must match the "id" field in streak.sitemap.json widgets[].
// type must match the "type" field AND the filename in src/widgets/.
// ─────────────────────────────────────────────────────────────────────────────

const MainLayout = () => {
  console.info("Rendering Main Layout");
  return (
    <html dir="ltr" lang="en">
      <head>
        <WidgetPlaceholder id="PageHead" type="PageHead" />
      </head>
      <body className="bg-white text-gray-900 antialiased">
        {/*
          Global grain overlay - a single inline SVG feTurbulence data-URI,
          fixed + pointer-events:none so it never intercepts clicks.
          mix-blend-mode: overlay makes it self-adjust across both the dark
          hero/message sections and the light features section, so it never
          needs per-section scoping.
        */}
        <div
          aria-hidden="true"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9998,
            pointerEvents: "none",
            opacity: 0.03,
            mixBlendMode: "overlay",
            backgroundImage:
              "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          }}
        />

        <WidgetPlaceholder id="HelloNav"      type="HelloNav"      />
        <WidgetPlaceholder id="HelloBanner"   type="HelloBanner"   />
        <WidgetPlaceholder id="HelloFeatures"  type="HelloFeatures"  />
        <WidgetPlaceholder id="HelloTerminal"  type="HelloTerminal"  />
        <WidgetPlaceholder id="HelloAnimated"  type="HelloAnimated"  />
        <WidgetPlaceholder id="HelloMessage"   type="HelloMessage"   />
        <WidgetPlaceholder id="HelloFooter"   type="HelloFooter"   />
      </body>
    </html>
  );
};

export default MainLayout;
