/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aws: {
          navy: '#232F3E',
          orange: '#FF9900',
          'light-blue': '#00A1C9',
        },
      },
    },
  },
  plugins: [],
}
