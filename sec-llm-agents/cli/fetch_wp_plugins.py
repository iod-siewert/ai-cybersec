#!/usr/bin/env python3
import requests
from datetime import datetime
import sys
from pathlib import Path
import re
from urllib.parse import urlparse
import time

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
        # W 1.2 można przekazać fields jako tablicę lub string; wiele przykładów używa tablicy [web:8][web:59]
        "request[fields][homepage]": True,
        "request[fields][name]": True,
        "request[fields][slug]": True,
    }
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def extract_github_url(homepage: str) -> str | None:
    if not homepage:
        return None
    m = re.search(r'(?:https?://)?github\.com/([^/]+)/([^/]+?)(?:/|$)', homepage, re.IGNORECASE)
    if m:
        user, repo = m.groups()
        return f"https://github.com/{user}/{repo}"
    return None

def detect_alt_vcs(homepage: str) -> tuple[str, str] | None:
    """Opcjonalne wykrycie alternatywnego repo (GitHub/GitLab/Bitbucket itp.)."""
    if not homepage:
        return None

    parsed = urlparse(homepage)
    host = parsed.netloc.lower()

    # GitHub
    gh = extract_github_url(homepage)
    if gh:
        return "github", gh

    # GitLab / Bitbucket / ogólny git
    if "gitlab.com" in host:
        return "gitlab", homepage
    if "bitbucket.org" in host:
        return "bitbucket", homepage
    if host.startswith("git.") or host.endswith(".git"):
        return "git", homepage

    return None

def main():
    init_db()
    total = 0
    svn_count = 0
    alt_count = 0

    print("Buduję bazę pluginów (SVN + alternatywne repo)...")

    for page in range(1, 21):
        data = fetch_plugins(page=page)
        plugins = data.get("plugins", [])
        if not plugins:
            print(f"Strona {page}: brak pluginów, kończę.")
            break

        for p in plugins:
            slug = p["slug"]
            name = p.get("name", slug)
            homepage = p.get("homepage", "") or ""

            # 1. Główne repo ZAWSZE: oficjalny SVN WordPress.org [web:51][web:58]
            svn_url = f"https://plugins.svn.wordpress.org/{slug}"
            repo_url = svn_url
            vcs = "svn"
            svn_count += 1

            # 2. Opcjonalnie: alternatywne repo z homepage (GitHub, GitLab, Bitbucket)
            alt_vcs = None
            alt_repo_url = None
            alt = detect_alt_vcs(homepage)
            if alt:
                alt_vcs, alt_repo_url = alt
                alt_count += 1

            # upsert_plugin: rozszerz jeśli chcesz trzymać alt_repo_url/alt_vcs
            # Zakładam istniejący interfejs: upsert_plugin(slug, name, repo_url, vcs)
            # Jeśli chcesz, możesz zmodyfikować schemat bazy i dodać pola.
            upsert_plugin(slug, name, repo_url, vcs)

            total += 1

        print(
            f"[{datetime.utcnow().isoformat()}] page {page} -> {len(plugins)} "
            f"(total: {total}, svn: {svn_count}, alt_repos: {alt_count})"
        )
        time.sleep(0.3)  # delikatny rate-limit

    print(f"Zapisano {total} pluginów. SVN={svn_count}, z alt repo={alt_count}")

if __name__ == "__main__":
    main()
