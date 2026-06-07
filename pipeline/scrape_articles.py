"""
Scrapes franchise industry news sources and returns a list of recent articles.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import json
import time
import os


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
LOOKBACK_HOURS = 48


def load_sources():
    src = os.path.join(os.path.dirname(__file__), "..", "data", "sources.json")
    with open(src) as f:
        return json.load(f)


def is_recent(entry):
    """Return True if the feed entry was published within LOOKBACK_HOURS."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            pub = datetime(*t[:6], tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - pub) < timedelta(hours=LOOKBACK_HOURS)
    return True  # include if no date available


def fetch_full_text(url: str) -> str:
    """Attempt to pull the article body text from a URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        article = soup.find("article") or soup.find(class_=lambda c: c and "article" in c.lower())
        if article:
            return article.get_text(" ", strip=True)[:3000]
        return soup.get_text(" ", strip=True)[:3000]
    except Exception:
        return ""


def fetch_hero_image(url: str) -> str:
    """Return the og:image URL for an article page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
        img = soup.find("article img") if soup.find("article") else soup.find("img")
        return img["src"] if img and img.get("src") else ""
    except Exception:
        return ""


def scrape_rss(feed_cfg: dict) -> list[dict]:
    articles = []
    try:
        feed = feedparser.parse(feed_cfg["url"])
        for entry in feed.entries:
            if not is_recent(entry):
                continue
            articles.append({
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", ""),
                "summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)[:500],
                "source": feed_cfg["name"],
                "priority_boost": feed_cfg.get("priority_boost", 1),
                "published": entry.get("published", ""),
            })
    except Exception as e:
        print(f"RSS error ({feed_cfg['name']}): {e}")
    return articles


def scrape_html(page_cfg: dict) -> list[dict]:
    articles = []
    try:
        resp = requests.get(page_cfg["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        base = "https://www.franchisetimes.com"
        for a in soup.select("h2 a, h3 a, .article-title a")[:20]:
            href = a.get("href", "")
            if not href:
                continue
            if href.startswith("/"):
                href = base + href
            title = a.get_text(strip=True)
            if title:
                articles.append({
                    "title": title,
                    "url": href,
                    "summary": "",
                    "source": page_cfg["name"],
                    "priority_boost": page_cfg.get("priority_boost", 1),
                    "published": "",
                })
    except Exception as e:
        print(f"HTML scrape error ({page_cfg['name']}): {e}")
    return articles


def scrape_all() -> list[dict]:
    sources = load_sources()
    all_articles = []

    for feed in sources["rss_feeds"]:
        print(f"  Fetching RSS: {feed['name']}")
        all_articles.extend(scrape_rss(feed))
        time.sleep(0.5)

    for page in sources["scrape_urls"]:
        print(f"  Scraping HTML: {page['name']}")
        all_articles.extend(scrape_html(page))
        time.sleep(0.5)

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen and a["url"]:
            seen.add(a["url"])
            unique.append(a)

    print(f"  Total unique articles found: {len(unique)}")
    return unique


if __name__ == "__main__":
    articles = scrape_all()
    for a in articles[:5]:
        print(a["title"], "|", a["source"])
