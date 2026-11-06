import { Script, type GDom } from "streak-forge/components";

type HelloTerminalProps = {
  data?: {
    promptLabel?: string;
    lines?: string[];
    typeSpeedMs?: number;
  };
};

const HelloTerminal = (props: HelloTerminalProps) => {
  const promptLabel = props?.data?.promptLabel ?? "streak@forge";
  const lines = props?.data?.lines ?? ["$ echo Hello, Streak.js"];
  const typeSpeedMs = props?.data?.typeSpeedMs ?? 22;

  return (
    <section id="hello-terminal" className="py-28 px-6" style={{ background: "#09090b" }}>
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            See it build
          </h2>
          <p className="mt-3 text-gray-500 text-sm">
            The exact pipeline this page went through — typed out live.
          </p>
        </div>

        <div
          id="terminal-window"
          className="rounded-2xl overflow-hidden border border-white/10 shadow-2xl"
          style={{ background: "#0d1117" }}
        >
          {/* Title bar */}
          <div
            className="flex items-center gap-2 px-4 py-3 border-b border-white/5"
            style={{ background: "#161b22" }}
          >
            <span className="w-3 h-3 rounded-full" style={{ background: "#ff5f56" }} />
            <span className="w-3 h-3 rounded-full" style={{ background: "#ffbd2e" }} />
            <span className="w-3 h-3 rounded-full" style={{ background: "#27c93f" }} />
            <span className="ml-3 text-xs text-gray-500 font-mono">{promptLabel}</span>
          </div>

          {/*
            Lines render fully server-side (real content, works with JS off).
            The Script below re-types them character-by-character on mount —
            it reads the same `lines` from `options`, not the DOM, so the
            typed output is guaranteed to match what's already here.
          */}
          <div
            id="terminal-body"
            className="p-6 font-mono text-sm leading-relaxed"
            style={{ minHeight: "220px" }}
          >
            {lines.map((line, i) => (
              <div key={i} id={`term-line-${i}`} className="text-gray-300 whitespace-pre">
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/*
        Script: typewriter reveal. `lines` and `typeSpeedMs` are server-derived
        (from HomeDataHandler) and only survive `.toString()` serialization
        via `options` — see CLAUDE.md's Script section.
      */}
      <Script id="hello-terminal-script" options={{ lines, typeSpeedMs }}>
        {(gDom: GDom, options: { lines: string[]; typeSpeedMs: number }) => {
          const scriptLines: string[] = options.lines ?? [];
          const speed: number = options.typeSpeedMs ?? 22;

          const colorFor = (line: string) =>
            line.startsWith("$")
              ? "#79c0ff"
              : line.startsWith("✓")
                ? "#3fb950"
                : line.startsWith("→")
                  ? "#8b949e"
                  : "#c9d1d9";

          let lineIndex = 0;

          const typeLine = () => {
            if (lineIndex >= scriptLines.length) return;

            const text = scriptLines[lineIndex] ?? "";
            const el = document.getElementById(`term-line-${lineIndex}`);
            if (!el) {
              lineIndex++;
              typeLine();
              return;
            }

            el.style.color = colorFor(text);
            el.textContent = "";

            const cursor = document.createElement("span");
            cursor.textContent = "▋";
            cursor.style.opacity = "0.8";

            let charIndex = 0;
            const tick = () => {
              el.textContent = text.slice(0, charIndex);
              el.appendChild(cursor);
              charIndex++;
              if (charIndex <= text.length) {
                setTimeout(tick, speed);
              } else {
                cursor.remove();
                lineIndex++;
                setTimeout(typeLine, 180);
              }
            };
            tick();
          };

          typeLine();
        }}
      </Script>
    </section>
  );
};

export default HelloTerminal;
