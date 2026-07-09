from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class DeduplicationStrategy:
    enabled: bool = True
    field_key: str = "content"
    max_duplicates: int = 1

    def deduplicate(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.enabled:
            return items
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for item in items:
            key = str(item.get(self.field_key, ""))
            if key not in seen:
                seen.add(key)
                result.append(item)
            elif len([r for r in result if str(r.get(self.field_key, "")) == key]) < self.max_duplicates:
                result.append(item)
        return result


@dataclass
class TruncationStrategy:
    enabled: bool = True
    max_tokens: int = 0
    truncation_field: str = "content"
    truncation_suffix: str = " [truncated]"
    preserve_head: bool = True

    def truncate(self, data: dict[str, Any], token_counter: Callable[[str], int]) -> dict[str, Any]:
        if not self.enabled or self.max_tokens <= 0:
            return data
        content = data.get(self.truncation_field, "")
        if isinstance(content, str) and token_counter(content) > self.max_tokens:
            if self.preserve_head:
                truncated = content[:self.max_tokens * 4] + self.truncation_suffix
            else:
                truncated = self.truncation_suffix + content[-self.max_tokens * 4:]
            data[self.truncation_field] = truncated
        return data


class ContextCompressionPolicy:
    def __init__(
        self,
        dedup: DeduplicationStrategy | None = None,
        truncation: TruncationStrategy | None = None,
    ) -> None:
        self._dedup = dedup or DeduplicationStrategy()
        self._truncation = truncation or TruncationStrategy()

    @property
    def dedup(self) -> DeduplicationStrategy:
        return self._dedup

    @property
    def truncation(self) -> TruncationStrategy:
        return self._truncation

    def compress(
        self,
        data: dict[str, Any],
        token_counter: Callable[[str], int] | None = None,
    ) -> dict[str, Any]:
        result = dict(data)
        if token_counter and self._truncation.enabled:
            result = self._truncation.truncate(result, token_counter)
        messages = result.get("messages", [])
        if isinstance(messages, list) and self._dedup.enabled:
            result["messages"] = self._dedup.deduplicate(messages)
        items = result.get("items", [])
        if isinstance(items, list) and self._dedup.enabled:
            result["items"] = self._dedup.deduplicate(items)
        return result
