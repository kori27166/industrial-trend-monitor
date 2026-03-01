import feedparser
import yaml
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

FEEDS_FILE = "feeds.yaml"
RULES_FILE = "rules.yaml"
OUTFILE = "briefs/daily.md"

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def extract_real_url(google_news_link: str) -> str:
    """
    Google News RSS links often wrap the real URL.
    We'll try to pull ?url=... if present, else return original.
    """
    try:
        u = urlparse(google_news_link)
        qs = parse_qs(u.query)
        if "url" in qs and qs["url"]:
            return qs["url"][0]
    except Exception:
        pass
    return google_news_link

def score_item(title: str, summary: str, rules: dict) -> dict:
    t = normalize_text(title)
    s = normalize_text(summary)
    scoring = rules["scoring"]

    score = 0
    hits = []

    # keywords
    for k, w in scoring["keywords"].items():
        k2 = normalize_text(k)
        if k2 in t:
            score += w * scoring.get("title_multiplier", 2)
            hits.append(f"+{w*scoring.get('title_multiplier',2)} title:{k}")
        elif k2 in s:
            score += w
            hits.append(f"+{w} text:{k}")

    # capital triggers
    for k, w in scoring["capital_triggers"].items():
        k2 = normalize_text(k)
        if k2 in t or k2 in s:
            score += w
            hits.append(f"+{w} capital:{k}")

    # market triggers
    for k, w in scoring["market_triggers"].items():
        k2 = normalize_text(k)
        if k2 in t or k2 in s:
            score += w
            hits.append(f"+{w} market:{k}")

    # noise penalties
    for k, w in scoring["noise_penalties"].items():
        k2 = normalize_text(k)
        if k2 in t or k2 in s:
            score -= w
            hits.append(f"-{w} noise:{k}")

    return {"score": score, "hits": hits}

def detect_business_tags(title: str, summary: str, rules: dict):
    t = normalize_text(title)
    s = normalize_text(summary)
    tags = []

    for tag, config in rules.get("business_tags", {}).items():
        for kw in config.get("keywords", []):
            if normalize_text(kw) in t or normalize_text(kw) in s:
                tags.append(tag)
                break

    return tags
    
def fetch_feed(url, limit=20):
    feed = feedparser.parse(url)
    return feed.entries[:limit]

def build_candidates(feeds, rules):
    candidates = []
    seen = set()

    for feed in feeds:
        entries = fetch_feed(feed["url"], limit=20)
        for e in entries:
            title = e.get("title", "")
            summary = e.get("summary", "") or e.get("description", "")
            link = e.get("link", "")

            real_link = extract_real_url(link)
            key = (normalize_text(title), real_link)

            # 去重：同標題+同連結視為同一則
            if key in seen:
                continue
            seen.add(key)

            scored = score_item(title, summary, rules)
            tags = detect_business_tags(title, summary, rules)

            candidates.append({
                "title": title.strip(),
                "link": real_link,
                "source_group": feed["name"],
                "category": feed["category"],
                "score": scored["score"],
                "hits": scored["hits"],
                "tags": tags,
})

    return candidates

def generate_markdown(items, rules):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    th = rules["thresholds"]
    high = [x for x in items if x["score"] >= th["high_signal"]]
    monitor = [x for x in items if th["monitor"] <= x["score"] < th["high_signal"]]

    # 依分數排序
    high.sort(key=lambda x: x["score"], reverse=True)
    monitor.sort(key=lambda x: x["score"], reverse=True)

    lines = []
    lines.append(f"# Industrial Trend Brief - {today}")
    lines.append("")
    lines.append(f"- Total unique items scanned: **{len(items)}**")
    lines.append(f"- High signal (>= {th['high_signal']}): **{len(high)}**")
    lines.append(f"- Monitor ({th['monitor']}–{th['high_signal']-1}): **{len(monitor)}**")
    lines.append("")

    def render_section(title, arr, topn=15):
        lines.append(f"## {title}")
        lines.append("")
        if not arr:
            lines.append("_No items._")
            lines.append("")
            return
        for x in arr[:topn]:
            tag_str = f" | Tags: {', '.join(x['tags'])}" if x.get("tags") else ""
lines.append(
    f"- **({x['score']})** [{x['title']}]({x['link']})  \n  _{x['category']} | {x['source_group']}{tag_str}"
)
            # 想更透明就打開下一行（會變長）
            # lines.append(f"  - hits: {', '.join(x['hits'][:6])}")
        lines.append("")

    render_section("🔥 High Signal", high, topn=15)
    render_section("🟡 Worth Monitoring", monitor, topn=20)

    lines.append("## Notes")
    lines.append("")
    lines.append("- Scoring is rule-based (no AI). Adjust weights in `rules.yaml`.")
    lines.append("")

    return "\n".join(lines)

def save_brief(content, date_str):
    Path("briefs").mkdir(parents=True, exist_ok=True)

    # 最新版（覆蓋）
    with open("briefs/daily.md", "w", encoding="utf-8") as f:
        f.write(content)

    # 歷史版（每天一份）
    with open(f"briefs/{date_str}.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    feeds = load_yaml(FEEDS_FILE)["feeds"]
    rules = load_yaml(RULES_FILE)

    items = build_candidates(feeds, rules)
    md = generate_markdown(items, rules)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    save_brief(md, date_str)

    print("Brief generated: briefs/daily.md and briefs/{date_str}.md")
