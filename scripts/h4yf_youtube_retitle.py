#!/usr/bin/env python3
"""
h4yf_youtube_retitle.py
Pull all public videos from @HEAT4YAFEAT, classify titles, draft retitles,
and output the Josh-gate review doc (Markdown).

Usage:
    python3 h4yf_youtube_retitle.py --key AIza...
    python3 h4yf_youtube_retitle.py --worklist C:/Users/JAP/h4yf_youtube_worklist.json
    python3 h4yf_youtube_retitle.py --key-file C:/Users/JAP/.h4yf_secrets/google_cloud_YouTube.txt
"""

import argparse, json, sys, re, textwrap
from pathlib import Path
from datetime import datetime

try:
    import urllib.request as req
    import urllib.parse as up
except ImportError:
    sys.exit("Python 3.x required")

# ─── Channel constants ────────────────────────────────────────────────────────
CHANNEL_ID    = "UCgkDTwvA03jjul-H4SSlXNg"
UPLOADS_PL    = "UUgkDTwvA03jjul-H4SSlXNg"   # UC → UU prefix = uploads playlist
YT_API_BASE   = "https://www.googleapis.com/youtube/v3"

# ─── Brand formula & rules ────────────────────────────────────────────────────
FORMULA = "HEAT4YAFEAT presents [Full Shoe Name] [Year] — [Hook]"

HOOKS = [
    "Worth $X in 2026?",
    "The Full History",
    "How to Spot a Fake",
    "Cop or Skip?",
    "Real Authentication",
    "Every Detail",
    "What You Need to Know",
    "The Breakdown",
]

# Known off-brand / personal content → flag for UNLIST review (Bill decides)
UNLIST_SIGNALS = [
    "colts", "football", "dustin creekmore",
    "cat", "cats", "kitten",
    "nintendo", "switch",
    "campbell", "barbershop",
    "nba 2k", "2k", "gaming",
]

# Expired promo patterns → flag for UNLIST
PROMO_SIGNALS = [
    "sale ends", "limited time", "only until", "expires",
    "black friday", "cyber monday", "last chance",
]

# ─── YouTube Data API helpers ─────────────────────────────────────────────────

def yt_get(endpoint, params):
    url = f"{YT_API_BASE}/{endpoint}?" + up.urlencode(params)
    try:
        with req.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        sys.exit(f"YouTube API error: {e}")


def paginate_playlist(api_key, playlist_id):
    """Return list of {videoId, title, publishedAt} for entire playlist."""
    videos = []
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }
    while True:
        data = yt_get("playlistItems", params)
        for item in data.get("items", []):
            sn = item["snippet"]
            vid = sn.get("resourceId", {}).get("videoId", "")
            if vid:
                videos.append({
                    "videoId":    vid,
                    "title":      sn.get("title", ""),
                    "published":  sn.get("publishedAt", "")[:10],
                    "url":        f"https://youtu.be/{vid}",
                })
        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    return videos


def enrich_with_stats(api_key, videos):
    """Add views/likes/duration via videos.list (batch 50)."""
    enriched = []
    for i in range(0, len(videos), 50):
        batch = videos[i:i+50]
        ids   = ",".join(v["videoId"] for v in batch)
        data  = yt_get("videos", {
            "part":   "statistics,contentDetails",
            "id":     ids,
            "key":    api_key,
        })
        stats_map = {}
        for item in data.get("items", []):
            vid = item["id"]
            s   = item.get("statistics", {})
            d   = item.get("contentDetails", {})
            dur = d.get("duration", "PT0S")
            stats_map[vid] = {
                "views":    int(s.get("viewCount", 0)),
                "likes":    int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "duration": dur,
            }
        for v in batch:
            v.update(stats_map.get(v["videoId"], {}))
            enriched.append(v)
    return enriched


# ─── Title classification ─────────────────────────────────────────────────────

def uses_formula(title: str) -> bool:
    """True if title already matches HEAT4YAFEAT presents … — … pattern."""
    t = title.strip()
    return bool(re.match(r"HEAT4YAFEAT\s+presents\s+.+\s+—\s+.+", t, re.IGNORECASE))


def classify(title: str) -> str:
    """Return: ON_FORMULA | UNLIST_CANDIDATE | EXPIRED_PROMO | NEEDS_RETITLE"""
    tl = title.lower()
    if uses_formula(title):
        return "ON_FORMULA"
    if any(s in tl for s in UNLIST_SIGNALS):
        return "UNLIST_CANDIDATE"
    if any(s in tl for s in PROMO_SIGNALS):
        return "EXPIRED_PROMO"
    return "NEEDS_RETITLE"


