#!/usr/bin/env python3
"""
heat4yafeat — eBay Listing Title & Description Optimizer
Usage: python3 h4yf_ebay_optimizer.py
Outputs optimized titles, descriptions, and item specifics for new listings.
"""

import json
from datetime import datetime

# ── BRAND CONFIG ──
BRAND_CONFIG = {
    "seller": "heat4yafeat",
    "ebay_store": "https://www.ebay.com/str/h4yf",
    "youtube": "https://www.youtube.com/@HEAT4YAFEAT",
    "website": "https://www.heat4yafeat.com",
    "feedback_count": 267,
    "feedback_pct": "100%",
    "since_year": 2016,
    "city": "Indianapolis",
    "state": "IN",
    "default_size": "12",
    "shipping_policy": "Ships within 1 business day via USPS Priority Mail with tracking. FREE SHIPPING.",
    "return_policy": "30-day returns accepted. Item must be returned in same condition as received.",
    "auth_statement": "Personally authenticated by heat4yafeat — Indianapolis sneaker seller since 2016. 267 verified eBay sales. 100% positive feedback.",
}

# ── TITLE OPTIMIZER ──
def optimize_title(brand, model, colorway, year, size, condition="Pre-Owned"):
    """
    Builds a Cassini-optimized 80-character eBay title.
    Formula: Brand + Model + Colorway + Year + Gender + Size + Condition + Auth
    """
    components = [brand, model, colorway, year, "Mens", f"Sz {size}", condition, "Authentic"]
    full_title = " ".join(str(c) for c in components if c)
    
    if len(full_title) <= 80:
        return full_title, len(full_title), "OPTIMAL"
    
    # Trim if over 80 — remove least important words first
    trimmed = full_title
    removals = ["Authentic", "Pre-Owned", "Mens", f"Sz {size}", year]
    for word in removals:
        if len(trimmed) <= 80:
            break
        trimmed = trimmed.replace(f" {word}", "")
    
    return trimmed[:80], len(trimmed[:80]), "TRIMMED"

# ── DESCRIPTION GENERATOR ──
def generate_description(shoe_name, brand, year, cultural_story,
                          condition_detail, size, box_included=True,
                          photo_count=12):
    """
    Generates a full eBay listing description following the H4YF formula:
    Hook -> Authentication -> Condition -> Size/Fit -> Shipping -> Trust -> Cross-links
    """
    box_text = "Box included (may have shelf wear)." if box_included else "No box included."
    
    description = f"""HEAT4YAFEAT PRESENTS: {shoe_name}

{cultural_story}

AUTHENTICATION: {BRAND_CONFIG["auth_statement"]}

CONDITION: {condition_detail} {box_text}
All {photo_count} photos taken in natural daylight — no filters, no tricks.

SIZE: US Men\'s {size} | Fits true to size unless otherwise noted.

SHIPPING: {BRAND_CONFIG["shipping_policy"]}

RETURNS: {BRAND_CONFIG["return_policy"]}

MORE HEAT AT:
• eBay Store: {BRAND_CONFIG["ebay_store"]}
• Website: {BRAND_CONFIG["website"]}
• YouTube: {BRAND_CONFIG["youtube"]} — watch the full story on this shoe

Thank you for shopping with heat4yafeat."""
    
    return description

# ── ITEM SPECIFICS GENERATOR ──
def generate_item_specifics(brand, model, colorway, year, size, 
                             condition="Pre-Owned", gender="Men",
                             upper_material="Leather", style="Athletic",
                             authenticated_by="heat4yafeat"):
    """
    Returns complete eBay item specifics dict.
    Complete item specifics = Cassini ranking boost + Google Shopping eligibility.
    """
    return {
        "Brand": brand,
        "Style": model,
        "Color": colorway,
        "Year Manufactured": str(year),
        "US Shoe Size": str(size),
        "Gender": gender,
        "Condition": condition,
        "Upper Material": upper_material,
        "Style (category)": style,
        "Authenticated by": authenticated_by,
        "Seller Location": f"{BRAND_CONFIG['city']}, {BRAND_CONFIG['state']}",
        "Seller Feedback": f"{BRAND_CONFIG['feedback_count']} sales, {BRAND_CONFIG['feedback_pct']} positive",
    }

