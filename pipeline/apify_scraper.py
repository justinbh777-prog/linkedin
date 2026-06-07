"""
Scrapes Stuart's LinkedIn profile posts via Apify to pull engagement metrics.
Matches scraped posts back to rows in Google Sheets by date proximity.
"""
import requests
import os
from datetime import datetime, timedelta, timezone
from pipeline.sheets_manager import update_metrics, read_recent_posts


APIFY_ACTOR = "harvestapi~linkedin-profile-scraper"
LINKEDIN_PROFILE = "https://www.linkedin.com/in/stuartlevenberg/"


def run_apify_scrape(max_posts: int = 30) -> list[dict]:
    """Calls Apify synchronously and returns post data."""
    api_key = os.environ.get("APIFY_API_KEY")
    if not api_key:
        raise ValueError("APIFY_API_KEY not set")

    url = (
        f"https://api.apify.com/v2/actors/{APIFY_ACTOR}"
        f"/run-sync-get-dataset-items?token={api_key}"
    )

    payload = {
        "profileUrls": [LINKEDIN_PROFILE],
        "maxPosts": max_posts,
        "scrapePostsDetails": True,
    }

    print(f"  Calling Apify actor: {APIFY_ACTOR}")
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()

    data = resp.json()
    print(f"  Apify returned {len(data)} items")
    return data


def extract_posts_from_apify(apify_data: list[dict]) -> list[dict]:
    """Normalize Apify response into a flat list of posts with metrics."""
    posts = []
    for item in apify_data:
        raw_posts = item.get("posts", []) or item.get("items", []) or []
        if not raw_posts and "postUrl" in item:
            raw_posts = [item]
        for p in raw_posts:
            posts.append({
                "post_url": p.get("postUrl") or p.get("url", ""),
                "text": p.get("text") or p.get("content", ""),
                "published_at": p.get("publishedAt") or p.get("postedAt", ""),
                "impressions": p.get("impressionsCount") or p.get("impressions", 0),
                "likes": p.get("likesCount") or p.get("likes", 0),
                "comments": p.get("commentsCount") or p.get("comments", 0),
                "shares": p.get("sharesCount") or p.get("shares") or p.get("repostsCount", 0),
            })
    return posts


def match_and_update():
    """
    Pull live metrics from Apify and update the Google Sheet.
    Matches sheet rows that have a Post URL filled in.
    """
    records = read_recent_posts(days=30)

    # Get all rows with a post URL
    rows_with_url = [r for r in records if r.get("Post URL", "").startswith("http")]

    if not rows_with_url:
        print("  No rows with Post URL found in sheet yet. Skipping metrics update.")
        return

    print(f"  Found {len(rows_with_url)} posted rows to update")

    apify_data = run_apify_scrape(max_posts=50)
    live_posts = extract_posts_from_apify(apify_data)

    print(f"  Extracted {len(live_posts)} live posts from Apify")

    for row in rows_with_url:
        post_url = row.get("Post URL", "").strip()
        # Try exact URL match first
        match = next((p for p in live_posts if p["post_url"] == post_url), None)
        if match:
            update_metrics(post_url, match)
        else:
            print(f"  No Apify match for: {post_url}")


if __name__ == "__main__":
    match_and_update()
