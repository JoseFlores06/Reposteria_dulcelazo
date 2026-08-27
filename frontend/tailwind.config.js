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
        primary: {
          50:  '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
          800: '#9d174d',
          900: '#831843',
          950: '#500724',
        },
        rose: {
          25:  '#fff8fb',
          50:  '#fff1f7',
          75:  '#ffe8f2',
          100: '#ffdaed',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'rose': '0 2px 16px rgba(236, 72, 153, 0.08)',
        'rose-md': '0 4px 24px rgba(236, 72, 153, 0.12)',
        'rose-lg': '0 8px 40px rgba(236, 72, 153, 0.16)',
      },
      backgroundImage: {
        'rose-gradient': 'linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%)',
        'pink-gradient': 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
        'sidebar-light': 'linear-gradient(180deg, #ffffff 0%, #fdf5f9 100%)',
      },
    },
  },
  plugins: [],
}
