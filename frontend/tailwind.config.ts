import type { Config } from "tailwindcss";

/**
 * Design tokens for the Digital Twin control center.
 * Every colour, radius and shadow used in the UI is declared here so the
 * visual language stays consistent across all pages.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces — dark neutral, slightly blue-shifted engineering palette
        base: "#070A0F",
        surface: {
          DEFAULT: "#0D1117",
          raised: "#121822",
          overlay: "#171F2B",
          inset: "#0A0E14",
        },
        line: {
          DEFAULT: "#1E2733",
          strong: "#2A3644",
          soft: "#161D27",
        },
        content: {
          DEFAULT: "#E7ECF3",
          muted: "#93A1B5",
          faint: "#64748B",
        },
        // Semantic status — used identically everywhere
        ok: { DEFAULT: "#22C55E", soft: "#0E2C1C" },
        warn: { DEFAULT: "#F59E0B", soft: "#2E2109" },
        crit: { DEFAULT: "#EF4444", soft: "#2E1113" },
        info: { DEFAULT: "#38BDF8", soft: "#0A2434" },
        idle: { DEFAULT: "#64748B", soft: "#161D27" },
        // Domain accents — charts and energy-flow only
        accent: {
          load: "#38BDF8",
          gen: "#22C55E",
          forecast: "#A78BFA",
          baseline: "#7C8BA1",
          solar: "#FBBF24",
          battery: "#2DD4BF",
          grid: "#60A5FA",
          thermal: "#FB7185",
        },
      },
      borderRadius: {
        lg: "10px",
        xl: "14px",
        "2xl": "18px",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Inter",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "SF Mono",
          "JetBrains Mono",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.04em" }],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.8)",
        lift: "0 12px 32px -16px rgba(0,0,0,0.9)",
      },
      keyframes: {
        "pulse-dot": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.45", transform: "scale(0.85)" },
        },
        "flow-dash": {
          to: { strokeDashoffset: "-24" },
        },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "pulse-dot": "pulse-dot 2.4s ease-in-out infinite",
        "flow-dash": "flow-dash 1.2s linear infinite",
        "fade-up": "fade-up 0.25s ease-out both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
