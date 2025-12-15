#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional, Tuple
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


def checkout_repo(slug: str, repo_url: str, vcs: str, max_timeout: int = 300) -> Tuple[Path, Path]:
    """
    Pobiera repozytorium wg typu VCS.
    ZWRACA (Path do kodu do skanowania, Path głównego katalogu do usunięcia).
    """
    temp_base_root = Path(tempfile.mkdtemp(prefix=f"wp-scan-{slug}-"))
    scan_path: Path
    result = None

    try:
        print(f"Checkout {vcs.upper()}: [{repo_url}]")

        if vcs == "svn":
            # Dla WP.org: repo_url = https://plugins.svn.wordpress.org/slug
            # Checkout całego sluga (trunk, tags, branches) do temp_base_root
            result = subprocess.run(
                ["svn", "checkout", repo_url, str(temp_base_root)],
                capture_output=True,
                text=True,
                timeout=max_timeout,
            )
            # Właściwy kod do skanowania jest w 'trunk' (POPRAWKA 1)
            scan_path = temp_base_root / "trunk"

        elif vcs in ["github", "gitlab", "bitbucket", "git"]:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_base_root)],
                capture_output=True,
                text=True,
                timeout=max_timeout,
            )
            scan_path = temp_base_root

        else:
            # fallback: ZIP z WP.org
            zip_url = f"https://downloads.wordpress.org/plugin/{slug}.latest.zip"
            zip_path = temp_base_root / f"{slug}.zip"
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
                zf.extractall(temp_base_root)
            zip_path.unlink()
            scan_path = temp_base_root

        if result and result.returncode != 0:
            raise Exception(f"Checkout failed:\n{result.stderr}")

        if not scan_path.exists():
             raise Exception(f"Brak katalogu kodu do skanowania: {scan_path}")

        files_count = sum(1 for p in scan_path.rglob("*") if p.is_file())
        print(f"Skanuję {files_count} plików z [{repo_url}] w katalogu {scan_path}")

        return scan_path, temp_base_root

    except Exception as e:
        shutil.rmtree(temp_base_root, ignore_errors=True)
        raise Exception(f"Checkout {vcs} failed: {e}")


def scan_plugin(slug: str, name: str, repo_url: str, vcs: str) -> tuple[str, int]:
    """
    Skanuje jeden plugin: checkout -> scan_repo -> cleanup.
    """
    scan_path: Optional[Path] = None
    temp_base_root: Optional[Path] = None
    try:
        # Odbierz ścieżkę do kodu i ścieżkę do usunięcia
        scan_path, temp_base_root = checkout_repo(slug, repo_url, vcs)
        print(f"Wywołuję scan_repo({scan_path})")
        # scan_repo dostaje poprawny katalog, np. /tmp/.../trunk
        findings = scan_repo(str(scan_path), max_files=30)

        if findings is None:
            return "error: no findings", 0

        count = len(findings)
        return "ok", count

    except Exception as e:
        error_msg = str(e).strip()
        print(f"Błąd skanowania dla {slug}: {error_msg}")
        return f"error: {error_msg[:120]}", -1

    finally:
        # Usuń cały katalog tymczasowy (POPRAWKA 2)
        if temp_base_root and temp_base_root.exists():
            shutil.rmtree(temp_base_root, ignore_errors=True)


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
    # POPRAWKA 3: naprawa literówki
    scan_batch(args.limit, args.resume_from)


if __name__ == "__main__":
    main()