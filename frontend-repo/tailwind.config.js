/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        card: {
          DEFAULT: 'rgba(15, 23, 42, 0.95)',
          hover: 'rgba(15, 23, 42, 0.98)'
        }
      },
      boxShadow: {
        glow: '0 0 20px rgba(99, 102, 241, 0.1)'
      }
    },
  },
  plugins: [],
}