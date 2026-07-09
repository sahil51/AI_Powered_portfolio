from __future__ import annotations

import re


class ResponseSanitizer:
    def __init__(self, pii_patterns: list[str] | None = None, sensitive_patterns: list[str] | None = None) -> None:
        self._pii_patterns = pii_patterns or [
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        ]
        self._sensitive_patterns = sensitive_patterns or [
            r"api[_-]?key[_\s:=]+['\"]?[A-Za-z0-9\-._~+/]{16,}['\"]?",
            r"bearer\s+[A-Za-z0-9\-._~+/]+",
        ]

    def sanitize(self, content: str) -> str:
        result = content
        result = self._redact_pii(result)
        result = self._redact_sensitive_data(result)
        result = self._remove_control_chars(result)
        return result

    def _redact_pii(self, content: str) -> str:
        for pattern in self._pii_patterns:
            content = re.sub(pattern, "[REDACTED]", content)
        return content

    def _redact_sensitive_data(self, content: str) -> str:
        for pattern in self._sensitive_patterns:
            content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)
        return content

    def _remove_control_chars(self, content: str) -> str:
        result = []
        for c in content:
            if ord(c) < 32 and c not in "\n\r\t":
                continue
            result.append(c)
        return "".join(result)
