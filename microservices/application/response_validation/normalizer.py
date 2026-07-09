from __future__ import annotations

import re


class ResponseNormalizer:
    def normalize(self, content: str) -> str:
        result = content
        result = self._clean_whitespace(result)
        result = self._clean_formatting(result)
        return result

    def _clean_whitespace(self, content: str) -> str:
        result = content.strip()
        result = re.sub(r" +\n", "\n", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"[ \t]+", " ", result)
        return result

    def _clean_formatting(self, content: str) -> str:
        result = re.sub(r"\*\*\*\*", "**", content)
        result = re.sub(r"``````", "```", result)
        result = result.replace("\r\n", "\n")
        result = result.replace("\r", "\n")
        return result
