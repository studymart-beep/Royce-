import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: "#FFFEF9",
          100: "#FBF7EF",
          200: "#F5EDE0",
          300: "#EDE2CF",
          400: "#E0D0B5",
        },
        gold: {
          50: "#FBF6E9",
          100: "#F5E8C7",
          200: "#EAD49A",
          300: "#D4B56A",
          400: "#C49A3C",
          500: "#A67C2A",
          600: "#8B6914",
        },
        slate: {
          soft: "#6B7280",
          ink: "#1F2937",
          muted: "#9CA3AF",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 2px 12px rgba(28, 25, 23, 0.06)",
        card: "0 4px 24px rgba(28, 25, 23, 0.08)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
export default config;
