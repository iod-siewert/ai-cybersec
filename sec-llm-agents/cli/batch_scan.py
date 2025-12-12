#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional
import subprocess
import shutil
import tempfile
import sys
from pathlib import Path

# zapewnij, że katalog projektu jest na PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_plugins_ai_sec.scans_db import init_db, get_next_plugins, update_scan
from cli.repo_scan import scan_repo


def checkout_repo(slug: str, repo_url: str, vcs: str, max_timeout: int = 300) -> Path:
    """
    Pobiera repozytorium wg typu VCS.
    ZWRACA katalog bazowy checkoutu (np. /tmp/wp-scan-slug-xxxx),
    bez żadnego przenoszenia do trunk/main/master.
    """
    temp_base = Path(tempfile.mkdtemp(prefix=f"wp-scan-{slug}-"))

    try:
        print(f"Checkout {vcs.upper()}: [{repo_url}]")

        if vcs == "svn":
            # dla WP.org: repo_url = https://plugins.svn.wordpress.org/slug
            # checkout całego sluga (trunk, tags, branches)
            result = subprocess.run(
                ["svn", "checkout", repo_url, str(temp_base)],
                capture_output=True,
                text=True,
                timeout=max_timeout,
            )

        elif vcs in ["github", "gitlab", "bitbucket", "git"]:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_base)],
                capture_output=True,
                text=True,
                timeout=max_timeout,
            )

        else:
            # fallback: ZIP z WP.org
            zip_url = f"https://downloads.wordpress.org/plugin/{slug}.latest.zip"
            zip_path = temp_base / f"{slug}.zip"
            result = subprocess.run(
                ["wget", "-O", str(zip_path), zip_url],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise Exception(f"Wget failed: {result.stderr}")
            import zipfile
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_base)
            zip_path.unlink()

        if result.returncode != 0:
            raise Exception(f"Checkout failed:\n{result.stderr}")

        files_count = sum(1 for p in temp_base.rglob("*") if p.is_file())
        print(f"Skanuję {files_count} plików z [{repo_url}]")

        return temp_base

    except Exception as e:
        shutil.rmtree(temp_base, ignore_errors=True)
        raise Exception(f"Checkout {vcs} failed: {e}")


def scan_plugin(slug: str, name: str, repo_url: str, vcs: str) -> tuple[str, int]:
    """
    Skanuje jeden plugin: checkout -> scan_repo -> cleanup.
    """
    temp_base: Optional[Path] = None
    try:
        temp_base = checkout_repo(slug, repo_url, vcs)
        print(f"Wywołuję scan_repo({temp_base})")
        findings = scan_repo(str(temp_base), max_files=30)

        if findings is None:
            return "error: no findings", 0

        count = len(findings)
        return "ok", count

    except Exception as e:
        return f"error: {str(e)[:120]}", -1

    finally:
        if temp_base and temp_base.exists():
            # Usuń cały katalog tymczasowy
            shutil.rmtree(temp_base, ignore_errors=True)


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
        print(f"-> zapisano: {result}, findings={count}, at={scanned_at}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch OWASP scan for WP plugins (SVN/Git/ZIP)"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Ile pluginów zeskanować w tej sesji"
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Slug pluginu od którego kontynuować (alfabetycznie)",
    )
    args = parser.parse_args()
    scan_batch(args.limit, args.resume_from)


if __name__ == "__main__":
    main()
