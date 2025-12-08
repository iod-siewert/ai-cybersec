from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from output.models import Finding, ScanResult
from typing import List, Dict, Any
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from output.models import ScanResult


class PatternScanner:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.parser = PydanticOutputParser(pydantic_object=ScanResult)

    def _load_raw_template(self) -> str:
        path = Path("prompts/pattern_scan.txt")  # lub wp_patterns.txt jeśli tak nazwałeś
        return path.read_text(encoding="utf-8")

    def scan(self, code: str, filepath: str, language: str = "php") -> List[Dict[str, Any]]:
        format_instructions = self.parser.get_format_instructions()

        wp_context = (
            "WordPress plugin"
            if any(x in filepath.lower() for x in ["wp-content", "plugins", "plugin"])
            else "Web app"
        )

        raw = self._load_raw_template()

        # ✅ JEDYNE formatowanie – uzupełniamy WSZYSTKIE placeholdery z pliku:
        filled_prompt = raw.format(
            language=language,
            filepath=filepath,
            wp_context=wp_context,
            code=code[:8000],
            format_instructions=format_instructions,
        )

        # Teraz wołamy model na gotowym stringu
        try:
            llm_result = self.llm.invoke(filled_prompt)
            text = llm_result.content if hasattr(llm_result, "content") else str(llm_result)
            result: ScanResult = self.parser.parse(text)

            findings: List[Dict[str, Any]] = []
            for f in result.findings:
                d = f.model_dump()
                if not d.get("owasp"):
                    d["owasp"] = "A09:2021-Security Misconfiguration"
                findings.append(d)
            return findings
        except Exception as exc:
            print(f"[pattern_scanner] error for {filepath}: {exc}")
            return []
