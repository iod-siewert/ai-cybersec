#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Dict, Any, List
import sys
import yaml

# ✅ DODAJ TO, zanim zaimportujesz sec_agents
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sec_agents.wp_specialist import WPSpecialist  # dostosuj do swojej nazwy pakietu


ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "corpus"
MANIFEST = ROOT / "manifest.yaml"


def load_manifest() -> List[Dict[str, Any]]:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def run_benchmark() -> None:
    cases = load_manifest()
    scanner = WPSpecialist()

    stats = {
        "total": 0,
        "tp": 0,
        "tn": 0,
        "fp": 0,
        "fn": 0,
        "per_type": {},
    }

    results: List[Dict[str, Any]] = []

    for case in cases:
        cid = case["id"]
        fname = case["file"]
        vtype = case["type"]
        expected = bool(case["expected"])

        fpath = CORPUS_DIR / fname
        code = fpath.read_text(encoding="utf-8", errors="ignore")

        findings = scanner.scan_wp_file(code, fname, "php")

        has_vuln = any(f["type"] == vtype for f in findings)

        stats["total"] += 1
        stats["per_type"].setdefault(vtype, {"tp": 0, "tn": 0, "fp": 0, "fn": 0})

        if expected and has_vuln:
            stats["tp"] += 1
            stats["per_type"][vtype]["tp"] += 1
            verdict = "TP"
        elif (not expected) and (not has_vuln):
            stats["tn"] += 1
            stats["per_type"][vtype]["tn"] += 1
            verdict = "TN"
        elif expected and (not has_vuln):
            stats["fn"] += 1
            stats["per_type"][vtype]["fn"] += 1
            verdict = "FN"
        else:  # not expected, but has_vuln
            stats["fp"] += 1
            stats["per_type"][vtype]["fp"] += 1
            verdict = "FP"

        results.append(
            {
                "id": cid,
                "file": fname,
                "type": vtype,
                "expected": expected,
                "has_vuln": has_vuln,
                "verdict": verdict,
                "findings": findings,
            }
        )

    print("=== Global stats ===")
    print(json.dumps(stats, indent=2))

    print("\n=== Per type ===")
    for vtype, s in stats["per_type"].items():
        print(f"- {vtype}: {s}")

    (ROOT / "benchmark_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print("\nSzczegóły zapisane w benchmark/benchmark_results.json")


if __name__ == "__main__":
    run_benchmark()
