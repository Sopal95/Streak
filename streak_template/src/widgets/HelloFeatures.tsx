import { Dynamic, Script, type GDom } from "streak-forge/components";

type Feature = {
  id: string;
  title: string;
  description: string;
  image: string;
  imageAlt: string;
};

type HelloFeaturesProps = {
  data?: {
    heading?: string;
    features?: Feature[];
  };
};

const HelloFeatures = (props: HelloFeaturesProps) => {
  const heading = props?.data?.heading ?? "What Streak.js gives you";
  const features = props?.data?.features ?? [];

  return (
    <section id="features" className="py-28 px-6 bg-white">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
            {heading}
          </h2>
          <div className="mt-4 mx-auto w-16 h-1 rounded-full bg-indigo-500" />
        </div>

        {/* Feature cards - statically rendered */}
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <article
              key={feature.id}
              id={`feature-card-${feature.id}`}
              className="group rounded-2xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 bg-white"
            >
              {/* Image */}
              <div className="relative overflow-hidden h-48">
                <img
                  src={feature.image}
                  alt={feature.imageAlt}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                  width={600}
                  height={400}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
              </div>

              {/* Text */}
              <div className="p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </article>
          ))}
        </div>

        {/*
          Dynamic: this "learn more" panel is NOT in the initial static HTML.
          It is injected on demand when the user clicks the button.
          This keeps the initial HTML smaller and improves Time to Interactive.
        */}
        <Dynamic id="features-expand-panel">
          <div
            id="features-panel-content"
            className="mt-12 p-8 rounded-2xl bg-indigo-50 border border-indigo-100"
            style={{ opacity: 0, transition: "opacity 0.4s ease" }}
          >
            <h3 className="text-xl font-bold text-indigo-900 mb-3">
              How the build pipeline works
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-indigo-800">
              <li>
                <strong>streak-forge pre-build</strong> reads{" "}
                <code>streak.sitemap.json</code>
              </li>
              <li>
                It calls your <strong>dataHandler</strong> and gets back a data
                object
              </li>
              <li>
                Each <strong>widget</strong> receives its slice as{" "}
                <code>{"props.data"}</code>
              </li>
              <li>React renders widgets to HTML strings</li>
              <li>
                Output lands in{" "}
                <code>out/{"<renderId>"}/index.html</code> - done.
              </li>
            </ol>
          </div>
        </Dynamic>

        {/* Button that triggers the Dynamic panel */}
        <div className="mt-10 text-center">
          <button
            id="expand-features-btn"
            className="inline-flex items-center gap-2 px-6 py-3 border border-indigo-300 text-indigo-700 rounded-xl text-sm font-medium hover:bg-indigo-50 transition-colors"
          >
            <span>How does the build work?</span>
            <span id="expand-arrow" aria-hidden="true">↓</span>
          </button>
        </div>

        <Script id="hello-features-script">
          {(gDom: GDom) => {
            const btn = document.getElementById("expand-features-btn");
            const arrow = document.getElementById("expand-arrow");
            if (!btn) return;

            let loaded = false;

            btn.addEventListener("click", () => {
              if (loaded) return;
              loaded = true;

              if (arrow) arrow.textContent = "…";
              btn.setAttribute("disabled", "true");

              gDom.loadDynamicComponent("features-expand-panel", () => {
                if (arrow) arrow.textContent = "↑";
                btn.removeAttribute("disabled");

                const panel = document.getElementById("features-panel-content");
                if (panel) {
                  requestAnimationFrame(() => {
                    panel.style.opacity = "1";
                    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
                  });
                }
              });
            });
          }}
        </Script>
      </div>
    </section>
  );
};

export default HelloFeatures;
