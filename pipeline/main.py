"""
Daily pipeline entry point.
Scrape → Score → Generate → Save to Sheet + Markdown file.
"""
import os
import sys
from datetime import datetime

from pipeline.scrape_articles import scrape_all
from pipeline.score_articles import select_top_article
from pipeline.generate_post import generate_post
from pipeline.sheets_manager import append_post


def save_markdown(article: dict, posts: dict, date_str: str):
    """Save a clean markdown file with both post variants for easy reference."""
    posts_dir = os.path.join(os.path.dirname(__file__), "..", "data", "posts")
    os.makedirs(posts_dir, exist_ok=True)
    filepath = os.path.join(posts_dir, f"{date_str}.md")

    content = f"""# LinkedIn Post — {date_str}

**Suggested Post Time:** 10:00 AM EST

---

## Source Article

**Title:** {article['title']}
**Source:** {article['source']}
**URL:** {article['url']}
**Category:** {article['topic_category']}
**Relevance Score:** {article['score']}

---

## POST VARIANT A — {posts['hook_type_A']} Hook

*(Copy and paste this to LinkedIn. Attach the hero image above.)*

---

{posts['variant_A']}

---

## POST VARIANT B — {posts['hook_type_B']} Hook

*(Alternative — test this against Variant A)*

---

{posts['variant_B']}

---

## Instructions

1. Pick Variant A or B
2. Copy the post text
3. Go to LinkedIn and create a new post
4. Post at 10:00 AM EST for best reach
6. After posting, paste the post URL into the Google Sheet row for {date_str}
7. Update Status column to POSTED

**Google Sheet:** https://docs.google.com/spreadsheets/d/1mZlBdEkkg81-jS3jdyaKNeIcgwwQnpAQNKY7gvbdFlo/edit
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Markdown saved: data/posts/{date_str}.md")
    return filepath


def run():
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"FRANCHISE CONTENT ENGINE — {date_str}")
    print(f"{'='*60}\n")

    print("STEP 1: Scraping articles...")
    articles = scrape_all()
    if not articles:
        print("  No articles found. Exiting.")
        sys.exit(1)

    print("\nSTEP 2: Scoring and selecting top article...")
    top = select_top_article(articles)
    if not top:
        print("  Could not select top article. Exiting.")
        sys.exit(1)

    print(f"\n  Selected: {top['title']}")
    print(f"  Source:   {top['source']}")
    print(f"  Category: {top['topic_category']}")
    print(f"  Score:    {top['score']}")

    print("\nSTEP 3: Generating LinkedIn posts (A/B variants)...")
    posts = generate_post(top)

    print("\nSTEP 4: Saving to Google Sheets...")
    append_post(top, posts, date_str)

    print("\nSTEP 5: Saving markdown file...")
    save_markdown(top, posts, date_str)

    print(f"\n{'='*60}")
    print("DONE. Check the Google Sheet and data/posts/{date_str}.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
