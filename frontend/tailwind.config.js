/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // ─── Brand color palette ─────────────────────────────────────────────
      colors: {
        brand: {
          50:      "#f5f4ff",
          100:     "#eeeeff",
          200:     "#e0deff",
          300:     "#afa9ec",
          400:     "#8f89e0",
          DEFAULT: "#7C3AED",   // primary — violet-600 (unique source of truth)
          600:     "#6D28D9",   // hover
          dark:    "#534AB7",   // gradient end / secondary
          darker:  "#3C3489",   // text emphasis / active states
          light:   "#f0eeff",   // tinted backgrounds
          border:  "#e8e4ff",   // card borders, dividers
          muted:   "#AFA9EC",   // disabled, placeholder hints
        },
        // ─── Status colors ──────────────────────────────────────────────────
        success: {
          DEFAULT: "#1D9E75",
          light:   "#E1F5EE",
          border:  "#9FE1CB",
          dark:    "#085041",
        },
        // ─── Neutral text scale ─────────────────────────────────────────────
        ink: {
          DEFAULT: "#1a1040",   // headings (replaces #1a1040, #111827)
          body:    "#374151",   // body text
          muted:   "#6B7280",   // secondary text
          subtle:  "#9CA3AF",   // hints, timestamps
        },
      },

      // ─── Typography ──────────────────────────────────────────────────────
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["10px", { lineHeight: "14px", letterSpacing: "0.02em" }],
        xs:    ["11px", { lineHeight: "16px" }],
        sm:    ["12px", { lineHeight: "18px" }],
        base:  ["13px", { lineHeight: "20px" }],
        md:    ["14px", { lineHeight: "22px" }],
        lg:    ["15px", { lineHeight: "24px" }],
        xl:    ["18px", { lineHeight: "28px" }],
        "2xl": ["20px", { lineHeight: "30px" }],
        "3xl": ["24px", { lineHeight: "32px" }],
        "4xl": ["28px", { lineHeight: "36px" }],
        "5xl": ["36px", { lineHeight: "44px" }],
      },

      // ─── Border radius ───────────────────────────────────────────────────
      borderRadius: {
        sm:   "6px",
        DEFAULT: "8px",
        md:   "10px",
        lg:   "12px",
        xl:   "14px",
        "2xl":"16px",
        "3xl":"20px",
        full: "9999px",
      },

      // ─── Box shadow ──────────────────────────────────────────────────────
      boxShadow: {
        card:       "0 2px 8px rgba(124,58,237,0.06)",
        "card-md":  "0 4px 16px rgba(124,58,237,0.10)",
        "card-lg":  "0 8px 32px rgba(124,58,237,0.14)",
        btn:        "0 2px 10px rgba(124,58,237,0.25)",
        "btn-hover":"0 4px 16px rgba(124,58,237,0.35)",
        topbar:     "0 1px 8px rgba(124,58,237,0.06)",
        sidebar:    "2px 0 16px rgba(124,58,237,0.06)",
        pill:       "0 2px 6px rgba(124,58,237,0.25)",
      },

      // ─── Keyframe animations ────────────────────────────────────────────
      keyframes: {
        "slide-up": {
          from: { opacity: 0, transform: "translateY(10px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: 0 },
          to:   { opacity: 1 },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: 1 },
          "50%":      { opacity: 0.3 },
        },
      },
      animation: {
        "slide-up":  "slide-up 0.3s ease forwards",
        "fade-in":   "fade-in 0.2s ease forwards",
        "pulse-dot": "pulse-dot 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
