/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/src/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'indigo-600': '#4f46e5',
      },
    },
  },
  plugins: [],
}
