import feedparser

# 我們先測試抓一個 Google News RSS
RSS_FEED = "https://news.google.com/rss/search?q=digital+twin+manufacturing&hl=en&gl=US&ceid=US:en"

def fetch_news():
    feed = feedparser.parse(RSS_FEED)

    print("Feed title:", feed.feed.title)
    print("=" * 50)

    for entry in feed.entries[:10]:
        print("Title:", entry.title)
        print("Link:", entry.link)
        print("-" * 50)

if __name__ == "__main__":
    fetch_news()