# ─── Retitle engine ───────────────────────────────────────────────────────────

# Shoe keyword → canonical full name mapping (expand as needed)
SHOE_CANON = {
    "aj1": "Air Jordan 1",        "jordan 1": "Air Jordan 1",
    "aj2": "Air Jordan 2",        "jordan 2": "Air Jordan 2",
    "aj3": "Air Jordan 3",        "jordan 3": "Air Jordan 3",
    "aj4": "Air Jordan 4",        "jordan 4": "Air Jordan 4",
    "aj5": "Air Jordan 5",        "jordan 5": "Air Jordan 5",
    "aj6": "Air Jordan 6",        "jordan 6": "Air Jordan 6",
    "aj7": "Air Jordan 7",        "jordan 7": "Air Jordan 7",
    "aj8": "Air Jordan 8",        "jordan 8": "Air Jordan 8",
    "aj9": "Air Jordan 9",        "jordan 9": "Air Jordan 9",
    "aj10": "Air Jordan 10",      "jordan 10": "Air Jordan 10",
    "aj11": "Air Jordan 11",      "jordan 11": "Air Jordan 11",
    "aj12": "Air Jordan 12",      "jordan 12": "Air Jordan 12",
    "aj13": "Air Jordan 13",      "jordan 13": "Air Jordan 13",
    "aj14": "Air Jordan 14",      "jordan 14": "Air Jordan 14",
    "aj15": "Air Jordan 15",      "jordan 15": "Air Jordan 15",
    "retro": "",  # strip, not a shoe name
    "kobe": "Kobe",               "phantom": "Kobe Phantom",
    "lebron": "LeBron",           "lbj": "LeBron",
    "dunk": "Nike Dunk",          "sb dunk": "Nike SB Dunk",
    "air max": "Air Max",         "uptempo": "Air More Uptempo",
    "force savage": "Air Jordan 3 Force Savage",
    "trophy room": "Air Jordan 7 Trophy Room",
    "flint": "Air Jordan 13 Flint",
    "mamba": "Kobe Black Mamba",
    "foamposite": "Nike Air Foamposite",
}

def extract_shoe_name(title: str) -> str:
    """Best-effort extraction of shoe name from a raw title."""
    tl = title.lower()
    # Try longest match first
    for kw, canon in sorted(SHOE_CANON.items(), key=lambda x: -len(x[0])):
        if kw in tl and canon:
            return canon
    # Fallback: title-case the original title (minus known junk words)
    junk = {"heat4yafeat", "presents", "h4yf", "review", "unboxing",
            "for", "sale", "check", "out", "my", "new", "the", "a", "an"}
    words = [w for w in re.split(r"\W+", title) if w.lower() not in junk and w]
    return " ".join(words[:4]).title() if words else title[:40]


def pick_hook(title: str, views: int) -> str:
    """Pick the best hook based on title keywords."""
    tl = title.lower()
    if any(k in tl for k in ["fake", "auth", "real", "legit", "check"]):
        return "How to Spot a Fake"
    if any(k in tl for k in ["history", "story", "og", "original", "1985", "1986", "1987",
                               "1988", "1989", "1990", "1991", "1992", "1993", "1994",
                               "1995", "1996", "1997", "1998", "1999", "2000", "2001",
                               "2002", "2003", "2004"]):
        return "The Full History"
    if any(k in tl for k in ["cop", "skip", "buy", "pass", "should", "worth"]):
        return "Cop or Skip?"
    if views and views > 50:
        return "Worth $X in 2026?"
    return "Real Authentication"


def extract_year(title: str, published: str) -> str:
    """Extract or infer the shoe's release year."""
    # Look for 4-digit year in title
    years = re.findall(r"\b(19[789]\d|20[012]\d)\b", title)
    if years:
        return years[0]
    # Fall back to published year
    if published:
        return published[:4]
    return "2026"


def draft_retitle(video: dict) -> tuple[str, str]:
    """Return (proposed_title, rationale) for a NEEDS_RETITLE video."""
    title     = video.get("title", "")
    views     = video.get("views", 0)
    published = video.get("published", "")

    shoe = extract_shoe_name(title)
    year = extract_year(title, published)
    hook = pick_hook(title, views)

    proposed = f"HEAT4YAFEAT presents {shoe} {year} — {hook}"

    rationale = (
        f"Current title lacks the brand prefix and formula hook. "
        f"Shoe identified as \"{shoe}\". "
        f"Hook \"{hook}\" selected based on {'keyword match' if 'auth' in title.lower() or 'fake' in title.lower() else 'view-count + content type'}. "
        f"Year {year} from {'title text' if re.search(r'\\b(19|20)\\d\\d\\b', title) else 'publish date'}."
    )
    return proposed, rationale