# ── META TAG GENERATOR ──
def generate_meta_tags(shoe_name, brand, year, size, price, condition="Pre-Owned"):
    """
    Generates SEO meta tags for heat4yafeat.com product pages.
    """
    # Title: max 60 chars
    title = f"{shoe_name} Sz{size} Auth | heat4yafeat"
    if len(title) > 60:
        title = title[:57] + "..."
    
    # Meta description: max 160 chars  
    desc = (f"Buy authenticated {shoe_name} ({year}) Size {size} from heat4yafeat — "
            f"Indianapolis reseller since 2016. 267 eBay sales. "
            f"Ships next day. Free shipping. ${price}.")
    if len(desc) > 160:
        desc = desc[:157] + "..."
    
    # Slug
    slug = shoe_name.lower().replace(" ", "-").replace("'", "").replace("/", "-")
    url = f"https://www.heat4yafeat.com/{slug}"
    
    return {
        "page_title": title,
        "meta_description": desc,
        "canonical_url": url,
        "og_title": title,
        "og_description": desc,
        "twitter_card": "summary_large_image",
        "char_counts": {
            "title": len(title),
            "description": len(desc),
            "title_status": "OK" if len(title) <= 60 else "TOO LONG",
            "desc_status": "OK" if len(desc) <= 160 else "TOO LONG",
        }
    }

# ── JSON-LD SCHEMA GENERATOR ──
def generate_product_schema(shoe_name, brand, description, sku, price,
                              availability="InStock", condition="UsedCondition"):
    """
    Generates JSON-LD Product schema. Copy output into website page <head>.
    Validated against Google Rich Results Test requirements (2026).
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": shoe_name,
        "brand": {"@type": "Brand", "name": brand},
        "description": description,
        "sku": sku,
        "offers": {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": "USD",
            "availability": f"https://schema.org/{availability}",
            "seller": {"@type": "Organization", "name": "heat4yafeat"},
            "itemCondition": f"https://schema.org/{condition}"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "5.0",
            "reviewCount": str(BRAND_CONFIG["feedback_count"]),
            "bestRating": "5"
        }
    }
    return json.dumps(schema, indent=2)

# ── YOUTUBE SEO GENERATOR ──
def generate_youtube_metadata(shoe_name, brand, year, angle, 
                               price=None, series="HEAT4YAFEAT presents"):
    """
    Generates SEO-optimized YouTube title, description template, and tags.
    Follows the H4YF formula: [Series] [Shoe] [Year] — [Compelling Hook]
    """
    # Build optimized title
    hook_options = {
        "resell": f"Worth the Resell at ${price}?" if price else "Worth the Resell?",
        "history": "Full History + Authentication",
        "comparison": "Better Than You Think",
        "story": f"The Full Story of the {shoe_name}",
        "cop": "Cop or Skip?",
    }
    hook = hook_options.get(angle, "Full Breakdown")
    title = f"{series} {shoe_name} {year} — {hook}"
    
    # Generate description template
    primary_kw = f"{brand} {shoe_name} {year} resell value"
    
    description_template = f"""[LINE 1 - KEYWORD LEAD (125 chars max)]:
I break down the {shoe_name} ({year}) — history, authentication, and whether it\'s worth buying at ${price or "market price"} in 2026.

[LINE 2 - CREDENTIALS]:
heat4yafeat | Indianapolis sneaker reseller since 2016 | 267 verified eBay sales | 100% positive feedback | Authenticated by hand.

[LINE 3 - CTA]:
Subscribe for weekly sneaker heat: https://www.youtube.com/@HEAT4YAFEAT

--- TIMESTAMPS ---
0:00 Intro
1:10 History — Where this colorway comes from
3:25 Authentication — How to spot a fake
6:40 Resell value — Current market data
9:15 Final verdict — Buy, wait, or skip?

--- LINKS ---
Shop this pair: https://www.heat4yafeat.com/[slug]
eBay store: https://www.ebay.com/str/h4yf
Indiana Sneaker Heads: https://www.facebook.com/groups/392779814221278
Instagram (Brand): https://www.instagram.com/h4yf16
Instagram (Founder): https://www.instagram.com/b2ill2323

