/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
        },
        accent: {
          DEFAULT: "#38bdf8",
        },
        surface: {
          DEFAULT: "#0b0f14",
          panel: "#111820",
          "panel-secondary": "#161f29",
          border: "#26313d",
        },
        slate: {
          850: "#151f2e",
          925: "#0d1520",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06)",
        panel: "0 1px 2px rgba(16,24,40,.06), 0 4px 12px rgba(16,24,40,.05)",
        ring: "0 0 0 3px rgba(27,87,240,.15)",
        glow: "0 0 24px rgba(51,119,255,.18)",
      },
    },
  },
  plugins: [],
};
