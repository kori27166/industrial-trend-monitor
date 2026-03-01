import feedparser
from datetime import datetime

RSS_FEED = "https://news.google.com/rss/search?q=digital+twin+manufacturing&hl=en&gl=US&ceid=US:en"

def fetch_news():
    feed = feedparser.parse(RSS_FEED)
    return feed.entries[:10]

def generate_markdown(entries):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# Industrial Trend Brief - {today}")
    lines.append("")
    lines.append("## Digital Twin / Manufacturing News")
    lines.append("")

    for entry in entries:
        lines.append(f"- [{entry.title}]({entry.link})")

    return "\n".join(lines)

def save_brief(content):
    with open("briefs/daily.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    news = fetch_news()
    markdown = generate_markdown(news)
    save_brief(markdown)
    print("Brief generated successfully.")
