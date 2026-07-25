# WooCommerce — Settings, Sync & Notes

## `h4yf_inventory_sync.gs`

Bidirectional sync between the Master Catalog (Google Sheets) and
WooCommerce. Standalone Apps Script project — paste into script.google.com,
set Script Properties (see file header), then run `setupTriggers()` once.
After that, do not run the sync functions manually — three time-based
triggers handle it:

- `syncPendingToWooCommerce` — every 2 hours, pushes any row flagged
  `Pending` in the Sync Status column
- `dailyStatusAudit` — 7 AM daily, reconciles WooCommerce stock status
  against the catalog and flags mismatches
- `weeklyReport` — Monday 8 AM, logs units/revenue/margin by platform

Also exposes `markItemSold(sku, platform, salePrice, orderId)` — call this
manually (or wire it to a form/webhook) whenever a sale is confirmed on
any platform; it sets the item out-of-stock in WooCommerce and logs the
sale to the Sales Tracker sheet.

## Settings applied by `automation/wordpress/h4yf_wp_setup.ps1`

- Currency: USD
- Store location: Indianapolis, IN (`US:IN`) — for tax calculation
- Taxes: enabled
- Free shipping threshold: $150 (applied to the first shipping zone)

## Credentials

Same rule as `automation/wordpress/`: WooCommerce REST API consumer
key/secret and Google Sheet IDs are read from Script Properties
(`H4YF_WC_CONSUMER_KEY`, `H4YF_WC_CONSUMER_SECRET`,
`H4YF_MASTER_CATALOG_ID`, `H4YF_SALES_TRACKER_ID`, etc.) — never
hardcoded. See `automation/README.md` for the full security note: the
original Drive copies of both the setup script and this sync script had
the *same* live-looking WooCommerce key hardcoded, confirming it's one
real key reused across scripts and deliberately not carried into this repo.

## Category ID map

`getCategoryId()` in `h4yf_inventory_sync.gs` hardcodes a brand/model to
WooCommerce category ID mapping captured from a specific point in time
(commented as "run June 2026"). If categories are ever restructured in
WooCommerce, this map needs regenerating — it's not currently automated.
