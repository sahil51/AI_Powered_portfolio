from __future__ import annotations

import json
import re


class ResponseFormatter:
    def format_plain(self, content: str) -> str:
        return content.strip()

    def format_markdown(self, content: str) -> str:
        result = content.strip()
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"[ \t]+$", "", result, flags=re.MULTILINE)
        return result

    def format_json(self, content: str, pretty: bool = True) -> str:
        trimmed = content.strip()
        if not (trimmed.startswith("{") or trimmed.startswith("[")):
            return content
        try:
            parsed = json.loads(trimmed)
            if pretty:
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            return content

    def inject_citation(self, content: str, citation_number: int, citation_text: str) -> str:
        placeholder = "{{citation_placeholder}}"
        citation = f"[^{citation_number}]: {citation_text}"
        if placeholder in content:
            return content.replace(placeholder, citation)
        return content + f"\n\n{citation}"

    def inject_metadata(self, content: str, metadata: dict[str, str]) -> str:
        result = content
        for key, value in metadata.items():
            placeholder = "{{" + key + "}}"
            if placeholder in result:
                result = result.replace(placeholder, value)
        return result
