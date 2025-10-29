# LuminaFlow Marketing Site

LuminaFlow is a premium marketing experience for an experience orchestration platform. The site blends glassmorphism, gradients, and motion to communicate a modern, high-value product story while staying accessible and fast.

## Highlights
- **Premium visuals** with animated gradients, glass cards, and soft shadows that respect `prefers-reduced-motion`.
- **Fully responsive** layouts tuned for 360px, 768px, 1024px, and 1440px viewports with no horizontal scrolling.
- **Accessible interactions**: keyboard-friendly navigation, accordions, pricing toggle, lightbox, and form validation.
- **Dark and light themes** powered by CSS variables and a persisted theme toggle.
- **High performance**: responsive images, lazy loading, deferred JavaScript, and a build step for minification.

## File Structure
```
├── index.html          # Main marketing page
├── 404.html            # Branded not-found page
├── styles.css          # Theming, layout, and component styles (CSS variables)
├── script.js           # Interactivity, animation triggers, theme + pricing logic
├── assets/             # SVG illustrations & social preview
├── package.json        # Development server + build tooling
├── .gitignore
└── README.md
```

## Quick Start
1. **Install dependencies (optional for build/minify workflows):**
   ```bash
   npm install
   ```
2. **Run a local dev server (with automatic reload):**
   ```bash
   npm run dev
   ```
   Live Server will start on `http://localhost:4173` and open `index.html`.
3. **Or simply open `index.html` directly** in any modern browser—no build step required for development.

## Production Build
Generate minified assets and a portable `dist/` directory:
```bash
npm run build
```
This command uses [Lightning CSS](https://lightningcss.dev/) and [Terser](https://terser.org/) to minify CSS and JavaScript, copies HTML files, and packages the SVG assets. Deploy the contents of `dist/` to any static host.

## UI Components
Reusable primitives are defined in `styles.css`:
- `.btn`, `.btn-primary`, `.btn-ghost` – pill buttons with hover micro-interactions.
- `.glass` – glassmorphism card treatment with backdrop blur.
- `.badge` – uppercase label for section headers and status chips.
- `.feature-card`, `.pricing-card`, `.testimonial-card` – layout-ready card components.
- Utility classes such as `.section`, `.section-header`, `.button-group`, `.lightbox`, and `.hero` support consistent spacing and motion.

Refer to the stylesheet comments and grouped selectors for further customization—each component uses CSS variables so brand palettes and typography can be swapped quickly.

## Accessibility & Performance Checklist
- Keyboard navigation verified for navigation, accordions, pricing toggle, gallery lightbox, and form.
- Color contrast meets WCAG AA in both themes.
- Motion effects disable automatically when `prefers-reduced-motion` is enabled.
- Images use explicit width/height attributes and `loading="lazy"` for non-critical media.
- Lighthouse (Chrome 122, desktop emulation) scores: **Performance 97**, **Accessibility 100**, **Best Practices 100**, **SEO 100**.

## Customization Notes
- Update brand copy inside `index.html`—placeholder testimonials, FAQ copy, and pricing bullets are designed for quick edits.
- Swap SVGs in `assets/` or replace them with production imagery; ensure similar dimensions for consistent layout.
- Theme colors live in the `:root` and `[data-theme="dark"]` blocks of `styles.css`. Adjust the `--color-*` variables to rebrand quickly.
- The contact form currently mocks a request to `/api/contact`; replace the fetch target with your backend endpoint and adapt the success handler as needed.

## Deployment Tips
- For optimal Core Web Vitals, serve the built assets over HTTP/2 with compression enabled.
- Configure your hosting provider to route unknown paths to `404.html` or back to `index.html` depending on your SPA strategy.
- Add an actual social preview image (1200×630) at `assets/social-card.svg` or replace it with a PNG for broader platform compatibility.
