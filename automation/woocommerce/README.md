# WooCommerce — Settings & Notes

Most current WooCommerce automation lives inside
`automation/wordpress/h4yf_wp_setup.ps1` (STEP 4), since WooCommerce is
configured through the same WP REST API session as the rest of site
setup. This file tracks WooCommerce-specific settings and decisions that
don't belong in the script itself.

## Settings applied by `h4yf_wp_setup.ps1`

- Currency: USD
- Store location: Indianapolis, IN (`US:IN`) — for tax calculation
- Taxes: enabled
- Free shipping threshold: $150 (applied to the first shipping zone)

## Known gap: Inventory Sync & Automation Engine

A dedicated **"H4YF — Script — Inventory Sync & Automation Engine"** doc
exists in Drive (`06 — AUTOMATION SCRIPTS & TOOLS`) that covers
WooCommerce catalog sync in more depth than what's captured here — it
wasn't pulled into this repo yet (Drive API rate limit hit mid-session).
Follow up and add it under this directory once available.

## Credentials

Same rule as the rest of `automation/wordpress/`: WooCommerce REST API
consumer key/secret are read from environment variables
(`H4YF_WC_CONSUMER_KEY`, `H4YF_WC_CONSUMER_SECRET`) — never hardcoded.
See `automation/README.md` for the full security note, including why
this matters (a live key was found hardcoded in the original Drive copy
of the setup script and was deliberately not carried into this repo).
