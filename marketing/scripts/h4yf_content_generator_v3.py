#!/usr/bin/env python3
"""
heat4yafeat — Content Generator (v3)
Generates cross-platform content — weekly plans and per-platform post/caption
scripts — based on upcoming releases, current inventory, and each platform's
Content Guide (see 05 — CONTENT & CONTENT CALENDAR / platform subfolders).

v3 CHANGE LOG (2026-07-25):
  - Audited the Drive automation library: this was the only content-generation
    script that existed. It had real logic for YouTube, TikTok, Facebook, and
    Instagram, but NO generator for Depop or Discord, and Facebook/Whatnot only
    had inline action strings rather than real post/caption generators. This
    version adds all four:
      generate_depop_listing()      -- new
      generate_discord_announcement() -- new
      generate_facebook_post()      -- promoted from inline string to a real generator
      generate_whatnot_preshow() / generate_whatnot_postshow() -- new
  - Carries forward everything from v2: every CTA that names a specific shoe
    links to that shoe's PDP (heat4yafeat.com/product/[slug]), never the bare
    heat4yafeat.com homepage. See PLATFORM_LINK_RULES.

Usage: python3 h4yf_content_generator_v3.py
"""

from datetime import datetime, date, timedelta
import json
import re

BRAND_ROOT = "https://heat4yafeat.com"

# ── RELEASE CALENDAR 2026 (key dates) ──
# "slug" is optional — auto-derived from the shoe name via slugify() if omitted.
RELEASE_CALENDAR = [
    {"date": "2026-06-06", "shoe": "AJ15 OG Black Muslin", "price": 255, "category": "Air Jordan"},
    {"date": "2026-06-06", "shoe": "AJ1 Low OG Pine Green", "price": 150, "category": "Air Jordan"},
    {"date": "2026-06-13", "shoe": "AJ3 OG Bin 23", "price": 355, "category": "Air Jordan", "note": "LIMITED — 2,300 pairs"},
    {"date": "2026-06-20", "shoe": "AJ13 Flint 2026", "price": 215, "category": "Air Jordan", "note": "CLIENT SOLD 2020 VERSION"},
    {"date": "2026-06-27", "shoe": "JAIDE x AJ11 Low", "price": 205, "category": "Air Jordan Collab"},
    {"date": "2026-07-01", "shoe": "LeBron 23 Hardwood Classic", "price": 210, "category": "LeBron"},
    {"date": "2026-07-01", "shoe": "Nike Kobe 3 Atomic Pink", "price": 190, "category": "Kobe"},
    {"date": "2026-07-10", "shoe": "AJ4 Birds of Paradise W", "price": 220, "category": "Air Jordan"},
    {"date": "2026-07-16", "shoe": "AJ41 Metallic Silver", "price": 205, "category": "Air Jordan"},
    {"date": "2026-07-17", "shoe": "Free The Youth x AJ16", "price": 250, "category": "Air Jordan Collab"},
    {"date": "2026-07-18", "shoe": "AJ5 Black/University Blue", "price": 215, "category": "Air Jordan"},
    {"date": "2026-07-24", "shoe": "Foamposite Pro Glow", "price": 250, "category": "Nike"},
    {"date": "2026-07-25", "shoe": "AJ4 Comic", "price": 220, "category": "Air Jordan"},
    {"date": "2026-08-06", "shoe": "AJ1 Low OG Laser", "price": 145, "category": "Air Jordan"},
    {"date": "2026-08-08", "shoe": "Nike Kobe 8 Protro Mambacurial", "price": 200, "category": "Kobe",
     "note": "HIGHEST CONTENT OPPORTUNITY — Kobe content is #1 TikTok niche"},
]

# ── CONTENT SERIES ROTATION ──
CONTENT_SERIES = {
    "tuesday": "Story Behind The Shoe",  # Long-form editorial
    "friday": "The Real Price",           # P&L transparency OR Resell University
}

