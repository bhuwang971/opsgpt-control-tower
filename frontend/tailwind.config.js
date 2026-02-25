/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f5f6ff",
          500: "#2442d5",
          700: "#182a93",
        },
      },
    },
  },
  plugins: [],
};
