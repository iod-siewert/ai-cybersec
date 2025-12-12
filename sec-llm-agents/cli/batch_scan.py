#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional
import subprocess
import shutil
import tempfile
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_plugins_ai_sec.scans_db import init_db, get_next_plugins, update_scan
from cli.repo_scan import scan_repo

def checkout_repo(slug: str, repo_url: str, vcs: str, max_timeout: int = 300) -> Path:
    """Pobiera repozytorium wg typu VCS do tymczasowego katalogu"""
    temp_dir = Path(tempfile.mkdtemp(prefix=f"wp-scan-{slug}-"))
    
    try:
        if vcs == "svn":
            cmd = ["svn", "checkout", f"{repo_url}/trunk", str(temp_dir)]
            print(f"Checkout SVN: [{repo_url}]({repo_url})")
        
        elif vcs in ["github", "gitlab", "bitbucket", "git"]:
            cmd = ["git", "clone", "--depth", "1", repo_url, str(temp_dir)]
            print(f"Clone Git: [{repo_url}]({repo_url})")
        
        else:  # unknown - fallback do ZIP WP.org
            zip_url = f"https://downloads.wordpress.org/plugin/{slug}.latest.zip"
            zip_path = temp_dir.parent / f"{slug}.zip"
            cmd = ["wget", "-O", str(zip_path), zip_url]
            print(f"Download ZIP: [{zip_url}]")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise Exception(f"Wget failed: {result.stderr}")
            
            # Rozpakuj ZIP
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            zip_path.unlink()  # Usuń ZIP
            # Przenieś główny katalog (np. plugin-slug-main -> trunk)
            for child in temp_dir.iterdir():
                if child.is_dir():
                    child.rename(temp_dir / "trunk")
                    break
            return temp_dir / "trunk"
        
        # Git/SVN checkout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_timeout)
        if result.returncode != 0:
            raise Exception(f"Checkout failed: {result.stderr}")
        
        files_count = sum(1 for p in temp_dir.rglob('*') if p.is_file())
        print(f"Skanuję {files_count} plików z [{repo_url}]")
        return temp_dir
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Checkout {vcs} failed for {slug}: {e}")

def scan_plugin(slug: str, name: str, repo_url: str, vcs: str) -> tuple[str, int]:
    """Skanuje jeden plugin z checkout + cleanup"""
    temp_repo_dir = None
    try:
        temp_repo_dir = checkout_repo(slug, repo_url, vcs)
        findings = scan_repo(str(temp_repo_dir), max_files=30)
        count = len(findings)
        result = "ok" if count >= 0 else "error"
        return result, count
    finally:
        if temp_repo_dir and temp_repo_dir.exists():
            shutil.rmtree(temp_repo_dir.parent, ignore_errors=True)

def scan_batch(limit: int, resume_from: Optional[str] = None) -> None:
    init_db()
    plugins = get_next_plugins(limit=limit, resume_from=resume_from)
    if not plugins:
        print("Brak nieskanowanych pluginów w bazie.")
        return

    for slug, name, repo_url, vcs in plugins:
        print(f"\n=== [{slug}] {name} ({repo_url}) ===")
        try:
            result, count = scan_plugin(slug, name, repo_url, vcs)
        except Exception as e:
            print(f"Scan error for {slug}: {e}")
            result = f"error: {e}"
            count = -1
        
        scanned_at = datetime.utcnow().isoformat()
        update_scan(slug, result, count, scanned_at)
        print(f"-> zapisano wynik: {result}, findings={count}, at={scanned_at}")

def main():
    parser = argparse.ArgumentParser(description="Batch OWASP scan for WP plugins (Git+SVN+ZIP) with resume")
    parser.add_argument("--limit", type=int, default=10, help="Ile pluginów zeskanować w tej sesji")
    parser.add_argument("--resume-from", type=str, default=None,
                        help="Slug pluginu od którego kontynuować (wg porządku alfabetycznego)")
    args = parser.parse_args()
    scan_batch(args.limit, args.resume_from)

if __name__ == "__main__":
    main()
