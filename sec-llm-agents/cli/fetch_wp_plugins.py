#!/usr/bin/env python3
import requests
from datetime import datetime
import sys
import re
from pathlib import Path
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
        "fields": "homepage,name,slug,short_description"  # Kluczowe pola
    }
    try:
        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"Błąd API na stronie {page}: {e}")
        return {}

def is_svn_accessible(svn_url: str) -> bool:
    """Sprawdza czy SVN ma trunk z plikami źródłowymi"""
    try:
        r = requests.head(svn_url + "/trunk/", timeout=10, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

def detect_vcs_type(url: str) -> tuple[str, str]:
    """Zwraca (vcs_type, normalized_url)"""
    parsed = urlparse(url.lower())
    netloc = parsed.netloc
    
    if 'svn.wordpress.org' in netloc:
        return 'svn', url
    elif 'github.com' in netloc:
        return 'github', f"https://github.com{parsed.path.rstrip('/')}"
    elif 'gitlab.com' in netloc:
        return 'gitlab', url
    elif 'bitbucket.org' in netloc:
        return 'bitbucket', url
    elif any(x in netloc for x in ['git.', '.git']):
        return 'git', url
    else:
        return 'unknown', url

def find_best_repo(homepage: str, slug: str) -> tuple[str, str] | None:
    """Inteligentna detekcja repo z homepage"""
    if not homepage:
        return None
    
    homepage_lower = homepage.lower()
    
    # 1. Bezpośrednie wzorce VCS
    vcs_patterns = [
        r'(?:https?://)?(?:www\.)?(github\.com|gitlab\.com|bitbucket\.org)/([^/]+)/([^/]+?)(?:/|$)',
        r'(?:https?://)(?:[^/]+\.)?(git(?:lab|hub)\.com)/([^/]+)/([^/]+?)(?:/|$)',
    ]
    
    for pattern in vcs_patterns:
        match = re.search(pattern, homepage, re.IGNORECASE)
        if match:
            vcs_domain, user, repo = match.groups()
            base_url = f"https://{vcs_domain}/{user}/{repo}"
            return detect_vcs_type(base_url)
    
    # 2. Keywords wskazujące na source code
    source_keywords = ['/source/', '/repo/', '/git/', 'sourcecode', 'repository', '源码']
    for keyword in source_keywords:
        if keyword in homepage_lower:
            return detect_vcs_type(homepage)
    
    return None

def main():
    init_db()
    total = 0
    skipped = 0
    svn_count = 0
    github_count = 0
    other_count = 0
    
    print("Budowanie bazy repozytoriów WordPress plugins...")
    
    for page in range(1, 21):  # ~2000 popularnych wtyczek
        print(f"Pobieram stronę {page}...")
        data = fetch_plugins(page=page)
        plugins = data.get("plugins", [])
        
        if not plugins:
            print(f"Brak pluginów na stronie {page} - koniec")
            break
            
        for p in plugins:
            slug = p["slug"]
            name = p.get("name", slug)
            homepage = p.get("homepage", "")
            
            # 1. SVN - najwyższy priorytet (oficjalne WP)
            svn_url = f"https://plugins.svn.wordpress.org/{slug}"
            if is_svn_accessible(svn_url):
                repo_url = svn_url
                vcs = "svn"
                svn_count += 1
            # 2. Inne repo z homepage
            elif repo_info := find_best_repo(homepage, slug):
                vcs, repo_url = repo_info
                if vcs == "github":
                    github_count += 1
                else:
                    other_count += 1
            # 3. Fallback: SVN (nawet puste - batch_scan obsłuży)
            else:
                repo_url = svn_url
                vcs = "svn"
                skipped += 1
            
            upsert_plugin(slug, name, repo_url, vcs)
            total += 1
            
            # Rate limiting
            time.sleep(0.1)
        
        print(f"Strona {page}: {len(plugins)} pluginów "
              f"(total: {total}, SVN: {svn_count}, GitHub: {github_count}, inne: {other_count}, skip: {skipped})")
    
    print(f"\n=== PODSUMOWANIE ===")
    print(f"Zapisano: {total} pluginów")
    print(f"SVN: {svn_count}, GitHub: {github_count}, Inne: {other_count}")
    print(f"Puste SVN (skip): {skipped}")

if __name__ == "__main__":
    main()
