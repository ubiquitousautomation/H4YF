# H4YF Marketing — Content Guides & Automation

Cross-platform content strategy and the script that generates day-to-day
posting content from it. Source of truth for platform strategy still lives
in Google Drive (`🔥HEAT4YAFEAT — Client Operating Center/05 — CONTENT &
CONTENT CALENDAR/`); this directory is the git-tracked, versioned mirror
that the automation script and any future CI/deploy step actually reads.

## Layout

```
marketing/
├── content-guides/          Per-platform strategy docs (.docx), PHASE-based template
│   ├── HEAT4YAFEAT_Depop_Content_Guide_v2.docx
│   ├── HEAT4YAFEAT_YouTube_Content_Guide_v2.docx
│   ├── HEAT4YAFEAT_Facebook_Content_Guide_v2.docx
│   ├── HEAT4YAFEAT_TikTok_Content_Guide_v2.docx
│   ├── HEAT4YAFEAT_Whatnot_Content_Guide_v2.docx
│   ├── HEAT4YAFEAT_Discord_Content_Guide_v2.docx
│   └── HEAT4YAFEAT_Campbells_Barbershop_OnePager_v1.docx
├── content-calendar/
│   └── HEAT4YAFEAT_Depop_Content_Calendar.xlsx   4-tab workbook: Weekly Calendar,
│       Cross-Platform Schedule, YouTube Schedule, Content Pillars, Monthly Overview
└── scripts/
    ├── h4yf_content_generator_v3.py    Canonical, current generator — run this one
    └── archive/                        Superseded versions, kept for change history
        ├── h4yf_content_generator_v1.py
        └── h4yf_content_generator_v2.py
```

## Instagram — where it actually lives

Instagram was the one Tier-1 channel with no guide in this folder, which
consistently made it the thinnest-covered channel in the whole library. That
gap is now closed, but **not here** — the canonical Instagram playbook lives in
the site repo:

> **`ubiquitousautomation/ubiq-h4yf-skin` → `docs/INSTAGRAM_PLAYBOOK.md`**

It sits there rather than in this folder because Instagram is wired into the
automated content pipeline (generation → queue → staged bundle → attribution),
and that pipeline lives in the skin repo. Keeping the playbook next to the code
that reads it prevents the two from drifting.

The original Drive source (`HEAT4YAFEAT_Instagram_Content_Guide — @h4yf16 &
@b2ill2323 Strategy [v2 CORRECTED]`, Drive ID
`16-LY_U2Sd0mWcTdu3-54Kq2aarmvxq-rI4__POKkVKA`) is superseded by it. The Drive
doc predates the brand-handle decision below and describes a two-account
architecture that is now three.

### The brand handle: `@heat4yafeatpresents`

The IG account architecture is now three handles with three distinct jobs:

| Handle | Role | Automation |
|---|---|---|
| **`@heat4yafeatpresents`** | **Brand-primary — product, drops, authentication** | Assisted |
| `@h4yf16` | Legacy handle. Keep, redirect, taper | Assisted |
| `@b2ill2323` | Founder. Billy's face and voice | **Never automate** |

`heat4yafeatpresents` is not a new brand voice — it is the one already in use.
Every one of the 449 eBay product descriptions in SEO Sheet Tab 3 opens with
the literal string **`HEAT4YAFEAT PRESENTS:`**, and the YouTube title
convention follows it (`heat4yafeat presents Air Jordan 4 'University Blue' —
Worth $200 in 2026?`). The handle makes a signature that already exists
addressable. It also reads as curation rather than inventory (matching the
curator-not-reseller positioning), and it is far more defensible against the
`heat4yafeet` / `HEATFORYAFEET` impersonator cluster than any short form.

**Seeding is unstarted and blocking** — claim the handle before promoting
anything to it. Full sequence in the playbook §1.2.

### Instagram in the content flywheel

Instagram consumes the same asset pyramid as every other channel — one filmed
authentication session feeds YouTube long-form, a Short, TikTok, an IG Reel,
and IG Stories. The only IG-specific work is the hashtag set and the Story
frames; **no bespoke shooting.**

One constraint worth knowing before planning anything: Instagram cannot be
posted to programmatically today (Meta App Review), and **Stories can never be
— there is no publish endpoint for them at all.** Since the IG cadence is
Story-heavy by design, plan for permanent partial manual work on this channel.
The pipeline still generates the caption, crops the image, stamps the UTM, and
stages a ready-to-post bundle; the human step is paste-and-tap, not write.

## Content Guide template

