import json
from typing import List, Dict, Any

def findings_to_sarif(findings: List[Dict[str, Any]],
                      tool_name: str = "sec-llm-agents") -> str:
    level_map = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
    }

    results = []
    for f in findings:
        sev = str(f.get("severity", "medium"))
        level = level_map.get(sev, "warning")
        result = {
            "ruleId": f.get("type", "vuln"),
            "level": level,
            "message": {"text": f'{f["type"]}: {f["desc"]}'},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f["file"]},
                    "region": {"startLine": f["line"]}
                }
            }]
        }
        if f.get("cwe"):
            result.setdefault("properties", {})["tags"] = [f"CWE-{c}" for c in f["cwe"]]
        results.append(result)

    sarif = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": tool_name, "version": "0.1.0"}},
            "results": results,
            "columnKind": "utf16CodeUnits"
        }]
    }
    return json.dumps(sarif, indent=2)
