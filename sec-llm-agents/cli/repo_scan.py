#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

from rich.console import Console
from rich.table import Table

# zapewnij, że katalog projektu jest na PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sec_agents.wp_specialist import WPSpecialist
from output.sarif_generator import findings_to_sarif

console = Console()


def scan_repo(repo_path: str, max_files: int = 30) -> List[Dict[str, Any]]:
    """
    Skanuje JUŻ POBRANE lokalne repozytorium.
    Oczekuje ścieżki katalogu (np. /tmp/wp-scan-foo-xxxx/trunk),
    NIE URL-a i NIE klonuje nic (git/svn).
    """
    base = Path(repo_path)
    if not base.exists() or not base.is_dir():
        raise ValueError(f"Repo path nie istnieje lub nie jest katalogiem: {base}")

    scanner = WPSpecialist()

    # Najpierw policz wszystkie pliki
    all_files: List[Path] = [p for p in base.rglob("*") if p.is_file()]
    console.print(f"[yellow]W repo {base} jest {len(all_files)} plików ogółem[/yellow]")

    # Wybierz tylko pliki kodu, bez limitu rozmiaru, do max_files
    code_files: List[Path] = []
    for path in all_files:
        if path.suffix.lower() in {".php", ".js", ".py"}:
            code_files.append(path)
            if len(code_files) >= max_files:
                break

    console.print(f"[bold]Skanuję {len(code_files)} plików z {base}[/bold]")

    all_findings: List[Dict[str, Any]] = []
    for path in code_files:
        rel = str(path.relative_to(base))
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # dobierz language na podstawie rozszerzenia
        ext = path.suffix.lower()
        if ext == ".php":
            lang = "php"
        elif ext == ".js":
            lang = "js"
        elif ext == ".py":
            lang = "python"
        else:
            lang = "php"

        findings = scanner.scan_wp_file(content, rel, lang)
        all_findings.extend(findings)

    return all_findings


def main() -> None:
    """
    Tryb standalone: teraz przyjmuje ŚCIEŻKĘ do lokalnego katalogu,
    a nie URL repo. To spójne z użyciem z batch_scan.py.
    """
    parser = argparse.ArgumentParser(
        description="WP plugin scanner dla lokalnego katalogu (bez git/svn checkout)"
    )
    parser.add_argument(
        "repo_path",
        help="Ścieżka do katalogu repo (np. /tmp/wp-scan-foo-xxxx/trunk)",
    )
    parser.add_argument("--max-files", type=int, default=30)
    parser.add_argument(
        "--output", choices=["summary", "json", "sarif"], default="summary"
    )
    args = parser.parse_args()

    try:
        findings = scan_repo(args.repo_path, args.max_files)
    except Exception as exc:
        console.print(f"[red]Błąd podczas skanowania: {exc}[/red]")
        sys.exit(1)

    if args.output == "summary":
        console.print(f"[green]Znaleziono {len(findings)} findings[/green]")
        table = Table(title="Findings")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Type")
        table.add_column("Severity")
        for f in findings[:50]:
            table.add_row(
                f.get("file", "?"),
                str(f.get("line", "?")),
                f.get("type", "?"),
                str(f.get("severity", "?")),
            )
        console.print(table)
    elif args.output == "json":
        print(json.dumps({"findings": findings}, indent=2))
    else:  # sarif
        print(findings_to_sarif(findings))


if __name__ == "__main__":
    main()
