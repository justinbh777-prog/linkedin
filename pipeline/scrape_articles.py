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


def fetch_unsplash_image(keywords: str) -> str:
    """Search Unsplash for a high-quality landscape image matching the article topic."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        return ""
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": keywords, "orientation": "landscape", "per_page": 5, "order_by": "relevant"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return results[0]["urls"]["regular"]
    except Exception as e:
        print(f"  Unsplash error: {e}")
    return ""


def build_image_keywords(article: dict) -> str:
    """Extract relevant search keywords from the article for Unsplash."""
    category = article.get("topic_category", "")
    title = article.get("title", "")

    keyword_map = {
        "PE/M&A":            "business acquisition deal corporate office",
        "Valuation":         "business growth chart meeting",
        "Multi-Unit":        "franchise storefront retail business",
        "Fitness":           "fitness gym modern interior",
        "Food/QSR":          "restaurant storefront food service",
        "Home Services":     "home services professional contractor",
        "Children's":        "children education learning",
        "Senior Care":       "senior care professional",
        "General Franchise": "franchise business professional storefront",
    }
    base = keyword_map.get(category, "franchise business professional")

    known_brands = [
        "McDonald", "Subway", "Chick-fil-A", "Domino", "Pizza Hut",
        "Anytime Fitness", "Orangetheory", "Great Clips", "Sport Clips",
        "7-Eleven", "UPS Store", "Kumon",
    ]
    for brand in known_brands:
        if brand.lower() in title.lower():
            base = f"{brand} franchise storefront exterior"
            break

    return base


def is_headshot_url(url: str) -> bool:
    """Return True if the URL looks like a headshot/avatar/author photo."""
    headshot_signals = [
        "avatar", "author", "headshot", "profile", "staff", "reporter",
        "journalist", "byline", "mugshot", "person", "people",
        # Small square resize params are a dead giveaway (CMS thumbnail of a person)
        "resize=200%2C200", "resize=200,200",
        "resize=100%2C100", "resize=150%2C150",
        "crop=518%2C518", "crop=200%2C200",
    ]
    url_lower = url.lower()
    return any(signal in url_lower for signal in headshot_signals)


def fetch_hero_image(url: str) -> str:
    """
    Return the best landscape/editorial image URL for an article page.
    Skips headshots, author photos, and tiny thumbnails.
    Prefers og:image (usually the article's main editorial image),
    but strips CMS resize parameters that indicate a thumbnail crop.
    Falls back to the largest landscape img tag found in the article body.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Try og:image first (best source for editorial images) ---
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            og_url = og["content"]
            if not is_headshot_url(og_url):
                # Strip CMS resize/crop query params to get full-size image
                clean = og_url.split("?")[0]
                return clean

        # --- Fall back: scan article body for landscape images ---
        article = soup.find("article") or soup.find(class_=lambda c: c and "article-body" in (c if isinstance(c, str) else " ".join(c)).lower())
        search_area = article if article else soup

        best_url = ""
        best_score = 0

        for img in search_area.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if not src or src.startswith("data:"):
                continue
            if is_headshot_url(src):
                continue
            # Skip tiny icons
            skip_keywords = ["icon", "logo", "sprite", "pixel", "tracking", "ad", "banner"]
            if any(k in src.lower() for k in skip_keywords):
                continue

            # Score by width attribute (prefer wide images)
            width = 0
            try:
                width = int(img.get("width", 0))
            except (ValueError, TypeError):
                pass

            # Boost score for images with "large", "full", "hero", "featured" in URL
            url_boost = sum(1 for k in ["large", "full", "hero", "featured", "editorial"] if k in src.lower())
            score = width + (url_boost * 300)

            if score > best_score:
                best_score = score
                best_url = src.split("?")[0]  # strip resize params

        if best_url:
            # Make absolute URL if relative
            if best_url.startswith("//"):
                best_url = "https:" + best_url
            elif best_url.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                best_url = f"{parsed.scheme}://{parsed.netloc}{best_url}"
            return best_url

        return ""
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
