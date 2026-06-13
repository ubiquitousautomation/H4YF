# HEAT4YAFEAT (H4YF) — Claude Code Context

## Project
Authenticated sneaker brand / multi-platform eCommerce.
- **Client:** Bill Bannon (@b2ill2323) — founder, content, authentication expert
- **Consultant:** Josh (JAP / Ubiquitous Solutions, ubiquitousautomation@gmail.com)
- **AI backbone:** Aure (Claude) — scripts, APIs, WP, SEO, data pipelines

## Memory System
All project memory lives in Google Drive (connected via MCP). Cold-start entry point:
- **Master Index v3:** Drive ID `1vKr9uzixjp6jXaR1jWJ4tv06CZx3NoAlckGazC2Vrxs`
- **Source-of-truth folder:** `1cySLlBG799s5VWDp56eSqsZx2jfvKlmc`
- Read `h4yf_cold_start.md` from Drive memory files before any session action.

## Repo Purpose
Script artifacts for Josh to deploy locally at `C:\Users\JAP\`. Pull from this repo → copy scripts to local machine.

## Local Secrets Directory
All credentials live at `C:\Users\JAP\.h4yf_secrets\` — never committed to this repo.

## Key Accounts
| Platform | Handle / Account |
|---|---|
| YouTube | Bill's channel (4 published videos) |
| Instagram | @h4yf16 (status TBD) / @heat4yafeat brand |
| TikTok | @heat4yafeat (claimed June 10, 2026) |
| Facebook | H4YF Page + 2 groups |
| eBay store | ebay.com/str/h4yf |
| WooCommerce (staging) | slategray-stinkbug-650783.hostingersite.com |

## GCP Project (Google APIs)
- Project number: `1070004533548`
- OAuth client (Desktop): `1070004533548-5g7h43gl0j1l8enaeir7c0gsl7uc1kst.apps.googleusercontent.com`
- OAuth client JSON: `C:\Users\JAP\.h4yf_secrets\google_oauth_client_aure.json`
- Gemini API key: `C:\Users\JAP\.h4yf_secrets\gemini_api_key.txt`

## Social API Scripts (this repo)
See `social_apis/` — PowerShell 5.1 scripts for YouTube, Meta, TikTok.
Each script reads credentials from `C:\Users\JAP\.h4yf_secrets\`.
