#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional
import subprocess
import shutil
import tempfile
import sys
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_plugins_ai_sec.scans_db import init_db, get_next_plugins, update_scan
from cli.repo_scan import scan_repo

def checkout_repo(slug: str, repo_url: str, vcs: str, max_timeout: int = 300) -> Path:
    """Pobiera repozytorium wg typu VCS"""
    temp_base = Path(tempfile.mkdtemp(prefix=f"wp-scan-{slug}-"))
    
    try:
        print(f"Checkout {vcs.upper()}: [{repo_url}]({repo_url})")
        
        if vcs == "svn":
            result = subprocess.run(
                ["svn", "checkout", f"{repo_url}/trunk", str(temp_base)], 
                capture_output=True, text=True, timeout=max_timeout
            )
        
        elif vcs in ["github", "gitlab", "bitbucket", "git"]:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_base)], 
                capture_output=True, text=True, timeout=max_timeout
            )
        
        else:  # ZIP fallback
            zip_url = f"https://downloads.wordpress.org/plugin/{slug}.latest.zip"
            zip_path = temp_base / f"{slug}.zip"
            result = subprocess.run(
                ["wget", "-O", str(zip_path), zip_url], 
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_base)
                zip_path.unlink()
                
                # Standaryzuj strukturę do trunk/
                temp_dir = temp_base / "trunk"
                temp_dir.mkdir(exist_ok=True)
                for child in temp_base.iterdir():
                    if child.is_dir() and child != temp_dir:
                        shutil.move(str(child), str(temp_dir))
            else:
                raise Exception(f"Wget failed: {result.stderr}")
        
        if result.returncode != 0:
            raise Exception(f"Checkout failed:\n{result.stderr}")
        
        # Standaryzuj: wszystkie repo → trunk/
        temp_dir = temp_base / "trunk"
        if not temp_dir.exists():
            for candidate in ["trunk", "main", "master"]:
                cand_path = temp_base / candidate
                if cand_path.exists():
                    cand_path.rename(temp_dir)
                    break
            else:
                # Główny katalog repo
                for child in temp_base.iterdir():
                    if child.is_dir():
                        child.rename(temp_dir)
                        break
        
        files_count = sum(1 for p in temp_dir.rglob('*') if p.is_file())
        print(f"Skanuję {files_count} plików z [{repo_url}]")
        
        return temp_dir
        
    except Exception as e:
        shutil.rmtree(temp_base, ignore_errors=True)
        raise Exception(f"Checkout {vcs} failed: {e}")

def scan_plugin(slug: str, name: str, repo_url: str, vcs: str) -> tuple[str, int]:
    """Skanuje plugin - zwraca (result, count)"""
    temp_base = None
    try:
        repo_dir = checkout_repo(slug, repo_url, vcs)
        
        # **PRZEKAŻ TYLKO LOKALNY KATALOG - NIE URL**
        print(f"Wywołuję scan_repo({repo_dir})")
        findings = scan_repo(str(repo_dir), max_files=30)
        
        if findings is None:
            return "error: no findings", 0
        count = len(findings)
        return "ok", count
        
    except Exception as e:
        return f"error: {str(e)[:120]}", -1
    finally:
        # CZYSZCZENIE
        if temp_base and Path(temp_base).exists():
            shutil.rmtree(Path(temp_base), ignore_errors=True)

def scan_batch(limit: int, resume_from: Optional[str] = None) -> None:
    init_db()
    plugins = get_next_plugins(limit=limit, resume_from=resume_from)
    if not plugins:
        print("Brak nieskanowanych pluginów.")
        return

    for slug, name, repo_url, vcs in plugins:
        print(f"\n=== [{slug}] {name} ({repo_url}) ===")
        result, count = scan_plugin(slug, name, repo_url, vcs)
        
        scanned_at = datetime.utcnow().isoformat()
        update_scan(slug, result, count, scanned_at)
        print(f"-> zapisano: {result}, findings={count}, at={scanned_at}")

def main():
    parser = argparse.ArgumentParser(description="Batch scan WP plugins")
    parser.add_argument("--limit", type=int, default=10, help="Liczba pluginów")
    parser.add_argument("--resume-from", type=str, default=None, help="Kontynuuj od")
    args = parser.parse_args()
    scan_batch(args.limit, args.resume_from)

if __name__ == "__main__":
    main()