--- HASHTAGS ---
#{brand.replace(" ", "")} #{shoe_name.replace(" ", "")} #SneakerResell #heat4yafeat #RetroSneakers"""

    # Tags
    tags = [
        shoe_name, f"{brand} {shoe_name}", f"{shoe_name} {year}",
        f"{shoe_name} resell value", f"{shoe_name} authentication",
        "sneaker resell", "heat4yafeat", "Indianapolis sneakers",
        "retro Jordan", brand, str(year), "authenticated sneakers"
    ]
    
    return {
        "optimized_title": title,
        "title_length": len(title),
        "primary_keyword": primary_kw,
        "description_template": description_template,
        "tags": tags,
        "shorts_hook": f"Would you cop this? {shoe_name} {year} — price reveal ⬇️",
        "tiktok_hook": f"This {shoe_name} sold in 24 hours 👀 here\'s why #{brand.lower().replace(' ','')} #sneakers",
        "community_post": f"New video: {shoe_name} {year} full breakdown. Drop your verdict below — buy or pass?",
    }

# ── PRICING CALCULATOR ──
def calculate_pricing(cost_paid, platform="ebay"):
    """
    Calculates recommended pricing and expected margin across platforms.
    eBay fee: 7% for Basic+ store on sneakers $150+
    Whatnot fee: ~8% + payment processing
    Website (direct): 0% platform fee (payment processing ~2.9%)
    """
    fees = {
        "ebay": 0.07,
        "whatnot": 0.08,
        "website": 0.029,
    }
    
    # Target margins
    min_margin = 0.25  # 25% minimum
    target_margin = 0.35  # 35% target
    
    fee = fees.get(platform, 0.07)
    shipping = 13.00  # average USPS Priority
    packaging = 1.50
    
    # Break-even price
    total_cost = cost_paid + shipping + packaging
    breakeven = total_cost / (1 - fee)
    
    # Recommended price points
    min_price = total_cost / (1 - fee - min_margin)
    target_price = total_cost / (1 - fee - target_margin)
    
    # Round to nearest $5 for clean pricing
    min_price_clean = round(min_price / 5) * 5
    target_price_clean = round(target_price / 5) * 5
    
    return {
        "cost_paid": cost_paid,
        "total_cost_with_fees": round(total_cost, 2),
        "platform": platform,
        "platform_fee_pct": f"{fee*100:.1f}%",
        "breakeven_price": round(breakeven, 2),
        "minimum_list_price": min_price_clean,
        "target_list_price": target_price_clean,
        "expected_profit_at_target": round(target_price_clean * (1 - fee) - total_cost, 2),
        "expected_margin_at_target": f"{round((target_price_clean * (1-fee) - total_cost) / target_price_clean * 100, 1)}%",
    }

# ── PROMOTED LISTINGS CALCULATOR ──
def calculate_promoted_rate(category, competition_level="medium"):
    """
    Returns recommended Promoted Listings ad rate based on category.
    Rule: Always match or exceed eBay's 'trending rate' for the category.
    """
    base_rates = {
        "Air Jordan 1-5": {"low": 3, "medium": 5, "high": 8},
        "Air Jordan 6-10": {"low": 3, "medium": 4, "high": 7},
        "Air Jordan 11-15": {"low": 3, "medium": 5, "high": 8},
        "Air Jordan 16+": {"low": 2, "medium": 3, "high": 5},
        "Nike Kobe": {"low": 4, "medium": 6, "high": 9},
        "Nike LeBron": {"low": 3, "medium": 5, "high": 7},
        "Nike Collab": {"low": 4, "medium": 6, "high": 8},
        "Vintage Streetwear": {"low": 3, "medium": 5, "high": 7},
        "Nike SB": {"low": 3, "medium": 4, "high": 6},
    }
    
    default = {"low": 3, "medium": 5, "high": 7}
    rates = base_rates.get(category, default)
    recommended = rates.get(competition_level, 5)
    
    return {
        "category": category,
        "competition_level": competition_level,
        "recommended_ad_rate": f"{recommended}%",
        "note": f"Set to {recommended}% in eBay Seller Hub > Advertising > Promoted Listings Standard",
        "peak_periods": "Increase +2% during: Jordan holiday drops (Dec), NBA Finals (May-Jun), Kobe anniversaries (Jan 26)",
    }

