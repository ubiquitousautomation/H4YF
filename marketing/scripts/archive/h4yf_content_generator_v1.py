#!/usr/bin/env python3
"""
heat4yafeat — Weekly Content Calendar Generator
Generates a week\'s worth of cross-platform content based on
upcoming releases, current inventory, and content series schedule.
Usage: python3 h4yf_content_generator.py
"""

from datetime import datetime, date, timedelta
import json

# ── RELEASE CALENDAR 2026 (key dates) ──
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
    "Sold this in 24 hours — here\'s why 👀 {shoe}",
    "The rarest {brand} you\'ve probably never heard of",
]

TIKTOK_HOOKS = {
    "Kobe": "This Kobe almost no one knows about 🐍 #{shoe_tag} #kobe #sneakers #heat4yafeat",
    "Air Jordan": "Would you cop this Jordan for ${price}? 👀 #{shoe_tag} #jordan #sneakers",
    "LeBron": "Rarest LeBron colorway explained 👑 #{shoe_tag} #lebron #sneakers",
    "Nike Collab": "The story behind this collab will change your mind 🤝 #{shoe_tag} #nike",
    "Default": "🔥 Just listed: {shoe} — ${price}. Cop or pass? #{shoe_tag} #sneakers #heat4yafeat",
}

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
            print(f"  {r['date']}: {r['shoe']} (${r['price']}){note}")
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        date_str = current_date.strftime("%b %d")
        
        # Check for release on this day
        day_release = None
        for r in RELEASE_CALENDAR:
            if r["date"] == current_date.strftime("%Y-%m-%d"):
                day_release = r
                break
        
        plan = {
            "date": date_str,
            "day": day_name,
            "release": day_release,
            "actions": []
        }
        
        # Long-form video days
        if day_name == "Tuesday":
            series = CONTENT_SERIES["tuesday"]
            plan["youtube_longform"] = f"{series} — [select from current inventory]"
            plan["actions"].append("FILM long-form video")
            plan["actions"].append("UPLOAD to YouTube at 10am ET")
            plan["actions"].append("SHARE in both Facebook groups within 1 hour")
        elif day_name == "Friday":
            series = CONTENT_SERIES["friday"]
            plan["youtube_longform"] = f"{series} — [select from current inventory]"
            plan["actions"].append("UPLOAD long-form video at 10am ET")
        
        # Release day actions
        if day_release:
            plan["actions"].insert(0, f"🔴 RELEASE DAY: {day_release['shoe']} at ${day_release['price']}")
            plan["actions"].append(f"POST drop day Short within 2 hours of release")
            plan["actions"].append(f"POST in Facebook groups: 'Cop or Skip? {day_release['shoe']}'")
            
            cat = day_release.get("category", "Default")
            shoe_tag = day_release["shoe"].replace(" ", "").replace("'", "").replace("/", "")
            tiktok_template = TIKTOK_HOOKS.get(cat, TIKTOK_HOOKS["Default"])
            plan["tiktok_caption"] = tiktok_template.format(
                shoe=day_release["shoe"],
                shoe_tag=shoe_tag,
                price=day_release["price"],
                brand=cat
            )
        
        # Daily shorts (every day)
        plan["daily_short"] = "Post 1 Short: clip from existing video OR new listing Short"
        plan["instagram_story"] = "@b2ill2323 Story: current inventory + heat4yafeat.com link"
        
        # Whatnot
        if day_name == "Wednesday":
            plan["actions"].append("WHATNOT: Heaters On Heaters live show tonight")
            plan["actions"].append("ANNOUNCE show in Facebook groups this morning")
        if day_name == "Thursday":
            plan["actions"].append("WHATNOT RECAP: Upload 48hr recap video to YouTube")
        
        week_plan[day_name] = plan
        
        # Print day
        print(f"\n{'─'*50}")
        print(f"  {day_name.upper()}, {date_str}")
        print(f"{'─'*50}")
        
        if day_release:
            note = f" ← {day_release.get('note', '')}" if day_release.get('note') else ""
            print(f"  🚨 RELEASE: {day_release['shoe']} ${day_release['price']}{note}")
        
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

def generate_listing_short_script(shoe_name, price, story_hook, sku):
    """
    Generates a 30-45 second Short script for a new listing.
    """
    script = f"""
=== SHORT SCRIPT: {shoe_name} ===
Duration: 30–45 seconds | Format: Vertical (9:16) | No cuts needed

[0:00–0:03] HOOK (on screen text + voiceover):
  TEXT OVERLAY: "Would you cop this?"
  VO: "This {shoe_name} just dropped on heat4yafeat.com —"

[0:03–0:15] THE SHOE:
  Show shoe from all angles while talking
  VO: "{story_hook}"
  TEXT OVERLAY: "{shoe_name}"

[0:15–0:25] THE PRICE:
  Show price tag or announce verbally
  VO: "Listed at ${price}. Authenticated. Ships tomorrow."
  TEXT OVERLAY: "${price} | Authenticated | Size 12"

[0:25–0:35] CTA:
  VO: "Link in bio — heat4yafeat.com — or search {sku} on eBay."
  TEXT OVERLAY: "heat4yafeat.com | @HEAT4YAFEAT"
  
[0:35–0:45] CLOSE:
  Show shoe one more time
  VO: "Subscribe for more heat every week."
  TEXT OVERLAY: "SUBSCRIBE 🔥"

=== POST WITH ===
TikTok: "Would you cop this? {shoe_name} — ${price} ⬇️ #sneakers #heat4yafeat #jordan"
YouTube Shorts: "Would you cop this? {shoe_name} — heat4yafeat #sneakers"
IG Reels (@h4yf16): same as TikTok
@b2ill2323 Story: shoe photo + "just listed — heat4yafeat.com"
"""
    return script

if __name__ == "__main__":
    print("\nheat4yafeat — Content Generator")
    print("1. Generate this week\'s content plan")
    print("2. Generate Short script for a listing")
    print("3. Show upcoming release calendar")
    print("4. Exit")
    
    choice = input("\nSelect (1-4): ").strip()
    
    if choice == "1":
        generate_week_plan()
    elif choice == "2":
        shoe = input("Shoe name: ").strip()
        price = input("Price ($): ").strip()
        hook = input("Story hook (1 sentence): ").strip()
        sku = input("SKU (e.g. H4YF-005): ").strip()
        print(generate_listing_short_script(shoe, price, hook, sku))
    elif choice == "3":
        print("\nUpcoming Releases (next 60 days):")
        releases = get_upcoming_releases(60)
        if releases:
            for r in releases:
                note = f" ← {r['note']}" if r.get('note') else ""
                print(f"  {r['date']} ({r['days_until']}d): {r['shoe']} ${r['price']}{note}")
        else:
            print("  No releases found in next 60 days (check RELEASE_CALENDAR dict)")
    else:
        print("Exiting.")
