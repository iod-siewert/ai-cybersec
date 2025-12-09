#!/usr/bin/env python3
import requests
from datetime import datetime
from db_plugins.scans_db import init_db, upsert_plugin

API_URL = "https://api.wordpress.org/plugins/info/1.2/"

def fetch_plugins(page: int = 1, per_page: int = 100):
    params = {
        "action": "query_plugins",
        "request[page]": page,
        "request[per_page]": per_page,
    }
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    init_db()
    total = 0
    # np. pierwsze 20 stron ~ 2000 wtyczek, możesz zwiększyć
    for page in range(1, 21):
        data = fetch_plugins(page=page)
        plugins = data.get("plugins", [])
        if not plugins:
            break
        for p in plugins:
            slug = p["slug"]
            name = p.get("name", slug)
            # repo SVN WordPressa
            repo_url = f"https://plugins.svn.wordpress.org/{slug}"
            vcs = "svn"
            upsert_plugin(slug, name, repo_url, vcs)
            total += 1
        print(f"[{datetime.utcnow().isoformat()}] page {page} -> {len(plugins)} plugins")
    print(f"Zapisano/uzupełniono {total} pluginów w bazie.")

if __name__ == "__main__":
    main()
