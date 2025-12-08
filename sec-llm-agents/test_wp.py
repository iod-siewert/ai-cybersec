#!/usr/bin/env python3
from cli.repo_scan import scan_repo

if __name__ == "__main__":
    repo = "https://github.com/wp-plugins/akismet"
    findings = scan_repo(repo_url=repo, max_files=10)
    print(f"AKISMET: {len(findings)} findings")
    for f in findings[:5]:
        print(f"{f['file']}:{f['line']} [{f['severity']}] {f['type']} – {f['desc']}")
