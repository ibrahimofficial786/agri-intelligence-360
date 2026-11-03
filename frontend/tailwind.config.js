/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        field: { 50: '#f0f5ee', 100: '#e2ebde', 200: '#c9d9c2', 300: '#a3bd99', 500: '#4d8a47', 600: '#2f6b3a', 700: '#1f5130', 800: '#173d25', 900: '#0f2a19' },
        turmeric: { 100: '#fbefc8', 400: '#e8b32f', 600: '#b5810d' },
        soil: { 700: '#4a3a2c', 100: '#eee7de' },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', '"Noto Sans Telugu"', 'system-ui', 'sans-serif'],
        sans: ['"Public Sans"', '"Noto Sans Telugu"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