SHORTS_HOOKS = [
    "Would you cop this? {shoe} — price reveal ⬇️",
    "I paid $X, sold for $Y on this {shoe} 👟",
    "This is why the {shoe} is priced at ${price} #sneakers",
    "Rate this pickup 1-10 👇 {shoe}",
    "Sold this in 24 hours — here's why 👀 {shoe}",
    "The rarest {brand} you've probably never heard of",
]

TIKTOK_HOOKS = {
    "Kobe": "This Kobe almost no one knows about 🐍 #{shoe_tag} #kobe #sneakers #heat4yafeat",
    "Air Jordan": "Would you cop this Jordan for ${price}? 👀 #{shoe_tag} #jordan #sneakers",
    "LeBron": "Rarest LeBron colorway explained 👑 #{shoe_tag} #lebron #sneakers",
    "Nike Collab": "The story behind this collab will change your mind 🤝 #{shoe_tag} #nike",
    "Default": "🔥 Just listed: {shoe} — ${price}. Cop or pass? #{shoe_tag} #sneakers #heat4yafeat",
}

# Depop condition tags — see HEAT4YAFEAT_Depop_Content_Guide
DEPOP_CONDITIONS = ["DS", "VNDS", "Used-Good", "Used-Fair"]

# ── PLATFORM-SPECIFIC SOCIAL SELLING RULES ──
# Mirrors the "Social Selling Strategy" section in every Content Guide doc.
# link_scope: "pdp"      = always link the specific shoe's PDP when one is named.
#             "bio"      = platform can't carry a clickable in-caption link; push PDP via bio/link-in-bio hub instead.
#             "checkout" = platform's own listing/checkout IS the point of sale; no external link needed mid-flow.
PLATFORM_LINK_RULES = {
    "YouTube": {"link_scope": "pdp", "note": "First line of every video description is the featured shoe's PDP link, not the homepage."},
    "TikTok": {"link_scope": "bio", "note": "Link-in-bio hub's top slot is the current featured shoe's PDP; pinned comment adds the direct PDP link."},
    "Instagram": {"link_scope": "bio", "note": "Bio link stack leads with the current featured shoe's PDP; Shopping tags resolve to the exact PDP."},
    "Facebook": {"link_scope": "pdp", "note": "Group posts and Shop tags include the direct PDP link, not just heat4yafeat.com."},
    "Depop": {"link_scope": "checkout", "note": "The Depop listing itself is the point of sale; cross-posted promo content still links out to the PDP."},
    "Whatnot": {"link_scope": "checkout", "note": "The live show checkout is the point of sale; pre/post-show promo content links to the PDP when relevant."},
    "Discord": {"link_scope": "pdp", "note": "#announcements and #cop-or-skip link to the PDP; #partner-spots is the one exception (links to Trusted Partners page)."},
}


def slugify(shoe_name):
    """Converts a shoe name into a PDP-safe slug, e.g. 'AJ13 Flint 2026' -> 'aj13-flint-2026'."""
    slug = shoe_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def pdp_url(release):
    """
    Returns the canonical PDP link for a release dict.
    Uses the explicit "slug" field if present, otherwise derives one from the shoe name.
    """
    slug = release.get("slug") or slugify(release["shoe"])
    return f"{BRAND_ROOT}/product/{slug}"


def get_upcoming_releases(days_ahead=14):
    """Returns releases in the next N days."""
    today = date.today()
    upcoming = []
    for release in RELEASE_CALENDAR:
        release_date = datetime.strptime(release["date"], "%Y-%m-%d").date()
        days_until = (release_date - today).days
        if 0 <= days_until <= days_ahead:
            release["days_until"] = days_until
            upcoming.append(release)
    return sorted(upcoming, key=lambda x: x["days_until"])


