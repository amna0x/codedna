# CodeDNA website — React + GSAP

The existing website now uses React 19 and GSAP ScrollTrigger. The original
design and catalogue remain; the overview has shorter copy and fewer repeated
sections. `src/App.jsx` contains the page components and shared React menu,
workflow filters, and catalogue mount. `src/client.jsx` hydrates the pages.

## Build and preview

```text
cd website
npm ci
npm run build
npm test
python -m http.server 8772 --bind 127.0.0.1
```

`build.mjs` bundles dependencies locally and pre-renders all four existing HTML
routes. No CDN, external fonts, new account, or backend service is needed.
Node is needed for rebuilding, not for hosting the generated static pages.
The root HTML files and assets/app.js are generated; edit src/App.jsx and
style.css, then rebuild. Do not hand-edit generated HTML.

ScrollTrigger adds gentle chapter movement and a short heading arrival. It
uses native scrolling, without scroll hijacking or pinned sections. GSAP
contexts and media listeners are cleaned up. Reduced-motion preferences
disable animation, including when changed during a visit. Pre-rendered content
and navigation remain available without JavaScript; the catalogue has a
no-JavaScript fallback.

plugins.js and catalogue/index.json retain their existing validation, pinned
downloads, checksums, and copy behavior. src/catalogue-adapter.js is the module
wrapper for that preserved renderer. site.js and its tests are retained as
legacy compatibility code; pages no longer load that script. React owns new
navigation and filter behavior. Existing tests cover the legacy catalogue;
React pre-render tests and local browser checks cover the new presentation.

Dependencies explicitly requested by the owner: react, react-dom, and gsap.
esbuild is a development-only bundler. Exact versions are pinned in package.json
and package-lock.json. No Python/core dependency or test/risk policy changed.

The pre-React website is preserved locally in
`C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/website-before-react-20261029.zip`.
This update is local source only: no public deployment, push, installer update,
or new claim of backend validation.
