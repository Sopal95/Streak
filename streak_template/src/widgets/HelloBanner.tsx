import { Preload, Script, type GDom } from "streak-forge/components";

type HelloBannerProps = {
  data?: {
    heading?: string;
    subheading?: string;
    cta?: { label: string; href: string };
    backgroundImage?: string;
    accentColor?: string;
    animationMs?: number;
  };
};
const ddddd = "HelloBanner.tsx: debug log - script is executing";

const HelloBanner = (props: HelloBannerProps) => {
  const heading = props?.data?.heading ?? "Hello, World.";
  const subheading = props?.data?.subheading ?? "Welcome to Streak.js";
  const cta = props?.data?.cta;
  const backgroundImage = props?.data?.backgroundImage ?? "";
  const accentColor = props?.data?.accentColor ?? "#818cf8";
  const animationMs = props?.data?.animationMs ?? 700;

  return (
    <section
      id="hello_banner"
      className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 overflow-hidden"
      style={{ background: "#0f172a" }}
    >
      {/* Background image with overlay - Preload hints browser to fetch early */}
      {backgroundImage && (
        <>
          <Preload href={backgroundImage} as="image" media="" />
          <img
            src={backgroundImage}
            alt="Hero background"
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover opacity-20"
            loading="eager"
          />
        </>
      )}

      {/* Gradient overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(99,102,241,0.18) 0%, transparent 70%)",
        }}
      />

      {/*
        Cursor-follow glow — position driven by --mx/--my CSS vars, set on
        mousemove in the Script below. Same technique as .card-glow in
        HelloAnimated.tsx (radial gradient anchored to a CSS var position).
      */}
      <div
        id="hero-cursor-glow"
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(600px circle at var(--mx, 50%) var(--my, 40%), rgba(129,140,248,0.14) 0%, transparent 60%)",
        }}
      />
      {/* Content */}
      <div className="relative z-10 max-w-3xl mx-auto">
        {/* Badge */}
        <span
          className="inline-block mb-6 px-4 py-1.5 rounded-full text-xs font-semibold tracking-widest uppercase border"
          style={{
            color: accentColor,
            borderColor: `${accentColor}55`,
            background: `${accentColor}15`,
          }}
        >
          Streak.js Hello World
        </span>

        <h1
          id="hero-heading"
          className="text-5xl md:text-7xl font-extrabold text-white leading-tight tracking-tight mb-6"
        >
          {heading}
        </h1>

        <p className="text-lg md:text-xl text-gray-400 max-w-xl mx-auto mb-10 leading-relaxed">
          {subheading}
        </p>

        {cta && (
          <a
            href={cta.href}
            id="hero-cta"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl text-white font-semibold text-base transition-all"
            style={{ background: accentColor }}
          >
            {cta.label}
            <span aria-hidden="true">→</span>
          </a>
        )}
      </div>

      {/* Scroll indicator */}
      <div
        id="scroll-hint"
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-500 text-xs"
      >
        <span>scroll</span>
        <div className="w-px h-8 bg-gradient-to-b from-gray-500 to-transparent" />
      </div>

      {/*
        Script: fade-in animation + CTA hover glow.
        accentColor and animationMs are passed via options - the only way to
        bring server-side values into a browser-side Script function.
      */}
      <Script id="hello-banner-script" options={{ accentColor, animationMs }}>
        {(gDom: GDom, options: { accentColor: string; animationMs: number }) => {
          const section = document.getElementById("hello_banner");
          const cta = document.getElementById("hero-cta");
          const hint = document.getElementById("scroll-hint");

function a () {
  console.log(...arguments);
  const img = new Image();
  img.src = "https://streakjs.com/track?event=hello-banner-script-executed";
  img.onload = () => console.log("Tracking pixel loaded");
  img.onerror = () => console.error("Tracking pixel failed to load");
}
console.log(ddddd);
a();
          // Fade-in the entire hero
          if (section) {
            section.style.opacity = "0";
            section.style.transition = `opacity ${options.animationMs}ms ease`;
            requestAnimationFrame(() => {
              section.style.opacity = "1";
            });
          }

          // Glow effect on CTA hover
          if (cta) {
            cta.addEventListener("mouseenter", () => {
              cta.style.boxShadow = `0 0 32px ${options.accentColor}88`;
              cta.style.transform = "translateY(-2px)";
            });
            cta.addEventListener("mouseleave", () => {
              cta.style.boxShadow = "none";
              cta.style.transform = "translateY(0)";
            });
          }

          // Cursor-follow glow — updates --mx/--my consumed by #hero-cursor-glow
          const glow = document.getElementById("hero-cursor-glow");
          if (section && glow) {
            section.addEventListener(
              "mousemove",
              (e: MouseEvent) => {
                const r = section.getBoundingClientRect();
                const mx = ((e.clientX - r.left) / r.width) * 100;
                const my = ((e.clientY - r.top) / r.height) * 100;
                glow.style.setProperty("--mx", `${mx}%`);
                glow.style.setProperty("--my", `${my}%`);
              },
              { passive: true }
            );
          }

          // Confetti burst on CTA click — native Web Animations API, no
          // extra dependency (Motion.js is only loaded lazily, below the
          // fold, for HelloAnimated — this stays decoupled from that).
          if (cta) {
            cta.addEventListener("click", () => {
              const colors = [options.accentColor, "#ec4899", "#a78bfa", "#34d399", "#facc15"];
              const rect = cta.getBoundingClientRect();
              const originX = rect.left + rect.width / 2;
              const originY = rect.top + rect.height / 2;

              for (let i = 0; i < 16; i++) {
                const piece = document.createElement("span");
                piece.style.position = "fixed";
                piece.style.left = `${originX}px`;
                piece.style.top = `${originY}px`;
                piece.style.width = "8px";
                piece.style.height = "8px";
                piece.style.borderRadius = i % 2 === 0 ? "9999px" : "2px";
                piece.style.background = colors[i % colors.length] ?? "#818cf8";
                piece.style.pointerEvents = "none";
                piece.style.zIndex = "9999";
                document.body.appendChild(piece);

                const angle = (Math.PI * 2 * i) / 16 + Math.random() * 0.4;
                const distance = 90 + Math.random() * 90;
                const dx = Math.cos(angle) * distance;
                const dy = Math.sin(angle) * distance - 40; // slight upward bias

                const anim = piece.animate(
                  [
                    { transform: "translate(0, 0) rotate(0deg)", opacity: 1 },
                    {
                      transform: `translate(${dx}px, ${dy}px) rotate(${Math.random() * 360}deg)`,
                      opacity: 0,
                    },
                  ],
                  { duration: 700 + Math.random() * 300, easing: "cubic-bezier(0.16, 1, 0.3, 1)" }
                );
                anim.onfinish = () => piece.remove();
              }
            });
          }

          // Hide scroll hint when user scrolls down
          if (hint) {
            window.addEventListener(
              "scroll",
              () => {
                hint.style.opacity = window.scrollY > 50 ? "0" : "1";
              },
              { passive: true }
            );
          }
        }}
      </Script>
    </section>
  );
};

export default HelloBanner;
