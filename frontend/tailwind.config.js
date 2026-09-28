/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#0B0F19",
          card: "#111827",
          border: "#1F2937",
          accent: "#1E293B"
        }
      }
    },
  },
  plugins: [],
}
