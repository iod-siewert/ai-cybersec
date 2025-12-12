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
    temp_base = Path(tempfile.mkdtemp(prefix=f"wp-scan-{slug}-"))
    temp_dir = temp_base / "trunk"  # Standaryzowana struktura
    
    try:
        print(f"Checkout {vcs.upper()}: [{repo_url}]({repo_url})")
        
        if vcs == "svn":
            cmd = ["svn", "checkout", f"{repo_url}/trunk", str(temp_base)]
        
        elif vcs in ["github", "gitlab", "bitbucket", "git"]:
            cmd = ["git", "clone", "--depth", "1", repo_url, str(temp_base)]
        
        else:  # unknown - fallback ZIP WP.org
            zip_url = f"https://downloads.wordpress.org/plugin/{slug}.latest.zip"
            zip_path = temp_base / f"{slug}.zip"
            cmd = ["wget", "-O", str(zip_path), zip_url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise Exception(f"Wget failed: {result.stderr}")
            
            # Rozpakuj i standaryzuj strukturę
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_base)
            zip_path.unlink()
            
            # Przenieś główny katalog do trunk/
            for child in temp_base.iterdir():
                if child.is_dir() and child.name.startswith(slug):
                    child.rename(temp_dir)
                    break
            else:
                # Jeśli brak głównego katalogu, użyj pierwszego
                for child in temp_base.iterdir():
                    if child.is_dir():
                        child.rename(temp_dir)
                        break
            return temp_dir
        
        # Wykonaj SVN/Git
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_timeout, cwd=str(temp_base.parent))
        if result.returncode != 0:
            raise Exception(f"Checkout failed:\n{result.stderr}\n{result.stdout}")
        
        # Dla Git - sprawdź czy jest trunk/main/master
        if vcs != "svn":
            git_dirs = ["trunk", "main", "master"]
            for dir_name in git_dirs:
                candidate = temp_base / dir_name
                if candidate.exists():
                    candidate.rename(temp_dir)
                    break
            else:
                # Użyj głównego katalogu repo
                for child in temp_base.iterdir():
                    if child.is_dir():
                        child.rename(temp_dir)
                        break
        
        # Licznik plików
        files_count = sum(1 for p in temp_dir.rglob('*') if p.is_file())
        print(f"Skanuję {files_count} plików z [{repo_url}]")
        
        return temp_dir
        
    except Exception as e:
        shutil.rmtree(temp_base, ignore_errors=True)
        raise Exception(f"Checkout {vcs} failed for {slug}: {e}")

def scan_plugin(slug: str, name: str, repo_url: str, vcs: str) -> tuple[str, int]:
    """Skanuje jeden plugin - zwraca (result, findings_count)"""
    temp_base = None
    try:
        temp_repo_dir = checkout_repo(slug, repo_url, vcs)
        
        # **KLUCZOWE**: przekaż Path, NIE string!
        findings = scan_repo(str(temp_repo_dir), max_files=30)  
        count = len(findings) if findings is not None else 0
        result = "ok" if count >= 0 else "error"
        return result, count
        
    except Exception as e:
        return f"error: {str(e)[:100]}", -1
    finally:
        if temp_base and Path(temp_base).exists():
            shutil.rmtree(Path(temp_base), ignore_errors=True)

def scan_batch(limit: int, resume_from: Optional[str] = None) -> None:
    init_db()
    plugins = get_next_plugins(limit=limit, resume_from=resume_from)
    if not plugins:
        print("Brak nieskanowanych pluginów w bazie.")
        return

    for slug, name, repo_url, vcs in plugins:
        print(f"\n=== [{slug}] {name} ({repo_url}) ===")
        result, count = scan_plugin(slug, name, repo_url, vcs)
        
        scanned_at = datetime.utcnow().isoformat()
        update_scan(slug, result, count, scanned_at)
        print(f"-> zapisano wynik: {result}, findings={count}, at={scanned_at}")

def main():
    parser = argparse.ArgumentParser(description="Batch OWASP scan for WP plugins (Git+SVN+ZIP)")
    parser.add_argument("--limit", type=int, default=10, help="Ile pluginów zeskanować")
    parser.add_argument("--resume-from", type=str, default=None, help="Kontynuuj od slug")
    args = parser.parse_args()
    scan_batch(args.limit, args.resume_from)

if __name__ == "__main__":
    main()
