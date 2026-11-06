// ─── Data Handler ─────────────────────────────────────────────────────────────
// Default-exported async function. Each key must match a widget "type" in the
// sitemap. Streak passes { data: value } to the matching widget as props.
// ─────────────────────────────────────────────────────────────────────────────

const stall = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

interface CommonData {
  branding?: { logoSrc?: string; logoAlt?: string; tagline?: string };
  nav?: { links?: { label: string; href: string }[] };
}

// Per-page identity content, keyed by streak.sitemap.json's metadata.pageName
// - the one piece of per-page context this handler receives but previously
// ignored (every page rendered identical content regardless of which page
// was building). Structural/demo content (HelloFeatures, HelloAnimated,
// HelloTerminal, HelloFooter) stays shared across pages - only the
// page-identity widgets vary.
const PAGE_CONTENT = {
  home: {
    pageTitle: "Hello Streak — Minimal Starter",
    pageDescription: "A minimal Hello World app built with Streak.js — the static site generator for React.",
    heading: "Hello, World.",
    subheading: "Build blazing-fast static sites with React components, zero runtime overhead.",
    cta: { label: "Get Started", href: "#features" },
    backgroundSeed: "streakjs-hero",
    accentColor: "#818cf8",
    quote: "Streak.js is the missing link between a React component tree and a genuinely static website.",
    bonusFact:
      "At build time Streak serialises your data handler output, renders every React widget to an HTML string, and stitches it all into a complete page — no hydration, no client bundle.",
  },
  docs: {
    pageTitle: "Hello Streak — Docs",
    pageDescription: "Preload, Script, Dynamic, loadPackage — every Streak.js primitive this app uses, explained.",
    heading: "Read the docs.",
    subheading: "Every widget on this site demonstrates a real Streak.js primitive — this page is the index.",
    cta: { label: "Jump to concepts", href: "#features" },
    backgroundSeed: "streakjs-hero-docs",
    accentColor: "#34d399",
    quote: "The best documentation is a real app you can read from top to bottom.",
    bonusFact:
      "Script's child function is serialised via .toString() and run as an IIFE - it can't close over widget-scope variables, so the options prop is the only bridge from server data into browser code.",
  },
  about: {
    pageTitle: "Hello Streak — About",
    pageDescription: "Why we built a zero-runtime static site generator.",
    heading: "About Streak.js.",
    subheading: "The missing link between a React component tree and a genuinely static website.",
    cta: { label: "See how it's built", href: "#features" },
    backgroundSeed: "streakjs-hero-about",
    accentColor: "#f472b6",
    quote: "We wanted React's ergonomics without shipping React to the browser.",
    bonusFact:
      "Every page in this app - home, docs, and this one - is pre-rendered once at build time. Nothing here re-renders in the browser.",
  },
} as const;

type PageName = keyof typeof PAGE_CONTENT;

const isPageName = (value: unknown): value is PageName =>
  typeof value === "string" && value in PAGE_CONTENT;

const getHomeData = async (metadata?: Record<string, unknown>, { common }: { common?: CommonData } = {}) => {
  await stall(500); // Simulate delay

  console.info("[HomeDataHandler] received metadata:", metadata);

  const page = PAGE_CONTENT[isPageName(metadata?.pageName) ? metadata.pageName : "home"];

  // Shared data available to every widget via props.common.
  // Branding and nav live here so widgets don't need widget-specific
  // keys just for site-wide values.
  const branding = {
    logoSrc: common?.branding?.logoSrc ?? "/images/streak-logo.svg",
    logoAlt: common?.branding?.logoAlt ?? "Streak.js",
    tagline: common?.branding?.tagline ?? "The React static site generator.",
  };
  const navLinks = common?.nav?.links ?? [
    { label: "Home",   href: "/" },
    { label: "Docs",   href: "/docs" },
    { label: "About",  href: "/about" },
    { label: "GitHub", href: "#" },
  ];

  return {
    status: 200,

    // common key — Streak passes this as props.common to every widget on the page.
    common: {
      branding,
      nav: { links: navLinks },
      year: new Date().getFullYear(),
    },

    PageHead: {
      title: page.pageTitle,
      description: page.pageDescription,
    },

    HelloNav: {
      // Only widget-specific data stays here; branding/nav come via props.common.
      streakCount: 128,
    },

    HelloBanner: {
      heading: page.heading,
      subheading: page.subheading,
      cta: page.cta,
      // Free image from Picsum Photos — https://picsum.photos (no attribution required)
      // Seeded URL so the image stays consistent across builds, distinct per page.
      backgroundImage: `https://picsum.photos/seed/${page.backgroundSeed}/1600/900`,
      accentColor: page.accentColor,
      animationMs: 700,
    },

    HelloFeatures: {
      heading: "What Streak.js gives you",
      features: [
        {
          id: "f1",
          title: "Static HTML at Build Time",
          description:
            "Every page is pre-rendered to plain HTML. No framework ships to the browser — just fast, indexable markup.",
          image: "https://picsum.photos/seed/streak-feat-1/600/400",
          imageAlt: "Server rack with code",
        },
        {
          id: "f2",
          title: "Widget-Driven Pages",
          description:
            "Pages are assembled from independent widgets. Each widget owns its markup, styles, and optional client script.",
          image: "https://picsum.photos/seed/streak-feat-2/600/400",
          imageAlt: "Modular component blocks",
        },
        {
          id: "f3",
          title: "Dynamic on Demand",
          description:
            "Heavy content is deferred with <Dynamic>. Load it on scroll, on click, or after a delay — your call.",
          image: "https://picsum.photos/seed/streak-feat-3/600/400",
          imageAlt: "Loading spinner to finished state",
        },
      ],
    },

    HelloTerminal: {
      promptLabel: "streak@forge",
      typeSpeedMs: 22,
      lines: [
        "$ cat streak.sitemap.json",
        "→ 3 pages · 8 widgets each",
        "$ streak-forge build",
        "✓ HomeDataHandler   → data",
        "✓ MainLayout        → shell",
        "✓ 8 widgets         → HTML strings",
        "✓ out/1.0.0/raw-content.json ready",
        "$ _",
      ],
    },

    HelloAnimated: {
      animationDuration: 0.65,
      // Words cycle in the morphing headline — swap out for any list
      words: ["Fast", "Beautiful", "Powerful", "Reliable"],
      cards: [
        {
          id: "c1",
          icon: "⚡",
          title: "Zero Runtime",
          description:
            "Pages are pre-rendered at build time. No framework ships to the browser — just lean, fast HTML.",
        },
        {
          id: "c2",
          icon: "🧩",
          title: "Widget System",
          description:
            "Assemble pages from independent React widgets. Each widget owns its markup, styles, and Scripts.",
        },
        {
          id: "c3",
          icon: "✨",
          title: "Script & Dynamic",
          description:
            "Drop in client interactivity with Script. Defer heavy content with Dynamic — loaded on demand.",
        },
      ],
    },

    HelloMessage: {
      quote: page.quote,
      author: "Streak.js Team",
      bonusFact: page.bonusFact,
    },

    HelloFooter: {
      // No widget-specific data — HelloFooter reads everything from props.common.
    },
  };
};

export default getHomeData;
