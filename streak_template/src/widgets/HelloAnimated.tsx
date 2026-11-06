import { Script, type GDom } from "streak-forge/components";

type Card = { id: string; icon: string; title: string; description: string };

type HelloAnimatedProps = {
  data?: {
    words?: string[];
    cards?: Card[];
    animationDuration?: number;
  };
};

const HelloAnimated = (props: HelloAnimatedProps) => {
  const words = props?.data?.words ?? ["Fast", "Beautiful", "Powerful", "Static"];
  const cards = props?.data?.cards ?? [];
  const animationDuration = props?.data?.animationDuration ?? 0.65;

  return (
    <section
      id="hello-animated"
      className="relative py-32 px-6 overflow-hidden"
      style={{ background: "#09090b" }}
    >
      {/* ── Scroll progress bar — fixed at page top, width driven by Motion.scroll ── */}
      <div
        id="scroll-bar"
        aria-hidden="true"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          height: "3px",
          background: "linear-gradient(90deg, #818cf8, #a78bfa, #ec4899)",
          transformOrigin: "0% 50%",
          transform: "scaleX(0)",
          zIndex: 9999,
        }}
      />

      {/* ── Background orbs — drift lazily toward the cursor via Motion ── */}
      <div
        id="orb-1"
        aria-hidden="true"
        style={{
          position: "absolute",
          width: "700px",
          height: "700px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(99,102,241,0.28) 0%, transparent 70%)",
          top: "-200px",
          left: "-200px",
          filter: "blur(90px)",
          pointerEvents: "none",
        }}
      />
      <div
        id="orb-2"
        aria-hidden="true"
        style={{
          position: "absolute",
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(167,139,250,0.22) 0%, transparent 70%)",
          bottom: "-180px",
          right: "-180px",
          filter: "blur(80px)",
          pointerEvents: "none",
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto">

        {/* ── Morphing headline ── */}
        <div
          id="animated-header"
          className="text-center mb-20"
          style={{ opacity: 0, transform: "translateY(-30px)" }}
        >
          <span className="inline-block mb-4 px-3 py-1 text-xs font-semibold tracking-widest uppercase rounded-full border border-indigo-500/30 text-indigo-400">
            Motion.js · loaded via Streak's asset worker
          </span>
          <h2 className="mt-4 text-5xl md:text-7xl font-extrabold text-white tracking-tight leading-none">
            Build something
          </h2>
          {/* This word morphs via animate().finished promise chain */}
          <h2
            id="morph-word"
            className="text-5xl md:text-7xl font-extrabold tracking-tight leading-none mt-1"
            style={{
              background: "linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #ec4899 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            {words[0]}
          </h2>
          <p className="mt-6 text-gray-500 max-w-md mx-auto text-base leading-relaxed">
            Every API demonstrated live on this page — no fake demos.
          </p>
        </div>

        {/* ── 3D tilt cards — parent needs perspective for rotateX/Y to show ── */}
        <div
          id="cards-grid"
          className="grid md:grid-cols-3 gap-5"
          style={{ perspective: "1200px" }}
        >
          {cards.map((card) => (
            <div
              key={card.id}
              className="tilt-card relative p-8 rounded-2xl"
              style={{
                opacity: 0,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
                backdropFilter: "blur(16px)",
                transformStyle: "preserve-3d",
                cursor: "default",
              }}
            >
              {/*
                Radial glow follows cursor inside the card.
                --mx and --my CSS vars are set on mousemove via JS.
              */}
              <div
                className="card-glow absolute inset-0 rounded-2xl pointer-events-none"
                style={{
                  opacity: 0,
                  background:
                    "radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(129,140,248,0.18) 0%, transparent 65%)",
                  transition: "opacity 0.2s",
                }}
              />
              <div className="relative">
                <span
                  className="text-4xl mb-5 block"
                  style={{ filter: "drop-shadow(0 0 12px rgba(129,140,248,0.6))" }}
                >
                  {card.icon}
                </span>
                <h3 className="text-lg font-bold text-white mb-2">{card.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{card.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ── Magnetic button — larger zone so cursor attracts from afar ── */}
        <div
          id="magnetic-zone"
          className="flex justify-center"
          style={{ marginTop: "4rem", padding: "3rem" }}
        >
          <a
            id="magnetic-btn"
            href="#"
            className="inline-flex items-center gap-3 px-8 py-4 rounded-full text-white font-semibold text-base"
            style={{
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              boxShadow: "0 0 48px rgba(99,102,241,0.35)",
              display: "inline-flex",
            }}
          >
            <span>Explore Streak.js</span>
            <span
              id="btn-arrow"
              aria-hidden="true"
              style={{ display: "inline-block" }}
            >
              →
            </span>
          </a>
        </div>

      </div>

      {/*
        ── Script: all Motion.js animations wired up here ──────────────────────

        gDom.loadPackage("js/motion.js")
          → Streak's internal asset-worker fetches /assets/js/motion.js off-thread
          → injects it as a <script> tag into <head>
          → Promise resolves, window.Motion is now available as gDom.Motion

        File lives at:  public/assets/js/motion.js  (committed to the repo)
      */}
      <Script
        id="hello-animated-script"
        options={{ animationDuration, words }}
      >
        {(gDom: GDom, options: { animationDuration: number; words: string[] }) => {
          gDom
            .loadPackage("js/motion.js")
            .then(() => {
              const { animate, scroll, inView, stagger, spring } = (gDom as any).Motion;

              // ── 1. Scroll progress bar ───────────────────────────────────
              // scroll(animation) links an existing animation's progress
              // directly to the page scroll position — no callback needed.
              // The bar goes from scaleX:0 to scaleX:1 as the page scrolls.
              scroll(animate("#scroll-bar", { scaleX: [0, 1] }));

              // ── 2. Section header entrance ──────────────────────────────
              animate(
                "#animated-header",
                { opacity: [0, 1], y: [-30, 0] },
                { duration: options.animationDuration, easing: "ease-out" }
              );

              // ── 3. Morphing headline ─────────────────────────────────────
              // animate() returns an object with a `.finished` Promise.
              // Chain .finished calls to sequence animations without nesting.
              const morphEl = document.getElementById("morph-word");
              const words: string[] = options.words ?? [];
              let wordIndex = 0;

              const morphNext = () => {
                wordIndex = (wordIndex + 1) % words.length;

                // Step A: slide current word up and fade out
                animate(morphEl, { opacity: 0, y: -20 }, {
                  duration: 0.22,
                  easing: "ease-in",
                })
                  .finished
                  .then(() => {
                    // Step B: swap the text content
                    if (morphEl) morphEl.textContent = words[wordIndex] ?? "";

                    // Step C: spring the new word in from below
                    return animate(morphEl, { opacity: 1, y: 0 }, {
                      duration: 0.55,
                      easing: spring({ stiffness: 180, damping: 16, restSpeed: 0.5 }),
                    }).finished;
                  })
                  .then(() => {
                    // Step D: wait, then repeat
                    setTimeout(morphNext, 2200);
                  });
              };

              if (morphEl && words.length > 1) setTimeout(morphNext, 2200);

              // ── 4. Staggered card entrance with spring ───────────────────
              // inView fires once when the element enters the viewport.
              // stagger(0.12) adds 0 / 0.12 / 0.24s delays across the 3 cards.
              // spring easing gives a natural overshoot — feels physical.
              inView(
                "#cards-grid",
                () => {
                  animate(
                    ".tilt-card",
                    { opacity: [0, 1], y: [70, 0], scale: [0.86, 1] },
                    {
                      delay: stagger(0.13),
                      duration: 0.9,
                      easing: spring({ stiffness: 110, damping: 13, restSpeed: 0.5 }),
                    }
                  );
                }
              );

              // ── 5. 3D perspective tilt on hover ─────────────────────────
              // rotateX/rotateY require the parent to have perspective set.
              // The grid parent has perspective: 1200px in JSX.
              // spring on mouseleave snaps back with a satisfying overshoot.
              const tiltCards = document.querySelectorAll<HTMLElement>(".tilt-card");

              tiltCards.forEach((card) => {
                card.addEventListener("mousemove", (e: MouseEvent) => {
                  const r = card.getBoundingClientRect();
                  const x = (e.clientX - r.left)  / r.width  - 0.5; // -0.5 to +0.5
                  const y = (e.clientY - r.top)   / r.height - 0.5;

                  animate(card, {
                    rotateX: -y * 22,  // tilt up/down
                    rotateY:  x * 22,  // tilt left/right
                    scale: 1.05,
                  }, { duration: 0.12, easing: "linear" });

                  // Move the inner glow spotlight to cursor position
                  const glow = card.querySelector<HTMLElement>(".card-glow");
                  if (glow) {
                    const mx = ((e.clientX - r.left) / r.width)  * 100;
                    const my = ((e.clientY - r.top)  / r.height) * 100;
                    glow.style.setProperty("--mx", `${mx}%`);
                    glow.style.setProperty("--my", `${my}%`);
                    animate(glow, { opacity: 1 }, { duration: 0.15 });
                  }
                });

                card.addEventListener("mouseleave", () => {
                  animate(card, {
                    rotateX: 0,
                    rotateY: 0,
                    scale: 1,
                  }, {
                    duration: 0.8,
                    easing: spring({ stiffness: 75, damping: 11, restSpeed: 0.5 }),
                  });

                  const glow = card.querySelector<HTMLElement>(".card-glow");
                  if (glow) animate(glow, { opacity: 0 }, { duration: 0.3 });
                });
              });

              // ── 6. Magnetic button ──────────────────────────────────────
              // The magnetic zone (padding: 3rem around the button) is the
              // invisible hit area. Mouse entering it pulls the button.
              // Strength: 35% of cursor offset. Springs back on leave.
              const zone  = document.getElementById("magnetic-zone");
              const btn   = document.getElementById("magnetic-btn");
              const arrow = document.getElementById("btn-arrow");

              if (zone && btn) {
                zone.addEventListener("mousemove", (e: MouseEvent) => {
                  const r  = zone.getBoundingClientRect();
                  const dx = (e.clientX - (r.left + r.width  / 2)) * 0.35;
                  const dy = (e.clientY - (r.top  + r.height / 2)) * 0.35;

                  animate(btn,  { x: dx, y: dy },         { duration: 0.22, easing: "ease-out" });
                  if (arrow) animate(arrow, { x: dx * 0.4 }, { duration: 0.22 });
                }, { passive: true });

                zone.addEventListener("mouseleave", () => {
                  animate(btn,  { x: 0, y: 0 }, {
                    duration: 0.9,
                    easing: spring({ stiffness: 75, damping: 11, restSpeed: 0.5 }),
                  });
                  if (arrow) animate(arrow, { x: 0 }, {
                    duration: 0.7,
                    easing: spring({ stiffness: 100, damping: 14 }),
                  });
                });
              }

              // ── 7. Background orbs drift toward cursor ──────────────────
              // Long duration + ease-out = slow, lazy drift. The two orbs
              // move in opposite directions so they cross as the cursor moves.
              const orb1 = document.getElementById("orb-1");
              const orb2 = document.getElementById("orb-2");

              document.addEventListener("mousemove", (e: MouseEvent) => {
                const nx = e.clientX / window.innerWidth;   // 0 → 1
                const ny = e.clientY / window.innerHeight;  // 0 → 1

                if (orb1) {
                  animate(orb1,
                    { x: nx * 130 - 65, y: ny * 90 - 45 },
                    { duration: 2.8, easing: "ease-out" }
                  );
                }
                if (orb2) {
                  animate(orb2,
                    { x: -(nx * 110 - 55), y: -(ny * 70 - 35) },
                    { duration: 3.5, easing: "ease-out" }
                  );
                }
              }, { passive: true });

            })
            .catch((err: unknown) => {
              console.error("[HelloAnimated] motion.js failed to load:", err);
              console.info("Ensure public/assets/js/motion.js exists in the repo.");
            });
        }}
      </Script>
    </section>
  );
};

export default HelloAnimated;