def generate_week_plan(start_date=None):
    """
    Generates a complete 7-day content plan across all platforms.
    All shoe-specific CTAs route to that shoe's PDP (see pdp_url()).
    """
    if start_date is None:
        start_date = date.today()

    week_plan = {}
    upcoming = get_upcoming_releases(days_ahead=14)

    print(f"\n{'='*65}")
    print(f"heat4yafeat — Weekly Content Plan")
    print(f"Week of: {start_date.strftime('%B %d, %Y')}")
    print(f"{'='*65}")

    if upcoming:
        print(f"\n⚡ UPCOMING RELEASES THIS PERIOD:")
        for r in upcoming[:5]:
            note = f" — {r['note']}" if r.get('note') else ""
            print(f"  {r['date']}: {r['shoe']} (${r['price']}){note} → {pdp_url(r)}")

    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        date_str = current_date.strftime("%b %d")

        day_release = None
        for r in RELEASE_CALENDAR:
            if r["date"] == current_date.strftime("%Y-%m-%d"):
                day_release = r
                break

        plan = {"date": date_str, "day": day_name, "release": day_release, "actions": []}

        if day_name == "Tuesday":
            series = CONTENT_SERIES["tuesday"]
            plan["youtube_longform"] = f"{series} — [select from current inventory]"
            plan["actions"].append("FILM long-form video")
            plan["actions"].append("UPLOAD to YouTube at 10am ET — description's first link = featured shoe's PDP")
            plan["actions"].append("SHARE in both Facebook groups within 1 hour")
        elif day_name == "Friday":
            series = CONTENT_SERIES["friday"]
            plan["youtube_longform"] = f"{series} — [select from current inventory]"
            plan["actions"].append("UPLOAD long-form video at 10am ET — description's first link = featured shoe's PDP")
            plan["actions"].append("DEPOP: Friday Restock — 5+ listings live same day (see generate_depop_listing per pair)")

        if day_release:
            pdp = pdp_url(day_release)
            plan["actions"].insert(0, f"🔴 RELEASE DAY: {day_release['shoe']} at ${day_release['price']} — PDP: {pdp}")
            plan["actions"].append(f"POST drop day Short within 2 hours of release — caption CTA links to {pdp}")
            plan["actions"].append(f"POST in Facebook groups: 'Cop or Skip? {day_release['shoe']}' — include {pdp}")
            plan["actions"].append(f"UPDATE bio link-in-bio hub top slot to {pdp} for the day")
            plan["actions"].append(f"POST to Discord #announcements — {pdp}")

            cat = day_release.get("category", "Default")
            shoe_tag = day_release["shoe"].replace(" ", "").replace("'", "").replace("/", "")
            tiktok_template = TIKTOK_HOOKS.get(cat, TIKTOK_HOOKS["Default"])
            plan["tiktok_caption"] = tiktok_template.format(
                shoe=day_release["shoe"], shoe_tag=shoe_tag, price=day_release["price"], brand=cat
            )
            plan["pdp_url"] = pdp

        plan["daily_short"] = "Post 1 Short: clip from existing video OR new listing Short"
        plan["instagram_story"] = "@b2ill2323 Story: current inventory + featured shoe's PDP link (not heat4yafeat.com root)"

        if day_name == "Wednesday":
            plan["actions"].append("WHATNOT: Heaters On Heaters live show tonight (see generate_whatnot_preshow)")
            plan["actions"].append("ANNOUNCE show in Facebook groups this morning")
        if day_name == "Thursday":
            plan["actions"].append("WHATNOT RECAP: Upload 48hr recap video to YouTube (see generate_whatnot_postshow)")

        week_plan[day_name] = plan

        print(f"\n{'─'*50}")
        print(f"  {day_name.upper()}, {date_str}")
        print(f"{'─'*50}")
        if day_release:
            note = f" ← {day_release.get('note', '')}" if day_release.get('note') else ""
            print(f"  🚨 RELEASE: {day_release['shoe']} ${day_release['price']}{note}")
            print(f"  🔗 PDP: {plan['pdp_url']}")
        if plan.get("youtube_longform"):
            print(f"  📺 YouTube: {plan['youtube_longform']}")
        print(f"  📱 Short: {plan['daily_short']}")
        print(f"  📸 Stories: {plan['instagram_story']}")
        if plan.get("tiktok_caption"):
            print(f"  🎵 TikTok: {plan['tiktok_caption'][:80]}...")
        for action in plan["actions"]:
            print(f"  ✓ {action}")

    print(f"\n{'='*65}")
    print("Weekly plan generated. Update Content Calendar tab in tracker.")
    print(f"{'='*65}\n")
    return week_plan


