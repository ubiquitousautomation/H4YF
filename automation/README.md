# H4YF Automation — WordPress, WooCommerce, GitHub

Git-tracked mirror of the WordPress + WooCommerce automation scripts that
previously lived only in Drive (`06 — AUTOMATION SCRIPTS & TOOLS`). Same
purpose as `marketing/`: give the automation a stable, versioned source
instead of live docs, and make it CI-checkable.

## Layout

```
automation/
├── wordpress/
│   ├── h4yf_wp_setup.ps1           One-click WP setup: plugins, WooCommerce
│   │                                settings, CSS push, site identity
│   ├── h4yf_wp_site_builder.gs     Apps Script: push page content + print
│   │                                nav menu structure via WP REST API
│   └── h4yf-design-tokens.css      Real design system CSS (see note below)
└── woocommerce/
    ├── README.md                   WooCommerce-specific settings/notes
    └── h4yf_inventory_sync.gs      Apps Script: Master Catalog <-> WooCommerce
                                     bidirectional sync, sale tracking, reports
```

## Security — read this before running anything here

**Every script here reads credentials from environment variables / Script
Properties. None hardcodes a secret.** This matters because the original
Drive copies of `h4yf_wp_setup.ps1` AND `h4yf_inventory_sync.gs` both had
the same live-looking WooCommerce REST API consumer key (`ck_...`)
hardcoded — identical value in both files, confirming it's one real key
reused across scripts. Neither original value was committed here.

- If that key is still active, **rotate it**: WooCommerce → Settings →
  Advanced → REST API → regenerate. Treat any key that was ever pasted
  into a shared doc as compromised.
- `h4yf_wp_setup.ps1` requires `H4YF_WP_BASE_URL`, `H4YF_WP_ADMIN_USER`,
  `H4YF_WP_APP_PASSWORD`, `H4YF_WC_CONSUMER_KEY`, `H4YF_WC_CONSUMER_SECRET`
  as environment variables — it exits immediately if any are missing.
- `h4yf_wp_site_builder.gs` reads the same shape of config from Apps
  Script's `PropertiesService` (Project Settings → Script Properties),
  which is Google's built-in per-project secret store — never edit
  credentials directly into the `.gs` file.
- If this ever moves into a GitHub Actions workflow, use **repository
  secrets** (`Settings → Secrets and variables → Actions`), never
  workflow-file literals.

## `h4yf-design-tokens.css` — resolved

Populated with the real design system CSS from the source Drive doc
(colors, type scale, WooCommerce product grid/button styling, the
auth-checklist numbered-list component, etc.). One caveat: the final
media-query rule at the bottom of the source file didn't survive the
transcription cleanly, so those two lines (`@media(max-width:768px)`
and `@media(max-width:480px)` — responsive product-grid column counts)
were reconstructed from the surrounding pattern rather than pulled
byte-exact. Worth a quick diff against the Drive source next time it's
open. Verify colors/spacing still match `07 — BRAND ASSETS` before
pushing to production — this was captured from a June 2026 snapshot.

## `h4yf_wp_site_builder.gs` — known gap

Same story: `getPageContent()` is a stub. The real page HTML (About, FAQ,
Authentication, Shipping, Trusted Partners, Contact) is long-form
generated content in the Drive doc. Recommended fix when populating this:
point `getPageContent()` at a Drive doc/sheet as the content source at
runtime instead of inlining HTML in the script — keeps content edits out
of code review and lets non-engineers update copy without touching code.

## CI

`.github/workflows/ci.yml` includes a `wordpress-scripts` job:

- Syntax-checks `h4yf_wp_site_builder.gs` (copied to `.js` first — Node
  refuses to parse the `.gs` extension directly, but Apps Script syntax
  is plain JS)
- Syntax-checks `h4yf_wp_setup.ps1` with PowerShell's tokenizer (parse
  only, never executed — no credentials needed for this check)

## What's still only in Drive

`h4yf_seo_pusher.gs`, `h4yf_ebay_image_fetcher.gs`, `h4yf_ebay_optimizer.py`,
and the StockX API Integration Spec haven't been pulled into this repo yet.
Worth a follow-up pass.
