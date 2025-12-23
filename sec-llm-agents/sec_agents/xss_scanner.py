from typing import List, Dict, Any
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from output.models import ScanResult


class XSSScanner:
    def __init__(self) -> None:
        # Możesz podmienić na mocniejszy model, np. gpt-4.1
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.parser = PydanticOutputParser(pydantic_object=ScanResult)

    def _load_template(self) -> str:
        path = Path("prompts/xss_scan.txt")
        return path.read_text(encoding="utf-8")

    def scan(self, code: str, filepath: str, language: str = "php") -> List[Dict[str, Any]]:
        format_instructions = self.parser.get_format_instructions()
        wp_context = (
            "WordPress plugin"
            if any(x in filepath.lower() for x in ["wp-content", "plugins", "plugin"])
            else "Web app"
        )

        # NIE używamy .format() na pliku, bo ma w sobie JSON z { }.
        # Wstrzykujemy tylko potrzebne rzeczy ręcznie.
        raw = self._load_template()

        # Prosta podmiana pięciu placeholderów, reszta treści zostaje nienaruszona.
        prompt = (
            raw
            .replace("{language}", language)
            .replace("{filepath}", filepath)
            .replace("{wp_context}", wp_context)
            .replace("{code}", code[:8000])
            .replace("{format_instructions}", format_instructions)
        )

        text = ""
        try:
            llm_result = self.llm.invoke(prompt)
            text = llm_result.content if hasattr(llm_result, "content") else str(llm_result)
            result: ScanResult = self.parser.parse(text)
        except Exception as exc:
            # DEBUG: pokaż dokładnie, co model zwrócił
            print(f"[xss_scanner] parse error for {filepath}: {exc}")
            if text:
                print("=== XSS RAW LLM OUTPUT BEGIN ===")
                print(text)
                print("=== XSS RAW LLM OUTPUT END ===")
            return []

        findings: List[Dict[str, Any]] = []
        for f in result.findings:
            d = f.model_dump()
            # wymuszamy typ i OWASP, bo to jest XSS‑only agent
            d["type"] = "xss"
            if not d.get("owasp"):
                d["owasp"] = "A07:2021-XSS"
            findings.append(d)

        return findings