def generate_listing_short_script(shoe_name, price, story_hook, sku, slug=None):
    """Generates a 30-45 second Short script for a new listing (YouTube/TikTok/IG)."""
    pdp = pdp_url({"shoe": shoe_name, "slug": slug})
    script = f"""
=== SHORT SCRIPT: {shoe_name} ===
Duration: 30–45 seconds | Format: Vertical (9:16) | No cuts needed
PDP: {pdp}

[0:00–0:03] HOOK (on screen text + voiceover):
  TEXT OVERLAY: "Would you cop this?"
  VO: "This {shoe_name} just dropped —"

[0:03–0:15] THE SHOE:
  Show shoe from all angles while talking
  VO: "{story_hook}"
  TEXT OVERLAY: "{shoe_name}"

[0:15–0:25] THE PRICE:
  Show price tag or announce verbally
  VO: "Listed at ${price}. Authenticated. Ships tomorrow."
  TEXT OVERLAY: "${price} | Authenticated | Size 12"

[0:25–0:35] CTA:
  VO: "Link in bio — full details and photos on the product page — or search {sku} on eBay."
  TEXT OVERLAY: "See it up close: {pdp}"

[0:35–0:45] CLOSE:
  Show shoe one more time
  VO: "Subscribe for more heat every week."
  TEXT OVERLAY: "SUBSCRIBE 🔥"

=== POST WITH ===
TikTok: "Would you cop this? {shoe_name} — ${price} ⬇️ #sneakers #heat4yafeat #jordan" (bio link hub top slot → {pdp})
YouTube Shorts: "Would you cop this? {shoe_name} — heat4yafeat #sneakers" (description first line → {pdp})
IG Reels (@h4yf16): same as TikTok (bio link stack top slot → {pdp})
@b2ill2323 Story: shoe photo + "just listed" + PDP sticker link → {pdp}
Facebook Groups: include direct PDP link {pdp}, not just heat4yafeat.com
Discord #announcements: {pdp}

Reminder: heat4yafeat.com (bare root) is for channel bios / "about us" contexts only.
Any CTA naming this specific shoe uses the PDP link above.
"""
    return script


def generate_depop_listing(shoe_name, price, condition, size, story_fact, flaw_note=None, slug=None):
    """
    NEW in v3. Generates a Depop listing title + description per the Depop Content Guide
    (Type 1 — Listing Photoset) and its title formula. Depop's own listing page is the
    checkout — the PDP link only shows up in cross-posted promo content, not the listing itself.
    """
    if condition not in DEPOP_CONDITIONS:
        raise ValueError(f"condition must be one of {DEPOP_CONDITIONS}")

    flaw_line = flaw_note if flaw_note else "No flaws noted."
    pdp = pdp_url({"shoe": shoe_name, "slug": slug})

    title = f'{shoe_name} Size {size} — {condition}'
    description = (
        f'{shoe_name} Size {size}. Condition: {condition}. {flaw_line} '
        f'{story_fact} Ships in 1–2 days. Bundle & save — check out our other H4YF heat 🔥 '
        f'#sneakers #{slugify(shoe_name).replace("-", "")} #heat4yafeat #depop'
    )

    output = f"""
=== DEPOP LISTING: {shoe_name} ===
Photoset checklist (4–6 photos): hero shot / tongue / sole / heel tab / size tag / box label
                                  + 1 optional styled/on-foot shot

TITLE: {title}

DESCRIPTION:
{description}

PRICE: List at ${round(price * 1.12)} (10–15% above target ${price} to leave Offers negotiation room)

CROSS-POST NOTE: this listing's own page is the checkout — no external link needed in the
Depop listing itself. If this pair is cross-posted (IG Story, TikTok caption, insert card QR),
that cross-post links to {pdp}.
"""
    return output


