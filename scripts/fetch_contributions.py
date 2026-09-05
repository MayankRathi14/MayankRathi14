#!/usr/bin/env python3
"""
fetch_contributions.py — scrape the public contribution calendar
for a GitHub user, no token / no GraphQL API required.

GitHub serves the calendar as a public HTML fragment at:
    https://github.com/users/<username>/contributions
(the same markup the profile page itself embeds).

Usage:
    python scripts/fetch_contributions.py [username]

Writes data/contributions.json:
    {
      "username": "...",
      "generated_at": "...",
      "days": [{"date": "2025-09-04", "count": 3, "level": 2}, ...],
      "stats": {
        "total": 9376,
        "current_streak": 12,
        "longest_streak": 41,
        "best_day": {"date": "...", "count": 27},
        "monthly_totals": {"2025-09": 120, ...}
      }
    }
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "MayankRathi14"
URL_TMPL = "https://github.com/users/{username}/contributions"
OUT_PATH = Path("data/contributions.json")

HEADERS = {
    # A normal browser UA avoids odd edge-case responses from GitHub's fragment endpoint.
    "User-Agent": "Mozilla/5.0 (compatible; profile-art-bot/1.0; +https://github.com)"
}


def fetch_html(username: str) -> str:
    url = URL_TMPL.format(username=username)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td> (or <rect> in older markup) with
    # a data-date and data-level attribute. The human-readable count
    # ("3 contributions on September 4th.") lives in a separate
    # <tool-tip for="<cell-id>"> element, not inline on the cell itself,
    # so we build a lookup from cell id -> tooltip text first.
    tooltip_by_target = {}
    for tip in soup.find_all("tool-tip"):
        target_id = tip.get("for")
        if target_id:
            tooltip_by_target[target_id] = tip.get_text(strip=True)

    cells = soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day, td[data-date], rect[data-date]")

    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue

        level_raw = cell.get("data-level")
        level = int(level_raw) if level_raw is not None else None

        # Prefer the linked tooltip text; fall back to any inline
        # aria-label/title in case GitHub reverts to older markup.
        label = tooltip_by_target.get(cell.get("id"), "") or cell.get("aria-label") or cell.get("title") or ""
        count_match = re.search(r"(\d+|No)\s+contribution", label)
        if count_match:
            token = count_match.group(1)
            count = 0 if token == "No" else int(token)
        else:
            count = 0

        if level is None:
            # Fall back to a rough level from count if data-level is absent.
            if count == 0:
                level = 0
            elif count <= 3:
                level = 1
            elif count <= 6:
                level = 2
            elif count <= 9:
                level = 3
            else:
                level = 4

        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    best_day = max(days, key=lambda d: d["count"], default=None)
    best_day_out = {"date": best_day["date"], "count": best_day["count"]} if best_day else None

    # Streaks: consecutive days with count > 0, ending at the most recent day.
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    monthly_totals = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly_totals[month_key] += d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day_out,
        "monthly_totals": dict(sorted(monthly_totals.items())),
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME

    print(f"Fetching contribution calendar for {username} ...")
    html = fetch_html(username)

    print("Parsing days ...")
    days = parse_days(html)

    if not days:
        print("Warning: no contribution cells parsed — GitHub markup may have "
              "changed, or the request was blocked. Check the raw HTML.")
        sys.exit(1)

    stats = compute_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Done -> {OUT_PATH}  ({len(days)} days, {stats['total']} contributions)")


if __name__ == "__main__":
    main()
