"""
Manages all Google Sheets read/write operations.
Sheet schema defined here — creates headers on first run.
"""
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_HEADERS = [
    "Date",
    "Suggested Post Time (EST)",
    "Article Title",
    "Article URL",
    "Source",
    "Topic Category",
    "Relevance Score",
    "Hook Type A",
    "Post Variant A",
    "Hook Type B",
    "Post Variant B",
    "Variant Posted (A/B)",
    "Status",
    "Post URL",
    "Impressions",
    "Likes",
    "Comments",
    "Shares",
    "Engagement Rate",
    "Hero Image URL",
    "Notes",
]

TAB_POSTS = "Posts"
TAB_METRICS = "Weekly Metrics"
TAB_STRATEGY = "Strategy Log"


def get_client():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    creds_dict = json.loads(sa_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_sheet(client, sheet_id: str, tab_name: str):
    spreadsheet = client.open_by_key(sheet_id)
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
        return ws


def ensure_headers(worksheet, headers: list):
    existing = worksheet.row_values(1)
    if not existing:
        worksheet.append_row(headers, value_input_option="RAW")


def append_post(article: dict, posts: dict, date_str: str):
    """Write a new post row to the Posts tab."""
    client = get_client()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    ws = get_or_create_sheet(client, sheet_id, TAB_POSTS)
    ensure_headers(ws, SHEET_HEADERS)

    row = [
        date_str,
        "10:00 AM",
        article.get("title", ""),
        article.get("url", ""),
        article.get("source", ""),
        article.get("topic_category", ""),
        str(article.get("score", "")),
        posts.get("hook_type_A", "Financial"),
        posts.get("variant_A", ""),
        posts.get("hook_type_B", "Contrarian"),
        posts.get("variant_B", ""),
        "",          # Variant Posted — Stuart fills in
        "PENDING",
        "",          # Post URL — Stuart fills in
        "",          # Impressions
        "",          # Likes
        "",          # Comments
        "",          # Shares
        "",          # Engagement Rate
        article.get("hero_image_url", ""),
        "",          # Notes
    ]

    ws.append_row(row, value_input_option="USER_ENTERED")
    print(f"  Row appended to Google Sheet tab '{TAB_POSTS}'")


def update_metrics(post_url: str, metrics: dict):
    """Update engagement metrics for a row identified by post URL."""
    client = get_client()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    ws = get_or_create_sheet(client, sheet_id, TAB_POSTS)

    post_url_col = SHEET_HEADERS.index("Post URL") + 1
    cells = ws.col_values(post_url_col)

    for i, val in enumerate(cells):
        if val == post_url:
            row_num = i + 1
            impressions = metrics.get("impressions", "")
            likes = metrics.get("likes", "")
            comments = metrics.get("comments", "")
            shares = metrics.get("shares", "")
            eng_rate = ""
            if impressions and impressions > 0:
                total = (likes or 0) + (comments or 0) + (shares or 0)
                eng_rate = f"{(total / impressions * 100):.2f}%"

            updates = {
                "Impressions": impressions,
                "Likes": likes,
                "Comments": comments,
                "Shares": shares,
                "Engagement Rate": eng_rate,
                "Status": "POSTED",
            }
            for col_name, value in updates.items():
                col_idx = SHEET_HEADERS.index(col_name) + 1
                ws.update_cell(row_num, col_idx, value)

            print(f"  Metrics updated for row {row_num}")
            return

    print(f"  Post URL not found in sheet: {post_url}")


def read_recent_posts(days: int = 30) -> list[dict]:
    """Read all posts from the last N days for autoresearch."""
    client = get_client()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    ws = get_or_create_sheet(client, sheet_id, TAB_POSTS)
    records = ws.get_all_records()
    return records


def log_strategy_update(summary: str, date_str: str):
    """Log each weekly strategy update."""
    client = get_client()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    ws = get_or_create_sheet(client, sheet_id, TAB_STRATEGY)
    ensure_headers(ws, ["Date", "Strategy Summary"])
    ws.append_row([date_str, summary], value_input_option="USER_ENTERED")


if __name__ == "__main__":
    print("sheets_manager: run via main pipeline")
