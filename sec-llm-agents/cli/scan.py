#!/usr/bin/env python3
import argparse
from pathlib import Path

from sec_agents.wp_specialist import WPSpecialist

def main() -> None:
    parser = argparse.ArgumentParser(description="Scan single local file")
    parser.add_argument("path", help="Ścieżka do pliku PHP/JS")
    parser.add_argument("--language", default="php")
    args = parser.parse_args()

    p = Path(args.path)
    code = p.read_text(encoding="utf-8", errors="ignore")

    scanner = WPSpecialist()
    findings = scanner.scan_wp_file(code, str(p), args.language)

    print(f"Znaleziono {len(findings)} błędów")
    for f in findings:
        print(f"- {f['file']}:{f['line']} [{f['severity']}] {f['type']} – {f['desc']}")

if __name__ == "__main__":
    main()
