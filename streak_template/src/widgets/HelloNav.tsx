import { Dynamic, Script, type GDom } from "streak-forge/components";

type NavLink = { label: string; href: string };

type HelloNavProps = {
  data?: {
    streakCount?: number;
  };
  common?: {
    branding?: { logoSrc?: string; logoAlt?: string };
    nav?: { links?: NavLink[] };
  };
};

const HelloNav = (props: HelloNavProps) => {
  const logoSrc = props?.common?.branding?.logoSrc ?? "/images/streak-logo.svg";
  const logoAlt = props?.common?.branding?.logoAlt ?? "Streak.js";
  const links = props?.common?.nav?.links ?? [];
  const streakCount = props?.data?.streakCount ?? 0;

  return (
    <header
      id="site-nav"
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-3 group">
          <img
            src={logoSrc}
            alt={logoAlt}
            width={32}
            height={32}
            className="w-8 h-8"
          />
          <span className="text-white font-semibold text-lg tracking-tight group-hover:opacity-80 transition-opacity">
            Streak<span className="text-indigo-400">.js</span>
          </span>

          {/* Streak-count badge — counts up from 0 on mount via Script */}
          {streakCount > 0 && (
            <span
              id="streak-badge"
              className="hidden sm:inline-flex items-center gap-1 ml-1 px-2.5 py-1 rounded-full text-xs font-semibold border border-orange-500/30 text-orange-300"
              style={{ background: "rgba(249,115,22,0.1)" }}
              title={`${streakCount} day streak`}
            >
              <span aria-hidden="true">🔥</span>
              <span id="streak-count">0</span>
            </span>
          )}
        </a>

        {/* Desktop links */}
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-gray-300 hover:text-white transition-colors font-medium"
            >
              {link.label}
            </a>
          ))}
          <a
            href="#"
            className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors font-medium"
          >
            Star on GitHub ★
          </a>
        </nav>

        {/* Mobile hamburger — hidden on md+ */}
        <button
          id="mobile-menu-btn"
          className="md:hidden flex flex-col justify-center gap-1.5 w-10 h-10 text-gray-300 hover:text-white transition-colors"
          aria-label="Toggle menu"
          aria-expanded="false"
        >
          <span id="ham-top"    className="block w-6 h-0.5 bg-current transition-all duration-300 origin-center"></span>
          <span id="ham-mid"    className="block w-6 h-0.5 bg-current transition-all duration-300"></span>
          <span id="ham-bottom" className="block w-6 h-0.5 bg-current transition-all duration-300 origin-center"></span>
        </button>
      </div>

      {/* Mobile menu — absent from initial HTML, injected on first hamburger click */}
      <Dynamic id="hello-mobile-menu">
        <nav
          id="mobile-menu-content"
          className="md:hidden border-t border-white/10 px-6 py-5 flex flex-col gap-1"
          style={{
            background: "rgba(15,23,42,0.97)",
            backdropFilter: "blur(12px)",
            opacity: 0,
            transition: "opacity 0.2s ease",
          }}
        >
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-gray-300 hover:text-white transition-colors font-medium py-3 border-b border-white/5"
            >
              {link.label}
            </a>
          ))}
          <a
            href="#"
            className="mt-3 text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-lg transition-colors font-medium text-center"
          >
            Star on GitHub ★
          </a>
        </nav>
      </Dynamic>

      <Script id="hello-nav-script" options={{ streakCount }}>
        {(gDom: GDom, options: { streakCount: number }) => {
          const nav = document.getElementById("site-nav");
          if (!nav) return;

          // Count up the streak badge from 0 -> options.streakCount.
          const countEl = document.getElementById("streak-count");
          const target = options.streakCount ?? 0;
          if (countEl && target > 0) {
            const durationMs = 900;
            const start = performance.now();
            const tick = (now: number) => {
              const progress = Math.min((now - start) / durationMs, 1);
              const eased = 1 - Math.pow(1 - progress, 3);
              countEl.textContent = String(Math.round(eased * target));
              if (progress < 1) requestAnimationFrame(tick);
            };
            requestAnimationFrame(tick);
          }

          const onScroll = () => {
            if (window.scrollY > 60) {
              nav.style.background = "rgba(15, 23, 42, 0.95)";
              nav.style.backdropFilter = "blur(12px)";
              nav.style.borderBottom = "1px solid rgba(255,255,255,0.08)";
            } else {
              nav.style.background = "transparent";
              nav.style.backdropFilter = "none";
              nav.style.borderBottom = "none";
            }
          };
          window.addEventListener("scroll", onScroll, { passive: true });
          onScroll();

          const btn = document.getElementById("mobile-menu-btn");
          const hamTop    = document.getElementById("ham-top");
          const hamMid    = document.getElementById("ham-mid");
          const hamBottom = document.getElementById("ham-bottom");
          if (!btn) return;

          let menuOpen   = false;
          let menuLoaded = false;

          const setHamburger = (open: boolean) => {
            if (!hamTop || !hamMid || !hamBottom) return;
            if (open) {
              hamTop.style.transform    = "translateY(8px) rotate(45deg)";
              hamMid.style.opacity      = "0";
              hamBottom.style.transform = "translateY(-8px) rotate(-45deg)";
            } else {
              hamTop.style.transform    = "";
              hamMid.style.opacity      = "1";
              hamBottom.style.transform = "";
            }
            btn.setAttribute("aria-expanded", open ? "true" : "false");
          };

          btn.addEventListener("click", () => {
            if (!menuLoaded) {
              gDom.loadDynamicComponent("hello-mobile-menu", () => {
                const menu = document.getElementById("mobile-menu-content");
                if (!menu) return;
                requestAnimationFrame(() => { menu.style.opacity = "1"; });
              });
              menuLoaded = true;
              menuOpen   = true;
              setHamburger(true);
              return;
            }

            const menu = document.getElementById("mobile-menu-content");
            if (!menu) return;

            if (menuOpen) {
              menu.style.opacity = "0";
              setTimeout(() => { menu.style.display = "none"; }, 200);
              menuOpen = false;
              setHamburger(false);
            } else {
              menu.style.display = "";
              requestAnimationFrame(() => { menu.style.opacity = "1"; });
              menuOpen = true;
              setHamburger(true);
            }
          });
        }}
      </Script>
    </header>
  );
};

export default HelloNav;
