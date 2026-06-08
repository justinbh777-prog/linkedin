"""
Daily pipeline entry point.
Generates TWO posts per day:
  1. Article post - based on top franchise news article
  2. Personal post - Stuart's voice, no article needed
Both saved to Google Sheets + daily markdown file.
"""
import os
import sys
from datetime import datetime

from pipeline.scrape_articles import scrape_all
from pipeline.score_articles import select_top_article
from pipeline.generate_post import generate_post
from pipeline.generate_personal_post import generate_personal_post
from pipeline.sheets_manager import append_post, append_personal_post


def save_markdown(article: dict, posts: dict, personal: dict, date_str: str):
    posts_dir = os.path.join(os.path.dirname(__file__), "..", "data", "posts")
    os.makedirs(posts_dir, exist_ok=True)
    filepath = os.path.join(posts_dir, f"{date_str}.md")

    content = f"""# Daily Posts — {date_str}

**Suggested Post Time:** 10:00 AM EST

---

# POST 1 — Article Post

**Article:** {article['title']}
**Source:** {article['source']}
**URL:** {article['url']}
**Category:** {article['topic_category']}

---

## VARIANT A — {posts['hook_type_A']} Hook

{posts['variant_A']}

---

## VARIANT B — {posts['hook_type_B']} Hook

{posts['variant_B']}

---
---

# POST 2 — Personal Post

**Topic:** {personal['topic']}

---

{personal['post']}

---

## Instructions

**Post 1 (Article):** Pick Variant A or B. Copy and post on LinkedIn at 10am EST.
**Post 2 (Personal):** Post this separately later in the day or next morning.
After posting each one, paste the LinkedIn URL into the Google Sheet and set Status to POSTED.

**Google Sheet:** https://docs.google.com/spreadsheets/d/1mZlBdEkkg81-jS3jdyaKNeIcgwwQnpAQNKY7gvbdFlo/edit
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Markdown saved: data/posts/{date_str}.md")


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
    print(f"  Category: {top['topic_category']} | Score: {top['score']}")

    print("\nSTEP 3: Generating article post (A/B variants)...")
    posts = generate_post(top)

    print("\nSTEP 4: Generating personal post...")
    personal = generate_personal_post()
    print(f"  Topic: {personal['topic']}")

    print("\nSTEP 5: Saving both posts to Google Sheets...")
    append_post(top, posts, date_str)
    append_personal_post(personal, date_str)

    print("\nSTEP 6: Saving markdown file...")
    save_markdown(top, posts, personal, date_str)

    print(f"\n{'='*60}")
    print(f"DONE. 2 posts ready in Google Sheet and data/posts/{date_str}.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
