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
│   └── h4yf-design-tokens.css      Placeholder — see note below
└── woocommerce/
    └── README.md                   WooCommerce-specific settings/notes
                                     (most WC config lives inside h4yf_wp_setup.ps1)
```

## Security — read this before running anything here

**Both scripts read credentials from environment variables / Script
Properties. Neither hardcodes a secret.** This matters because the
original Drive copy of `h4yf_wp_setup.ps1` had a live-looking WooCommerce
REST API consumer key (`ck_...`) hardcoded in it. That version was **not**
committed here.

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

## `h4yf-design-tokens.css` — known gap

This file is a placeholder. The real design system CSS lives inline in
the source Drive doc as a large generated block; a Drive API rate limit
during this session blocked pulling and verifying it byte-for-byte, and
rather than guess at the brand's actual hex values, it was left as a TODO
with instructions in the file header. Pull it from Drive and paste it in
before running `h4yf_wp_setup.ps1` STEP 3 for real — until then that step
pushes an effectively empty stylesheet.

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

A WooCommerce **Inventory Sync & Automation Engine** doc exists in
`06 — AUTOMATION SCRIPTS & TOOLS` that wasn't pulled into this PR — a
Drive API rate limit hit mid-session. Also still Drive-only: `h4yf_seo_pusher.gs`,
`h4yf_ebay_image_fetcher.gs`, `h4yf_ebay_optimizer.py`, and the StockX API
Integration Spec. Worth a follow-up pass once the rate limit clears.
