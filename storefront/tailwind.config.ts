import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef7ff",
          100: "#d9ecff",
          200: "#bcdcfe",
          300: "#8cc5fd",
          400: "#55a5fa",
          500: "#2f84f4",
          600: "#1a66e9",
          700: "#1552d6",
          800: "#1742ad",
          900: "#183c89"
        }
      }
    }
  },
  plugins: []
};

export default config;
