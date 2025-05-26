# Tailwind CSS Setup

This project uses Tailwind CSS with a proper build process. Follow these steps to set up the development environment:

## Prerequisites

- Node.js (v14 or later)
- npm (comes with Node.js)

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

## Development

To watch for changes and automatically rebuild the CSS during development:

```bash
npm run watch:css
```

## Production Build

To create a production-optimized build:

```bash
npm run build:css
```

## Project Structure

- `app/static/src/css/main.css` - Source CSS file with Tailwind directives
- `app/static/css/main.css` - Processed CSS (generated, do not edit directly)
- `tailwind.config.js` - Tailwind configuration
- `postcss.config.js` - PostCSS configuration

## Customization

Edit `tailwind.config.js` to customize the design system, and add custom styles to `app/static/src/css/main.css`.
