type HelloFooterProps = {
  data?: Record<string, never>;
  common?: {
    branding?: { logoSrc?: string; logoAlt?: string; tagline?: string };
    year?: number;
  };
};

const HelloFooter = (props: HelloFooterProps) => {
  const logoSrc = props?.common?.branding?.logoSrc ?? "/images/streak-logo.svg";
  const logoAlt = props?.common?.branding?.logoAlt ?? "Streak.js";
  const tagline = props?.common?.branding?.tagline ?? "The React static site generator.";
  const year = props?.common?.year ?? new Date().getFullYear();

  return (
    <footer
      className="py-12 px-6 border-t"
      style={{
        background: "#0f172a",
        borderColor: "rgba(255,255,255,0.07)",
      }}
    >
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <img
            src={logoSrc}
            alt={logoAlt}
            width={28}
            height={28}
            className="w-7 h-7 opacity-80"
          />
          <span className="text-white font-semibold">
            Streak<span className="text-indigo-400">.js</span>
          </span>
          <span className="text-gray-600 text-sm hidden md:inline">-</span>
          <span className="text-gray-500 text-sm hidden md:inline">{tagline}</span>
        </div>

        {/* Copyright */}
        <p className="text-gray-600 text-sm">
          © {year} Streak.js. Built with{" "}
          <span className="text-indigo-400">streak-forge</span>.
        </p>
      </div>
    </footer>
  );
};

export default HelloFooter;
