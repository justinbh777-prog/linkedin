"""
Weekly autoresearch loop.
Reads 30 days of post performance from Google Sheets,
sends to Claude for analysis, and rewrites strategy.md.
Commits the updated strategy back to the repo.
"""
import anthropic
import os
import subprocess
from datetime import datetime
from pipeline.sheets_manager import read_recent_posts, log_strategy_update


def load_strategy() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.md")
    with open(path) as f:
        return f.read()


def save_strategy(content: str):
    path = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.md")
    with open(path, "w") as f:
        f.write(content)


def build_analysis_prompt(records: list[dict], current_strategy: str) -> str:
    # Build a summary table of posted content
    posted = [r for r in records if r.get("Status") == "POSTED" and r.get("Post URL")]

    if not posted:
        return ""

    rows_text = ""
    for r in posted:
        eng = r.get("Engagement Rate", "0%")
        rows_text += (
            f"Date: {r.get('Date')} | Category: {r.get('Topic Category')} | "
            f"Hook Type: {r.get('Hook Type A' if r.get('Variant Posted') != 'B' else 'Hook Type B')} | "
            f"Impressions: {r.get('Impressions', 0)} | Likes: {r.get('Likes', 0)} | "
            f"Comments: {r.get('Comments', 0)} | Shares: {r.get('Shares', 0)} | "
            f"Engagement Rate: {eng}\n"
        )

    return f"""You are a LinkedIn content strategist analyzing 30 days of franchise industry posts for Stuart Levenberg — a franchise M&A advisor and resale specialist.

Your job: analyze what worked, what didn't, and rewrite the content strategy to improve performance.

CURRENT STRATEGY:
{current_strategy}

---

POST PERFORMANCE DATA (last 30 days):
{rows_text}

---

ANALYSIS TASKS:

1. Identify the top 3 performing topic categories by engagement rate
2. Identify the top-performing hook type (Financial vs Contrarian vs Acquisition vs Pattern)
3. Identify optimal post length patterns
4. Identify any topic categories that underperformed
5. Recommend 3 specific changes to the content strategy

OUTPUT: Rewrite the full strategy.md file with updated performance tables, revised topic priorities, and concrete recommendations for the next 30 days.

Keep the same structure as the current strategy.md. Update:
- The "Category Performance" table with real data
- The "Best-Performing Hook Types" table with real data
- The "Topic Priority" ranking based on what's working
- The "Auto-Research Notes" section with specific findings

Return ONLY the full updated strategy.md content. No preamble.
"""


def run_autoresearch():
    print("Running weekly autoresearch loop...")
    records = read_recent_posts(days=30)
    posted_count = len([r for r in records if r.get("Status") == "POSTED"])

    if posted_count < 3:
        print(f"  Only {posted_count} posted rows — need at least 3 for meaningful analysis. Skipping.")
        return

    current_strategy = load_strategy()
    prompt = build_analysis_prompt(records, current_strategy)

    if not prompt:
        print("  No performance data available. Skipping.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    print("  Sending to Claude for analysis...")
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    updated_strategy = message.content[0].text.strip()
    save_strategy(updated_strategy)
    print("  strategy.md updated")

    # Log the update
    date_str = datetime.now().strftime("%Y-%m-%d")
    summary = f"Weekly autoresearch: {posted_count} posts analyzed. Strategy updated."
    log_strategy_update(summary, date_str)

    # Commit to repo
    try:
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "add", "data/strategy.md"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"autoresearch: weekly strategy update {date_str}"],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
        print("  strategy.md committed and pushed")
    except subprocess.CalledProcessError as e:
        print(f"  Git commit failed: {e}")


if __name__ == "__main__":
    run_autoresearch()
