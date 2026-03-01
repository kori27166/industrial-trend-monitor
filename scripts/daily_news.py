import feedparser
import yaml
from datetime import datetime
from pathlib import Path

FEEDS_FILE = "feeds.yaml"
OUTFILE = "briefs/daily.md"

def load_feeds():
    with open(FEEDS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["feeds"]

def fetch_feed(url, limit=10):
    feed = feedparser.parse(url)
    return feed.entries[:limit]

def generate_markdown(all_results):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# Industrial Trend Brief - {today}")
    lines.append("")
    lines.append("> Sources: Google News RSS (A/C/D).")
    lines.append("")

    for group in all_results:
        lines.append(f"## {group['name']}")
        lines.append("")
        if not group["items"]:
            lines.append("_No items found._")
        else:
            for item in group["items"]:
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()
                if title and link:
                    lines.append(f"- [{title}]({link})")
        lines.append("")

    return "\n".join(lines)

def save_brief(content):
    Path("briefs").mkdir(parents=True, exist_ok=True)
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    feeds = load_feeds()

    all_results = []
    for feed in feeds:
        items = fetch_feed(feed["url"], limit=10)
        all_results.append({
            "name": feed["name"],
            "category": feed["category"],
            "items": items
        })

    md = generate_markdown(all_results)
    save_brief(md)
    print("Brief generated:", OUTFILE)
