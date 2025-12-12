#!/usr/bin/env python3
import argparse
import requests
from datetime import datetime
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_plugins_ai_sec.scans_db import init_db, upsert_plugin

API_URL = "https://api.wordpress.org/plugins/info/1.2/"

def fetch_plugins(page: int = 1, per_page: int = 100):
    params = {
        "action": "query_plugins",
        "request[page]": page,
        "request[per_page]": per_page,
        "request[browse]": "popular",
        "request[fields][homepage]": True,
        "request[fields][name]": True,
        "request[fields][slug]": True,
    }
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser(description="Fetch WP plugins into DB")
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Numer strony z API (request[page])",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=100,
        help="Ilość pluginów na stronę (request[per_page])",
    )
    args = parser.parse_args()

    init_db()
    total = 0

    data = fetch_plugins(page=args.page, per_page=args.per_page)
    plugins = data.get("plugins", [])

    for p in plugins:
        slug = p["slug"]
        name = p.get("name", slug)
        repo_url = f"https://plugins.svn.wordpress.org/{slug}"
        vcs = "svn"
        upsert_plugin(slug, name, repo_url, vcs)
        total += 1

    print(
        f"[{datetime.utcnow().isoformat()}] page={args.page}, "
        f"per_page={args.per_page} -> zapisano {total} pluginów."
    )

if __name__ == "__main__":
    main()
