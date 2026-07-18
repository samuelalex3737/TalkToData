import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#112033",
        mist: "#eef4ff",
        sand: "#f4efe7",
        ember: "#b95c31",
        slate: "#213047",
        mint: "#66c3b4",
        signal: "#f2b950",
      },
      boxShadow: {
        panel: "0 18px 48px rgba(10, 19, 34, 0.16)",
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI Variable", "Trebuchet MS", "sans-serif"],
        display: ["Aptos Display", "Aptos", "Trebuchet MS", "sans-serif"],
        mono: ["Cascadia Code", "Consolas", "monospace"],
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(17,32,51,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(17,32,51,0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
} satisfies Config;
