from typing import List, Dict, Any
import os
from pathlib import Path
import re # Nowy import

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException # Nowy import

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
        path = Path("prompts/pattern_scan.txt")
        return path.read_text(encoding="utf-8")

    def scan(self, code: str, filepath: str, language: str = "php") -> List[Dict[str, Any]]:
        format_instructions = self.parser.get_format_instructions()

        wp_context = (
            "WordPress plugin"
            if any(x in filepath.lower() for x in ["wp-content", "plugins", "plugin"])
            else "Web app"
        )

        raw = self._load_raw_template()

        # uzupełniamy wszystkie placeholdery z pliku
        filled_prompt = raw.format(
            language=language,
            filepath=filepath,
            wp_context=wp_context,
            code=code[:8000],
            format_instructions=format_instructions,
        )

        # wołamy model na gotowym stringu i parsujemy JSON
        try:
            llm_result = self.llm.invoke(filled_prompt)
            text = llm_result.content if hasattr(llm_result, "content") else str(llm_result)
            
            # Poprawka: usuń otaczający blok Markdown (```json...```)
            if text.strip().startswith('```'):
                text = re.sub(r"```json\n|```", "", text, flags=re.IGNORECASE).strip()

            result: ScanResult = self.parser.parse(text)
        except OutputParserException as exc:
            print(f"[pattern_scanner] parse error (OutputParserException) for {filepath}: {exc}")
            return []
        except Exception as exc:
            print(f"[pattern_scanner] generic parse error for {filepath}: {exc}")
            return []

        findings: List[Dict[str, Any]] = []
        for f in result.findings:
            d = f.model_dump()
            if not d.get("owasp"):
                d["owasp"] = "A09:2021-Security Misconfiguration"
            findings.append(d)

        return findings