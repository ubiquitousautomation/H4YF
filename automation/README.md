# H4YF Automation — WordPress, WooCommerce, eBay, StockX

Git-tracked mirror of the automation scripts that previously lived only in
Drive (`06 — AUTOMATION SCRIPTS & TOOLS`). Same purpose as `marketing/`:
give the automation a stable, versioned source instead of live docs, and
make it CI-checkable. This now covers every script in that Drive folder.

## Layout

```
automation/
├── wordpress/
│   ├── h4yf_wp_setup.ps1           One-click WP setup: plugins, WooCommerce
│   │                                settings, CSS push, site identity
│   ├── h4yf_wp_site_builder.gs     Apps Script: push page content + print
│   │                                nav menu structure via WP REST API
│   ├── h4yf_seo_pusher.gs          Apps Script: pushes RankMath/LLM/Schema
│   │                                meta from the SEO sheet to WC products
│   └── h4yf-design-tokens.css      Real design system CSS (see note below)
├── woocommerce/
│   ├── README.md                   WooCommerce-specific settings/notes
│   └── h4yf_inventory_sync.gs      Apps Script: Master Catalog <-> WooCommerce
│                                    bidirectional sync, sale tracking, reports
├── ebay/
│   ├── h4yf_ebay_image_fetcher.gs  Apps Script: pulls images from eBay's
│   │                                Browse API, attaches to matching WC products
│   └── h4yf_ebay_optimizer.py      Title/description/pricing/schema generator
│                                    for new eBay listings (no credentials — pure
│                                    content/calculation logic)
└── stockx/
    └── H4YF_StockX_API_Integration_Spec.txt   Planning doc: StockX API access,
                                     the 3 relevant APIs, and the planned
                                     h4yf_stockx_image_fetcher.gs (not yet built)
```

## Security — read this before running anything here

**Every script here reads credentials from environment variables / Script
Properties. None hardcodes a secret.** This matters because the original
Drive copies of several scripts had real credentials hardcoded:

- `h4yf_wp_setup.ps1` and `h4yf_inventory_sync.gs` both had the *same*
  live-looking WooCommerce REST API consumer key (`ck_...`) hardcoded —
  identical value in both files, confirming it's one real key reused
  across scripts.
- `h4yf_seo_pusher.gs` and `h4yf_ebay_image_fetcher.gs` both had the
  *same* live WordPress username (a real email address) and a live
  Application Password hardcoded — again identical across both files.

None of those original values were committed here.

- If the WooCommerce key is still active, **rotate it**: WooCommerce →
  Settings → Advanced → REST API → regenerate.
- If the WordPress Application Password is still active, **revoke it**:
  WP Admin → Users → Your Profile → Application Passwords → Revoke, then
  issue a fresh one and store it only in Script Properties / env vars.
- Treat any credential that was ever pasted into a shared Drive doc as
  compromised — regenerate rather than reuse.
- `h4yf_wp_setup.ps1` requires `H4YF_WP_BASE_URL`, `H4YF_WP_ADMIN_USER`,
  `H4YF_WP_APP_PASSWORD`, `H4YF_WC_CONSUMER_KEY`, `H4YF_WC_CONSUMER_SECRET`
  as environment variables — it exits immediately if any are missing.
- Every `.gs` file reads the same shape of config from Apps Script's
  `PropertiesService` (Project Settings → Script Properties), which is
  Google's built-in per-project secret store — never edit credentials
  directly into a `.gs` file.
- If this ever moves into a GitHub Actions workflow, use **repository
  secrets** (`Settings → Secrets and variables → Actions`), never
  workflow-file literals.

## `h4yf-design-tokens.css` — SUPERSEDED (found 2026-07-25, see below)

This file used to hold the design system CSS pulled from the June 2026
Drive doc, and `h4yf_wp_setup.ps1` STEP 3 pushed it live via
`/wp-json/wp/v2/settings.custom_css`.

**That's now wrong on two counts, discovered while checking whether this
repo's automation should also live in `ubiquitousautomation/ubiq-h4yf-skin`
(the actual theme repo):**

1. **The palette itself is stale.** The June snapshot has a black/gold
   palette with Inter typography. The real, currently-locked canon (in
   `ubiq-h4yf-skin/style.css`, locked 2026-06-22, maintained through at
   least Sprint 6.6 RC3 as of 2026-07-23) is a charcoal/crimson/orange
   palette with Bebas Neue (display) + Montserrat (body).
2. **The deployment model changed.** `ubiq-h4yf-skin` is git-managed and
   deployed via SFTP directly to `wp-content/themes/h4yf-skin/`. Pushing
   CSS through the WordPress REST API's customizer setting — what STEP 3
   did — now fights that deployment instead of complementing it.

**Fix applied:** STEP 3 in `h4yf_wp_setup.ps1` is disabled (logs a
message and pushes nothing). This CSS file is kept only as a
labeled-obsolete historical snapshot — do not deploy it. If a real
design-system change is needed, make it in `ubiq-h4yf-skin/style.css` /
`assets/skin.css` and deploy through that repo's own process, not this one.

**On the broader question this surfaced** — whether `automation/`'s other
scripts (SEO pusher, inventory sync, eBay/StockX tools) should also live
in `ubiq-h4yf-skin` since that's the repo actually running the live
site: that repo already has its own `docs/strategy/salvage/h4yf_ebay_api_reference.md`
and `h4yf_stockx_api_reference.md`, plus its own `scripts/images/`
backfill scripts — so a blind copy risks duplicating/conflicting with
work already done there. That reconciliation is a separate, larger task
than fixing this immediate regression risk, and hasn't been done yet.

## `h4yf_wp_site_builder.gs` — known gap

`getPageContent()` is a stub. The real page HTML (About, FAQ,
Authentication, Shipping, Trusted Partners, Contact) is long-form
generated content in the Drive doc. Recommended fix when populating this:
point `getPageContent()` at a Drive doc/sheet as the content source at
runtime instead of inlining HTML in the script — keeps content edits out
of code review and lets non-engineers update copy without touching code.

## `stockx/` — planning stage, not yet built

The StockX integration doesn't have a script yet — `H4YF_StockX_API_Integration_Spec.txt`
is the plan: apply for StockX developer API access (1–2 week approval),
then build `h4yf_stockx_image_fetcher.gs` mirroring
`ebay/h4yf_ebay_image_fetcher.gs`'s structure, matching by style code
(more reliable than eBay's title-fuzzy-match) to fill in product images
eBay's Browse API couldn't cover. Apply for access before starting the
eBay image pass so approval lands in time.

## CI

`.github/workflows/ci.yml`:

- `python-scripts` job syntax-checks every `.py` under `marketing/scripts`
  and `automation/ebay`, plus a smoke test that runs
  `h4yf_ebay_optimizer.py`'s demo end to end.
- `wordpress-scripts` job syntax-checks every `.gs` file across
  `automation/wordpress/`, `automation/woocommerce/`, and
  `automation/ebay/` (copied to `.js` first — Node refuses to parse the
  `.gs` extension directly, but Apps Script syntax is plain JS), plus
  `h4yf_wp_setup.ps1` via PowerShell's tokenizer (parse only, never
  executed — no credentials needed for this check).