def generate_discord_announcement(shoe_name, price, channel="#announcements", slug=None, note=None):
    """
    NEW in v3. Generates a Discord post for #announcements (new listings, YouTube drops,
    Whatnot show dates) or #cop-or-skip (drop day discussion). Per the Discord Content Guide,
    every #announcements / #cop-or-skip post links to the specific PDP.
    """
    pdp = pdp_url({"shoe": shoe_name, "slug": slug})
    extra = f"\n{note}" if note else ""
    message = (
        f"🔥 **New heat just dropped: {shoe_name}** — ${price}\n"
        f"Full details, photos, and buy link: {pdp}{extra}"
    )
    return f"""
=== DISCORD POST ({channel}) ===
{message}

Reminder: #partner-spots is the one Discord channel that does NOT use a PDP link —
it routes to the Trusted Partners page (Campbell's Barbershop) instead.
"""


def generate_facebook_post(shoe_name, price, story_hook, sku, group="Indiana Sneaker Heads", slug=None):
    """
    Promoted from an inline action string (v1/v2) to a real generator in v3.
    Matches the Facebook Content Guide's Group Post Formula.
    """
    pdp = pdp_url({"shoe": shoe_name, "slug": slug})
    post = (
        f"Just listed this {shoe_name} — ${price}. {story_hook} "
        f"Full story in the YouTube video: [link]. See it up close: {pdp}\n"
        f"heat4yafeat ships nationwide from Indianapolis. eBay: ebay.com/str/h4yf"
    )
    return f"""
=== FACEBOOK GROUP POST ({group}) ===
[Shoe photo]
"{post}"

Cadence: post to Group 1 (Indiana Sneaker Heads) first; Group 2 follows, slightly delayed.
Product tag (if Facebook Shop is connected) must resolve to {pdp}, not the shop root.
"""


def generate_whatnot_preshow(show_time, pairs_count, whatnot_link, featured_pairs=None):
    """
    NEW in v3. Generates the 24-hours-before pre-show promo per the Whatnot Content Guide
    Pre-Show Checklist. Featured pairs (if already listed elsewhere) get their PDP link
    included so buyers who can't make the live show can still convert.
    """
    fb_post = f"Going live on Whatnot — {show_time}. Dropping {pairs_count} pairs. Link: {whatnot_link}"
    featured_lines = ""
    if featured_pairs:
        lines = []
        for pair in featured_pairs:
            pdp = pdp_url(pair)
            lines.append(f"  - {pair['shoe']}: {pdp}")
        featured_lines = "\nCan't make the show? Some pairs are also up now:\n" + "\n".join(lines)

    return f"""
=== WHATNOT PRE-SHOW (post 24 hours before) ===
Facebook Groups (both): "{fb_post}"{featured_lines}
@h4yf16 Story: countdown sticker + preview
@b2ill2323 Story: personal angle
Master Catalog: mark all show inventory "Whatnot — Pending" in the Platform column
"""


def generate_whatnot_postshow(sold_count, clip_note, restocked_pairs=None):
    """
    NEW in v3. Generates the within-24-hours post-show recap per the Whatnot Content Guide.
    If a sold pair has a similar/restocked pair available, links to that PDP; otherwise
    points to the next show.
    """
    restock_lines = ""
    if restocked_pairs:
        lines = []
        for pair in restocked_pairs:
            pdp = pdp_url(pair)
            lines.append(f"  - {pair['shoe']} restocked / similar available: {pdp}")
        restock_lines = "\n" + "\n".join(lines)

    return f"""
=== WHATNOT POST-SHOW (within 24 hours) ===
Sold {sold_count} pairs last night 🔥
Clip: {clip_note} → push to YouTube Short → TikTok → Instagram Reel
Update Master Catalog: mark sold items, update Platform columns
Post sold recap to both Facebook Groups + Stories + Discord #sold-gallery{restock_lines}
"""


