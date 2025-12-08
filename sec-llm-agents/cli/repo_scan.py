#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import sys

import git
from rich.console import Console
from rich.table import Table

# zapewnij, że katalog projektu jest na PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sec_agents.wp_specialist import WPSpecialist
from output.sarif_generator import findings_to_sarif

console = Console()


def checkout_git(repo_url: str, dest: Path) -> None:
    """Klonuje repo Git do dest."""
    console.print(f"[blue]Klonuję repo Git: {repo_url}[/blue]")
    git.Repo.clone_from(repo_url, dest)


def checkout_svn(repo_url: str, dest: Path) -> None:
    """
    Checkout z SVN WordPressa.
    Jeśli użytkownik poda URL bez /trunk, dokładamy /trunk.
    """
    console.print(f"[blue]Checkout SVN: {repo_url}[/blue]")

    # jeśli to typowy URL WP plugins, a nie ma /trunk, dodaj
    if "plugins.svn.wordpress.org" in repo_url and not repo_url.rstrip("/").endswith("/trunk"):
        repo_url = repo_url.rstrip("/") + "/trunk"

    result = subprocess.run(
        ["svn", "checkout", repo_url, str(dest)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"svn checkout failed: {result.stderr}")


def detect_vcs(repo_url: str) -> str:
    """Proste wykrycie: git vs svn."""
    if "github.com" in repo_url or repo_url.endswith(".git"):
        return "git"
    if "plugins.svn.wordpress.org" in repo_url:
        return "svn"
    # domyślnie git
    return "git"


def scan_repo(repo_url: str, max_files: int = 30) -> List[Dict[str, Any]]:
    scanner = WPSpecialist()

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        vcs = detect_vcs(repo_url)
        if vcs == "git":
            checkout_git(repo_url, base)
        else:
            checkout_svn(repo_url, base)

        files: List[Path] = []
        for path in base.rglob("*"):
            if (
                path.is_file()
                and path.suffix in {".php", ".js", ".py"}
                and path.stat().st_size < 80_000
            ):
                files.append(path)
                if len(files) >= max_files:
                    break

        console.print(f"[bold]Skanuję {len(files)} plików z {repo_url}[/bold]")

        all_findings: List[Dict[str, Any]] = []
        for path in files:
            rel = str(path.relative_to(base))
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            findings = scanner.scan_wp_file(content, rel, "php")
            all_findings.extend(findings)

        return all_findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch WP plugin scanner (Git + SVN)")
    parser.add_argument("repo_url", help="Git lub SVN URL (np. https://github.com/... lub https://plugins.svn.wordpress.org/nazwa-wtyczki)")
    parser.add_argument("--max-files", type=int, default=30)
    parser.add_argument(
        "--output", choices=["summary", "json", "sarif"], default="summary"
    )
    args = parser.parse_args()

    try:
        findings = scan_repo(args.repo_url, args.max_files)
    except Exception as exc:
        console.print(f"[red]Błąd podczas checkout/scan: {exc}[/red]")
        sys.exit(1)

    if args.output == "summary":
        console.print(f"[green]Znaleziono {len(findings)} findings[/green]")
        table = Table(title="Findings")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Type")
        table.add_column("Severity")
        for f in findings[:50]:
            table.add_row(f["file"], str(f["line"]), f["type"], str(f["severity"]))
        console.print(table)
    elif args.output == "json":
        print(json.dumps({"findings": findings}, indent=2))
    else:  # sarif
        print(findings_to_sarif(findings))


if __name__ == "__main__":
    main()
