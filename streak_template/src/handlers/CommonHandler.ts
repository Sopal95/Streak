// ─── Common Handler ────────────────────────────────────────────────────────
// Reserved, auto-discovered filename (CommonHandler.ts). Optional - if this
// file doesn't exist, nothing changes for other handlers.
//
// Called once for the whole `build`/`dev-build` run (shared across every
// page), but fresh on every single `dev` render (never cached) - so put API
// calls here that are the same across pages (site branding, nav, etc.) to
// avoid every page's own handler repeating them.
//
// Its return value is passed into every other handler as the `common`
// argument: `export default async ({ common }) => {...}`.
// ─────────────────────────────────────────────────────────────────────────────

const getCommonData = async () => {
  console.info("[CommonHandler] fetching shared site data...");

  return {
    branding: {
      logoSrc: "/images/streak-logo.svg",
      logoAlt: "Streak.js",
      tagline: "The React static site generator.",
    },
    nav: {
      links: [
        { label: "Home",   href: "/" },
        { label: "Docs",   href: "/docs" },
        { label: "About",  href: "/about" },
        { label: "GitHub", href: "#" },
      ],
    },
  };
};

export default getCommonData;
