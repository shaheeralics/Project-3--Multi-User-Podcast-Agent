/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e7fff7",
          100: "#c4ffe8",
          200: "#8affd3",
          300: "#4df6ba",
          400: "#22d3a9",
          500: "#10b981",
          600: "#0d8c64",
          700: "#0a6d51",
          800: "#0a5944",
          900: "#0b4a3a"
        }
      },
      boxShadow: {
        soft: "0 10px 30px -10px rgba(16,185,129,0.35)"
      }
    },
  },
  plugins: [],
}
