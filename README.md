# Franchise Content Engine

Automated franchise industry content pipeline for Stuart Levenberg's LinkedIn presence.

## What It Does

**Daily (10am EST, Mon–Fri)**
- Scrapes 7+ franchise industry news sources
- Scores articles by M&A, PE, valuation, and exit relevance
- Generates two LinkedIn post variants (A/B) using Claude Opus
- Saves both variants to Google Sheets + a dated markdown file in `data/posts/`

**Daily (2pm EST, Tue–Sat)**
- Scrapes Stuart's LinkedIn profile via Apify
- Updates engagement metrics (impressions, likes, comments, shares) in Google Sheets

**Weekly (Sunday 7am EST)**
- Analyzes 30 days of post performance
- Identifies best topics, best hook types, best post lengths
- Rewrites `data/strategy.md` with updated strategy
- Commits updated strategy to this repo automatically

## Posting Workflow (Stuart)

1. Check email or open `data/posts/YYYY-MM-DD.md` in this repo each morning
2. Pick Variant A or B
3. Copy the post text
4. Go to LinkedIn → Create post → Paste text → Attach hero image
5. Post at 10am EST
6. Paste the post URL into the Google Sheet column "Post URL"
7. Change Status to POSTED

**Google Sheet:** https://docs.google.com/spreadsheets/d/1mZlBdEkkg81-jS3jdyaKNeIcgwwQnpAQNKY7gvbdFlo/edit

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `APIFY_API_KEY` | Apify API key |
| `GOOGLE_SHEET_ID` | Google Sheet ID (from URL) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (one line) |

## Manual Trigger

Any workflow can be manually triggered from the **Actions** tab in GitHub → select workflow → **Run workflow**.

## File Structure

```
franchise-content-engine/
├── .github/workflows/
│   ├── daily_pipeline.yml       # Scrape → generate → save
│   ├── scrape_metrics.yml       # Pull LinkedIn engagement
│   └── autoresearch.yml         # Weekly strategy update
├── pipeline/
│   ├── main.py                  # Daily pipeline entry point
│   ├── scrape_articles.py       # Multi-source news scraper
│   ├── score_articles.py        # Article scoring + selection
│   ├── generate_post.py         # Claude post generation (A/B)
│   ├── sheets_manager.py        # Google Sheets read/write
│   ├── apify_scraper.py         # LinkedIn metrics via Apify
│   └── autoresearch.py          # Weekly analysis + strategy update
├── data/
│   ├── sources.json             # News sources + scoring config
│   ├── strategy.md              # Live content strategy (auto-updated)
│   └── posts/                   # Daily markdown files
└── requirements.txt
```
