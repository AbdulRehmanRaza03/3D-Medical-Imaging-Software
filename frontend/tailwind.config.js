/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef5ff",
          100: "#d9e8ff",
          200: "#bcd8ff",
          300: "#8ebfff",
          400: "#599bff",
          500: "#3377ff",
          600: "#1b57f0",
          700: "#1443d6",
          800: "#1738ad",
          900: "#193687",
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
