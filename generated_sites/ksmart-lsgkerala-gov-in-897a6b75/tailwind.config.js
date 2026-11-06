/** @type {import('tailwindcss').Config} */
const v = (n) => `hsl(var(--${n}) / <alpha-value>)`;
export default {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}", "./public/assets/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), surface: v("surface"), ink: v("ink"), muted: v("muted"), hair: v("hair"),
        teal: "#00b4a6", border: v("border"), input: v("input"), ring: v("ring"),
        background: v("background"), foreground: v("foreground"), card: v("card"), popover: v("popover"),
        primary: { DEFAULT: v("primary"), foreground: v("primary-foreground") },
        secondary: { DEFAULT: v("secondary"), foreground: v("secondary-foreground") },
        accent: { DEFAULT: v("accent"), foreground: v("accent-foreground") },
        destructive: { DEFAULT: v("destructive"), foreground: v("destructive-foreground") },
      },
      fontFamily: {
        display: ["Cabinet Grotesk", "Inter", "sans-serif"],
        sans: ["Satoshi", "Inter", "sans-serif"],
      },
      borderRadius: { sm: "4px", md: "6px", lg: "8px" },
      animation: {
        "accordion-down": "accordion-down .2s ease-out",
        "accordion-up": "accordion-up .2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
