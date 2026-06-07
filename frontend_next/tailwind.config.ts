import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: {
          50: "#fffaf0",
          100: "#fbf7ee",
          200: "#f8f3e8",
          300: "#f4efe3"
        },
        sage: {
          100: "#e7f2eb",
          200: "#cfe5d8",
          300: "#8ab89d",
          700: "#2f6f52"
        },
        warm: {
          border: "#e7dfd0",
          text: "#2f2f2f",
          muted: "#667085"
        }
      },
      boxShadow: {
        soft: "0 24px 70px rgba(47, 47, 47, 0.10)",
        card: "0 16px 42px rgba(47, 47, 47, 0.08)"
      },
      borderRadius: {
        "4xl": "2rem"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
