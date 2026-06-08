"""
Scores articles by relevance to franchise M&A, valuations, and exit topics.
Returns the top-scoring article with full text and hero image attached.
"""
import json
import os
import re
from pipeline.scrape_articles import fetch_full_text, fetch_unsplash_image, build_image_keywords


def load_scoring_config():
    src = os.path.join(os.path.dirname(__file__), "..", "data", "sources.json")
    with open(src) as f:
        return json.load(f)["scoring"]


def score_article(article: dict, scoring: dict) -> int:
    text = (article["title"] + " " + article["summary"]).lower()
    score = 0

    for tier, cfg in scoring.items():
        for kw in cfg["keywords"]:
            if kw.lower() in text:
                score += cfg["score"]

    # Apply source priority boost
    score *= article.get("priority_boost", 1)

    # Boost for unit counts in title (small franchise signal)
    if re.search(r'\d+[\s-]unit', article["title"], re.I):
        score += 10

    # Penalize billion-dollar mega deals - not our audience
    if re.search(r'\$[\d,]+\s*b(illion)?', article["title"], re.I):
        score -= 20

    return score


def select_top_article(articles: list[dict]) -> dict | None:
    if not articles:
        return None

    scoring = load_scoring_config()

    scored = []
    for a in articles:
        s = score_article(a, scoring)
        scored.append((s, a))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Pick top article and enrich it
    top_score, top = scored[0]
    print(f"  Top article score: {top_score} — {top['title'][:80]}")

    print("  Fetching full article text...")
    top["full_text"] = fetch_full_text(top["url"])

    print("  Fetching topic-relevant image from Unsplash...")
    top["topic_category"] = categorize(top)  # categorize first so keywords are accurate
    keywords = build_image_keywords(top)
    print(f"  Image search: '{keywords}'")
    top["hero_image_url"] = fetch_unsplash_image(keywords)

    top["score"] = top_score
    return top


def categorize(article: dict) -> str:
    text = (article["title"] + " " + article["summary"]).lower()
    if any(k in text for k in ["private equity", "pe firm", "acquisition", "acquired", "merger", "buyout", "roll-up"]):
        return "PE/M&A"
    if any(k in text for k in ["valuation", "multiple", "ebitda", "worth", "sale price"]):
        return "Valuation"
    if any(k in text for k in ["multi-unit", "area developer", "franchisee growth"]):
        return "Multi-Unit"
    if any(k in text for k in ["fitness", "gym", "yoga", "workout", "wellness"]):
        return "Fitness"
    if any(k in text for k in ["restaurant", "food", "qsr", "fast food", "pizza", "burger"]):
        return "Food/QSR"
    if any(k in text for k in ["home service", "restoration", "cleaning", "plumbing", "hvac"]):
        return "Home Services"
    if any(k in text for k in ["children", "kids", "education", "learning", "tutoring"]):
        return "Children's"
    if any(k in text for k in ["senior", "elderly", "care", "assisted living"]):
        return "Senior Care"
    return "General Franchise"


if __name__ == "__main__":
    from pipeline.scrape_articles import scrape_all
    articles = scrape_all()
    top = select_top_article(articles)
    if top:
        print("\nSelected:", top["title"])
        print("Category:", top["topic_category"])
        print("Score:", top["score"])