Every guide (except the Campbell's one-pager, which is a standalone
reference) follows the same shape so they diff and skim consistently:

- Title block: platform, handle(s), version, source
- `PHASE 1..N` sections: one-time setup → content calendar/cadence →
  cross-platform ties → engagement protocol → KPI dashboard
- A **Social Selling Strategy** section (added in v2 across the board) —
  see "PDP-first linking" below
- A **Change Log** table at the bottom — bump the version there whenever
  you edit a guide, don't just overwrite silently

## PDP-first linking (the rule baked into v2)

`heat4yafeat.com` — the bare root — is for channel bios and "about us"
contexts only. **Any CTA that names a specific shoe links to that shoe's
Product Detail Page**: `heat4yafeat.com/product/[shoe-slug]`, never the
homepage or a category page.

Because platforms differ in what they let you link, each Content Guide
documents one of three link scopes for that platform (also encoded in
`PLATFORM_LINK_RULES` in the script):

| Scope | Meaning | Platforms |
|---|---|---|
| `pdp` | Caption/description/post can carry a direct link — always the PDP | YouTube, Facebook, Discord |
| `bio` | No clickable in-caption link — the bio / link-in-bio hub's top slot carries the PDP instead | TikTok, Instagram |
| `checkout` | The platform's own listing/live-show *is* the point of sale — PDP only matters for cross-posted promo, not the platform itself | Depop, Whatnot |

## Automation script

`scripts/h4yf_content_generator_v3.py` is a stdlib-only Python 3 CLI (no
install step) that generates:

1. A 7-day cross-platform content plan from `RELEASE_CALENDAR`
2. A YouTube/TikTok/IG Short script for a listing
3. A Depop listing (title + description + Offers-margin pricing)
4. A Discord `#announcements` / `#cop-or-skip` post
5. A Facebook Group post
6. A Whatnot pre-show promo and post-show recap

Every generated CTA that names a shoe resolves its PDP link via
`pdp_url()`, which either uses an explicit `slug` on the release entry or
derives one from the shoe name with `slugify()`.

```bash
python3 marketing/scripts/h4yf_content_generator_v3.py
```

To add a new release/drop: add an entry to `RELEASE_CALENDAR` at the top
of the script (date, shoe, price, category, optional slug/note).

### Version history

- **v1** — original weekly plan + YouTube/TikTok generators only.
- **v2** — added `pdp_url()`/`slugify()`; every CTA routes to the specific
  product PDP instead of the bare homepage.
- **v3** (current) — added the previously-missing platform generators:
  `generate_depop_listing()`, `generate_discord_announcement()`,
  `generate_facebook_post()` (promoted from an inline string),
  `generate_whatnot_preshow()` / `generate_whatnot_postshow()`.

Superseded versions are kept under `scripts/archive/` for change history —
don't run those, they're missing platform coverage and the PDP-link rule.

## CI

`.github/workflows/ci.yml` runs on every push/PR:

- Syntax-checks every script in `marketing/scripts/` (`python3 -m py_compile`)
- Smoke-tests `h4yf_content_generator_v3.py` actually runs without error
- Shellchecks `scripts/drive-sync.sh` and `scripts/setup-drive.sh`

This is intentionally minimal — there's no build/deploy step yet (see below).
It exists to catch a broken script before it merges, not to gate a release.

## Deployment path (future)

Nothing here runs automatically beyond the CI checks above. When ready to
operationalize further:

1. **Slug source of truth** — `slugify()` currently derives slugs from the
   shoe name. Once the WooCommerce product catalog is live, swap this for
   a real lookup (product SKU → PDP slug) so generated links never 404.
2. **Release calendar as data, not code** — move `RELEASE_CALENDAR` out of
   the script and into the inventory/catalog source (the Master Catalog
   sheet or WooCommerce export) so new drops don't require editing Python.
3. **Scheduled run** — wire `generate_week_plan()` into a weekly GitHub
   Action (or the existing `scripts/drive-sync.sh` cron path) that opens a
   PR with the week's plan, or posts it into `ai-context/handoff.md` for
   the next session to action.
4. **Per-platform posting** — once ready to go from *generated text* to
   *actually posted*, each `generate_*` function's output is the payload;
   wrap it with the relevant platform API (Depop/Whatnot don't have public
   posting APIs — those stay manual) rather than rewriting the copy logic.
5. **Guide sync** — these `.docx` files are point-in-time exports from
   Drive. If Drive is edited directly, re-export and bump the version here
   too — don't let the two copies drift silently.
