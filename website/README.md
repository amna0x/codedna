# CodeDNA website

The existing buildless HTML/CSS/JavaScript website, redesigned on 28 October
2026 using the owner's Universal Website Design Blueprint. This is a local
source update, not a public deployment.

## Design

The overview uses a light opening poster, layered HTML/SVG workflow
illustrations, mint/lilac/sand chapters, a dark workflow rail, and a closing
setup action. Documentation, language plugins, and downloads use the same
identity with direct task-oriented layouts. The illustrations are labelled
examples, not product screenshots, actual analysis, or test results.

No framework, animation library, external font, analytics, or service was
added. `site.js` handles presentation only: mobile navigation, workflow
filters, and optional intersection-based reveals. It does not perform code
analysis. Core and plugin installation behavior remains separate.

`plugins.js`, `catalogue/index.json`, and the original catalogue tests are
unchanged. Public installer links remain unavailable; the download page
states that explicitly. The private source setup remains labelled for
collaborators. Java risk support is not attributed to Python/mixed projects.

## Local preview

From the repository root:

```text
python -m http.server 8771 --bind 127.0.0.1 --directory website
```

Open `http://127.0.0.1:8771/`. Direct HTML navigation works without JavaScript;
catalogue loading needs JavaScript and HTTP. Its fallback keeps bundled Java
and Python support clear. Reduced motion disables transitions and reveals.

## Website tests

```text
node --test website/tests/plugins.test.cjs website/tests/site.test.cjs
```

The 13 original catalogue checks and five presentation checks pass. Browser
verification covers all four pages at 375, 768, and 1440 pixels, workflow
filtering, mobile-menu Escape/focus, offline catalogue handling, and no-JS
navigation. There is no page-level horizontal overflow at those widths.
This is not a claim of comprehensive WCAG certification or clean-PC testing.

The original eight website files were archived byte-for-byte with a SHA-256
manifest before redesign at:
`C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/website-before-redesign-20261027.zip`.
Local QA captures and browser-results.json are in the sibling `website-qa/`
workspace folder. Neither backup nor local captures are public site assets.

No backend source, model, policy, threshold, original study, installer, or
publication state was changed. The separately completed 636-test backend
validation is historical evidence, not a new test run for this redesign.
