#!/usr/bin/env python3
"""
fetch_github_stats.py — pull public account + repo stats from the
unauthenticated GitHub REST API (api.github.com). No token needed;
this endpoint is public and rate-limited to 60 req/hour per IP,
which a once-daily cron comfortably fits inside.

Usage:
    python scripts/fetch_github_stats.py [username]

Writes data/github_stats.json:
    {
      "username", "generated_at",
      "public_repos", "followers", "following", "member_since",
      "total_stars", "top_languages": [{"name": "Python", "count": 7}, ...]
    }
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

DEFAULT_USERNAME = "MayankRathi14"
OUT_PATH = Path("data/github_stats.json")
API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "profile-art-bot/1.0",
}


def fetch_user(username: str) -> dict:
    resp = requests.get(f"{API}/users/{username}", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_all_repos(username: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME

    try:
        print(f"Fetching GitHub stats for {username} ...")
        user = fetch_user(username)
        repos = fetch_all_repos(username)
    except requests.exceptions.HTTPError as e:
        print(f"Warning: GitHub API request failed ({e}). "
              f"Leaving any existing {OUT_PATH} untouched.")
        sys.exit(0 if OUT_PATH.exists() else 1)

    non_fork = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in non_fork)

    lang_counts = Counter(r["language"] for r in non_fork if r.get("language"))
    top_languages = [{"name": name, "count": count}
                      for name, count in lang_counts.most_common(5)]

    created_at = user.get("created_at", "")
    member_since = created_at[:4] if created_at else "?"

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "member_since": member_since,
        "total_stars": total_stars,
        "top_languages": top_languages,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Done -> {OUT_PATH}  "
          f"(repos={payload['public_repos']}, stars={total_stars}, "
          f"followers={payload['followers']})")


if __name__ == "__main__":
    main()