# ── STALE LISTING CHECKER ──
def check_stale_listing(days_listed, watcher_count, view_count_7d):
    """
    Determines if a listing needs intervention based on Cassini signals.
    Returns action recommendations.
    """
    actions = []
    urgency = "LOW"
    
    if days_listed >= 90:
        actions.append("END and RELIST immediately — 90-day cycle complete")
        actions.append("Update title with fresh Terapeak keywords")
        actions.append("Reduce price 5-8% on relist")
        actions.append("Activate Promoted Listings at trending rate")
        urgency = "HIGH"
    elif days_listed >= 60:
        if watcher_count >= 10:
            actions.append(f"SEND OFFER TO WATCHERS — {watcher_count} watchers, offer 5-7% off with 48hr expiry")
            urgency = "MEDIUM"
        else:
            actions.append("Reduce price 3-5%")
            actions.append("Increase Promoted Listings rate +1-2%")
            urgency = "MEDIUM"
    elif days_listed >= 30:
        if view_count_7d < 5:
            actions.append("Review title — low views suggest keyword mismatch")
            actions.append("Run Terapeak audit for better search terms")
            urgency = "LOW"
    
    if not actions:
        actions.append("Listing healthy — no action needed")
    
    return {
        "days_listed": days_listed,
        "watcher_count": watcher_count,
        "weekly_views": view_count_7d,
        "urgency": urgency,
        "recommended_actions": actions,
    }

# ── MAIN: DEMO RUN ──
if __name__ == "__main__":
    print("=" * 60)
    print("heat4yafeat — eBay Listing Optimizer")
    print(f"Run date: {datetime.now().strftime('%B %d, %Y')}")
    print("=" * 60)
    
    # Demo: Phantom 6 Black Mamba
    shoe = {
        "name": "Nike Phantom 6 High Black Mamba",
        "brand": "Nike",
        "model": "Phantom 6 High",
        "colorway": "Black Mamba",
        "year": 2015,
        "size": 12,
        "price": 360,
        "sku": "H4YF-005",
        "cost_paid": 180,
    }
    
    print(f"\n[TITLE OPTIMIZATION]")
    title, char_count, status = optimize_title(
        shoe["brand"], shoe["model"], shoe["colorway"],
        shoe["year"], shoe["size"]
    )
    print(f"  Optimized Title: {title}")
    print(f"  Characters: {char_count}/80 — {status}")
    
    print(f"\n[PRICING ANALYSIS]")
    pricing = calculate_pricing(shoe["cost_paid"], "ebay")
    for k, v in pricing.items():
        print(f"  {k}: {v}")
    
    print(f"\n[META TAGS]")
    meta = generate_meta_tags(shoe["name"], shoe["brand"], shoe["year"], shoe["size"], shoe["price"])
    for k, v in meta.items():
        if k != "char_counts":
            print(f"  {k}: {v}")
    print(f"  Status: {meta['char_counts']}")
    
    print(f"\n[YOUTUBE METADATA]")
    yt = generate_youtube_metadata(shoe["name"], shoe["brand"], shoe["year"], "story", shoe["price"])
    print(f"  Title: {yt['optimized_title']}")
    print(f"  Shorts Hook: {yt['shorts_hook']}")
    print(f"  TikTok Hook: {yt['tiktok_hook']}")
    
    print(f"\n[PROMOTED LISTINGS]")
    promo = calculate_promoted_rate("Nike Kobe", "high")
    print(f"  Recommended Rate: {promo['recommended_ad_rate']}")
    print(f"  Note: {promo['note']}")
    
    print(f"\n[STALE LISTING CHECK — H4YF-001 AJ40 Chicago]")
    stale = check_stale_listing(days_listed=45, watcher_count=12, view_count_7d=8)
    print(f"  Urgency: {stale['urgency']}")
    for action in stale["recommended_actions"]:
        print(f"  → {action}")
    
    print("\n" + "=" * 60)
    print("Output complete. Copy generated values to inventory tracker.")
    print("=" * 60)