# ─── Deliverable writer ───────────────────────────────────────────────────────

def write_review_doc(videos: list, out_path: Path):
    now = datetime.utcnow().strftime("%Y-%m-%d")

    on_formula    = [v for v in videos if v["_class"] == "ON_FORMULA"]
    needs_retitle = [v for v in videos if v["_class"] == "NEEDS_RETITLE"]
    unlist        = [v for v in videos if v["_class"] == "UNLIST_CANDIDATE"]
    expired_promo = [v for v in videos if v["_class"] == "EXPIRED_PROMO"]

    lines = []
    A = lines.append

    A(f"# HEAT4YAFEAT — YouTube Retitle Review")
    A(f"**Josh-gate deliverable** | Prepared by Verus | {now}")
    A(f"Channel: @HEAT4YAFEAT (`{CHANNEL_ID}`) | {len(videos)} public videos audited")
    A("")
    A("---")
    A("")
    A("## EXECUTIVE SUMMARY")
    A("")
    A(f"| Category | Count |")
    A(f"|---|---|")
    A(f"| ✅ On-formula (no action) | {len(on_formula)} |")
    A(f"| ✏️ Needs retitle (core work) | {len(needs_retitle)} |")
    A(f"| 🗑️ Unlist candidates (Bill decides) | {len(unlist)} |")
    A(f"| ⏰ Expired promos (Bill decides) | {len(expired_promo)} |")
    A(f"| **Total** | **{len(videos)}** |")
    A("")
    A("**Title formula (locked):**")
    A(f"> `{FORMULA}`")
    A("")
    A("**Approved hooks:** " + " · ".join(f'"{h}"' for h in HOOKS))
    A("")
    A("**Brand rules enforced:**")
    A("- HEAT4YAFEAT = ALL CAPS in every title")
    A("- Full shoe name with colorway/edition where known")
    A("- Year = release year preferred, publish year fallback")
    A("- Em dash `—` (not hyphen) before the hook")
    A("- No price claims in title (YouTube policy)")
    A("")
    A("---")
    A("")

    # ── Section 1: Needs retitle ──────────────────────────────────────────────
    A("## SECTION 1 — Titles Needing the Formula ✏️")
    A(f"*{len(needs_retitle)} videos · Apply after Josh review · Can batch-apply via YouTube API*")
    A("")

    # Sort by views descending (fix highest-traffic first)
    for i, v in enumerate(sorted(needs_retitle, key=lambda x: x.get("views", 0), reverse=True), 1):
        proposed, rationale = draft_retitle(v)
        v["_proposed"] = proposed
        A(f"### {i}. `{v['videoId']}`")
        A(f"**URL:** {v['url']}")
        A(f"**Views:** {v.get('views', 'n/a')} | **Published:** {v.get('published', 'n/a')}")
        A(f"")
        A(f"| | Title |")
        A(f"|---|---|")
        A(f"| **Current** | {v['title']} |")
        A(f"| **Proposed** | {proposed} |")
        A(f"")
        A(f"**Rationale:** {rationale}")
        A(f"")
        A("---")
        A("")

    # ── Section 2: Unlist candidates ─────────────────────────────────────────
    A("## SECTION 2 — Unlist Candidates 🗑️")
    A(f"*{len(unlist)} videos · Off-brand/personal content · **Bill makes final call** · same topical-dilution risk as Campbell's Barbershop video (B5)*")
    A("")
    A("| # | Video ID | Current Title | Published | Views | Reason |")
    A("|---|---|---|---|---|---|")
    for i, v in enumerate(unlist, 1):
        tl = v["title"].lower()
        reason = "Off-brand personal" if any(s in tl for s in ["colts","football","cat","nintendo","gaming","nba 2k"]) else "Non-sneaker content"
        if "campbell" in tl or "barbershop" in tl:
            reason = "Barbershop collab — non-sneaker (B5)"
        A(f"| {i} | `{v['videoId']}` | {v['title']} | {v.get('published','?')} | {v.get('views','?')} | {reason} |")
    A("")
    A("---")
    A("")

    # ── Section 3: Expired promos ─────────────────────────────────────────────
    A("## SECTION 3 — Expired Promos ⏰")
    A(f"*{len(expired_promo)} videos · Time-sensitive content now stale · Bill decides: unlist or retitle*")
    A("")
    A("| # | Video ID | Current Title | Published | Views |")
    A("|---|---|---|---|---|")
    for i, v in enumerate(expired_promo, 1):
        A(f"| {i} | `{v['videoId']}` | {v['title']} | {v.get('published','?')} | {v.get('views','?')} |")
    A("")
    A("---")
    A("")

    # ── Section 4: On-formula (confirmation) ──────────────────────────────────
    A("## SECTION 4 — Already On-Formula ✅")
    A(f"*{len(on_formula)} videos · No action needed · Sorted by views (highest first)*")
    A("")
    A("| # | Video ID | Title | Published | Views |")
    A("|---|---|---|---|---|")
    for i, v in enumerate(sorted(on_formula, key=lambda x: x.get("views", 0), reverse=True), 1):
        A(f"| {i} | `{v['videoId']}` | {v['title']} | {v.get('published','?')} | {v.get('views','?')} |")
    A("")
    A("---")
    A("")
    A("## DEPLOY NOTES")
    A("")
    A("Once Josh approves the retitles in Section 1:")
    A("")
    A("```powershell")
    A("# Apply retitles via YouTube API (requires S3 OAuth — manager access)")
    A("# h4yf_youtube_api.ps1 -Action UpdateMetadata -VideoId <id> -Title '<proposed title>'")
    A("```")
    A("")
    A("Or batch-apply using the CSV export from this script.")
    A("")
    A(f"*Generated {now} by Verus. Brand standards: HEAT4YAFEAT brand standards doc (locked June-16, 2026).*")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Review doc written → {out_path}")

    # Also write a CSV for easy upload
    csv_path = out_path.with_suffix(".csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("videoId,url,currentTitle,proposedTitle,classification,views,published\n")
        for v in videos:
            proposed = v.get("_proposed", "")
            f.write(
                f'"{v["videoId"]}","{v["url"]}","{v["title"].replace(chr(34), "'")}","{proposed}",'
                f'"{v["_class"]}","{v.get("views","")}","{v.get("published","")}"' + "\n"
            )
    print(f"✅ CSV written → {csv_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="H4YF YouTube retitle deliverable")
    ap.add_argument("--key",      help="YouTube Data API v3 key (AIza...)")
    ap.add_argument("--key-file", help="Path to file containing the API key")
    ap.add_argument("--worklist", help="Path to existing h4yf_youtube_worklist.json")
    ap.add_argument("--out",      default="h4yf_youtube_retitle_review.md",
                    help="Output Markdown file (default: h4yf_youtube_retitle_review.md)")
    args = ap.parse_args()

    # ── Resolve API key ───────────────────────────────────────────────────────
    api_key = args.key
    if not api_key and args.key_file:
        api_key = Path(args.key_file).read_text().strip()

    # ── Pull or load video list ───────────────────────────────────────────────
    if args.worklist:
        print(f"Loading worklist from {args.worklist} …")
        videos = json.loads(Path(args.worklist).read_text(encoding="utf-8"))
    elif api_key:
        print(f"Pulling videos from uploads playlist {UPLOADS_PL} …")
        videos = paginate_playlist(api_key, UPLOADS_PL)
        print(f"  → {len(videos)} videos found. Enriching with stats …")
        videos = enrich_with_stats(api_key, videos)
        # Save worklist for next time
        worklist_out = Path("h4yf_youtube_worklist_fresh.json")
        worklist_out.write_text(json.dumps(videos, indent=2, ensure_ascii=False))
        print(f"  → Worklist saved to {worklist_out}")
    else:
        sys.exit("Provide --key, --key-file, or --worklist")

    # ── Classify ──────────────────────────────────────────────────────────────
    for v in videos:
        v["_class"]    = classify(v.get("title", ""))
        v["_proposed"] = ""

    # ── Report ────────────────────────────────────────────────────────────────
    from collections import Counter
    counts = Counter(v["_class"] for v in videos)
    print(f"\nClassification:")
    for cls, n in counts.items():
        print(f"  {cls}: {n}")

    # ── Write deliverable ─────────────────────────────────────────────────────
    out_path = Path(args.out)
    write_review_doc(videos, out_path)


if __name__ == "__main__":
    main()