def show_platform_link_rules():
    """Prints the Social Selling Strategy link rules for every platform."""
    print("\nheat4yafeat — Social Selling / PDP Link Rules by Platform")
    print(f"{'='*65}")
    for platform, rule in PLATFORM_LINK_RULES.items():
        print(f"\n{platform} (scope: {rule['link_scope']}):")
        print(f"  {rule['note']}")
    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    print("\nheat4yafeat — Content Generator (v3)")
    print("1. Generate this week's content plan")
    print("2. Generate Short script for a listing (YouTube/TikTok/IG)")
    print("3. Show upcoming release calendar")
    print("4. Show Social Selling / PDP link rules by platform")
    print("5. Generate Depop listing")
    print("6. Generate Discord announcement")
    print("7. Generate Facebook group post")
    print("8. Generate Whatnot pre-show promo")
    print("9. Generate Whatnot post-show recap")
    print("10. Exit")

    choice = input("\nSelect (1-10): ").strip()

    if choice == "1":
        generate_week_plan()
    elif choice == "2":
        shoe = input("Shoe name: ").strip()
        price = input("Price ($): ").strip()
        hook = input("Story hook (1 sentence): ").strip()
        sku = input("SKU (e.g. H4YF-005): ").strip()
        slug = input("PDP slug (leave blank to auto-generate from shoe name): ").strip() or None
        print(generate_listing_short_script(shoe, price, hook, sku, slug))
    elif choice == "3":
        print("\nUpcoming Releases (next 60 days):")
        releases = get_upcoming_releases(60)
        if releases:
            for r in releases:
                note = f" ← {r['note']}" if r.get('note') else ""
                print(f"  {r['date']} ({r['days_until']}d): {r['shoe']} ${r['price']}{note} → {pdp_url(r)}")
        else:
            print("  No releases found in next 60 days (check RELEASE_CALENDAR dict)")
    elif choice == "4":
        show_platform_link_rules()
    elif choice == "5":
        shoe = input("Shoe name: ").strip()
        price = float(input("Target price ($): ").strip())
        print(f"Condition options: {DEPOP_CONDITIONS}")
        condition = input("Condition: ").strip()
        size = input("US size: ").strip()
        fact = input("One compelling fact about the shoe: ").strip()
        flaw = input("Flaw disclosure (blank = 'No flaws noted.'): ").strip() or None
        slug = input("PDP slug (leave blank to auto-generate): ").strip() or None
        print(generate_depop_listing(shoe, price, condition, size, fact, flaw, slug))
    elif choice == "6":
        shoe = input("Shoe name: ").strip()
        price = input("Price ($): ").strip()
        channel = input("Channel (#announcements / #cop-or-skip) [default #announcements]: ").strip() or "#announcements"
        slug = input("PDP slug (leave blank to auto-generate): ").strip() or None
        print(generate_discord_announcement(shoe, price, channel, slug))
    elif choice == "7":
        shoe = input("Shoe name: ").strip()
        price = input("Price ($): ").strip()
        hook = input("Story hook (2 sentences): ").strip()
        sku = input("SKU: ").strip()
        group = input("Group (default: Indiana Sneaker Heads): ").strip() or "Indiana Sneaker Heads"
        slug = input("PDP slug (leave blank to auto-generate): ").strip() or None
        print(generate_facebook_post(shoe, price, hook, sku, group, slug))
    elif choice == "8":
        show_time = input("Show time (e.g. 'Wed 8pm ET'): ").strip()
        pairs_count = input("Number of pairs dropping: ").strip()
        whatnot_link = input("Whatnot show link: ").strip()
        print(generate_whatnot_preshow(show_time, pairs_count, whatnot_link))
    elif choice == "9":
        sold_count = input("Pairs sold: ").strip()
        clip_note = input("Best clip description: ").strip()
        print(generate_whatnot_postshow(sold_count, clip_note))
    else:
        print("Exiting.")
