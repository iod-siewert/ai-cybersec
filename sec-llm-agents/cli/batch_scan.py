#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional

import sys
from pathlib import Path
# zapewnij, że katalog projektu jest na PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_plugins_ai_sec.scans_db import init_db, get_next_plugins, update_scan
from cli.repo_scan import scan_repo  # używasz dotychczasowego kodu

def scan_batch(limit: int, resume_from: Optional[str] = None) -> None:
    init_db()
    plugins = get_next_plugins(limit=limit, resume_from=resume_from)
    if not plugins:
        print("Brak nieskanowanych pluginów w bazie.")
        return

    for slug, name, repo_url, vcs in plugins:
        print(f"\n=== [{slug}] {name} ({repo_url}) ===")
        try:
            findings = scan_repo(repo_url, max_files=30)
            count = len(findings)
            result = "ok" if count >= 0 else "error"
        except Exception as e:
            print(f"Scan error for {slug}: {e}")
            count = -1
            result = f"error: {e}"
        scanned_at = datetime.utcnow().isoformat()
        update_scan(slug, result, count, scanned_at)
        print(f"-> zapisano wynik: {result}, findings={count}, at={scanned_at}")

def main():
    parser = argparse.ArgumentParser(description="Batch OWASP scan for WP plugins (Git+SVN) with resume")
    parser.add_argument("--limit", type=int, default=10, help="Ile pluginów zeskanować w tej sesji")
    parser.add_argument("--resume-from", type=str, default=None,
                        help="Slug pluginu od którego kontynuować (wg porządku alfabetycznego)")
    args = parser.parse_args()
    scan_batch(args.limit, args.resume_from)

if __name__ == "__main__":
    main()
