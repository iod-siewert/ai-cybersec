from typing import List, Dict, Any

from sec_agents.pattern_scanner import PatternScanner
from sec_agents.xss_scanner import XSSScanner


class WPSpecialist:
    """
    Warstwa dodająca prosty WP‑specyficzny post‑processing:
    - podbija severity dla braków nonce w AJAX
    - mapuje typy na OWASP
    """

    OWASP_MAP = {
        "sqli": "A03:2021-Injection",
        "rce": "A03:2021-Injection",
        "ssrf": "A10:2021-SSRF",
        "xss": "A07:2021-XSS",
        "secrets": "A09:2021-Security Misconfiguration",
        "path_traversal": "A05:2021-Security Misconfiguration",
        "nonce_missing": "A01:2021-Broken Access Control",
        "idor": "A01:2021-Broken Access Control",
        "info_disclosure": "A01:2021-Broken Access Control",
    }

    def __init__(self) -> None:
        self.pattern = PatternScanner()
        self.xss = XSSScanner()

    def scan_wp_file(self, code: str, filepath: str, language: str = "php") -> List[Dict[str, Any]]:
        # surowe findings z obu skanerów
        findings = self.pattern.scan(code, filepath, language) or []
        xss_findings = self.xss.scan(code, filepath, language) or []

        all_findings = findings + xss_findings

        enriched: List[Dict[str, Any]] = []
        for f in all_findings:
            f = dict(f)  # kopia defensywna

            # gwarantowane podstawowe pola
            f.setdefault("file", filepath)
            f.setdefault("line", 1)
            f.setdefault("type", "unknown")
            f.setdefault("severity", "info")

            t = f.get("type", "")
            if t in ("nonce_missing", "idor"):
                f["severity"] = "high"
            if t in self.OWASP_MAP:
                f["owasp"] = self.OWASP_MAP[t]

            enriched.append(f)

        return enriched
