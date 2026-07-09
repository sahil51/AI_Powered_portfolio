from __future__ import annotations

import re
from typing import Any

import tiktoken

from application.knowledge_context.interfaces import KnowledgeContextCompressor as IKnowledgeContextCompressor
from application.knowledge_context.models import CompressionStrategy


class KnowledgeContextCompressor(IKnowledgeContextCompressor):
    def __init__(self, encoding: str = "cl100k_base") -> None:
        self._tokenizer: Any = None
        try:
            self._tokenizer = tiktoken.get_encoding(encoding)
        except Exception:
            self._tokenizer = None

    def compress(
        self,
        text: str,
        strategy: CompressionStrategy,
        max_tokens: int,
    ) -> tuple[str, int]:
        original_tokens = self.estimate_tokens(text)
        if original_tokens <= max_tokens:
            return text, 0

        if strategy == CompressionStrategy.TRUNCATE:
            return self._truncate(text, max_tokens)
        elif strategy == CompressionStrategy.EXTRACT:
            return self._extract_important(text, max_tokens)
        elif strategy == CompressionStrategy.PRIORITIZE:
            return self._prioritize_content(text, max_tokens)
        else:
            return self._truncate(text, max_tokens)

    def _truncate(self, text: str, max_tokens: int) -> tuple[str, int]:
        if self._tokenizer:
            tokens = self._tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text, 0
            truncated_tokens = tokens[:max_tokens]
            result = self._tokenizer.decode(truncated_tokens)
            saved = len(tokens) - len(truncated_tokens)
            return result, saved
        else:
            words = text.split()
            if len(words) <= max_tokens:
                return text, 0
            result = " ".join(words[:max_tokens])
            saved = len(words) - max_tokens
            return result, saved

    def _extract_important(self, text: str, max_tokens: int) -> tuple[str, int]:
        sections = re.split(r"\n#{1,6}\s", text)
        if len(sections) <= 1:
            return self._truncate(text, max_tokens)

        first_section = sections[0]
        first_tokens = self.estimate_tokens(first_section)
        if first_tokens >= max_tokens:
            return self._truncate(first_section, max_tokens)

        result_parts: list[str] = [first_section]
        current_tokens = first_tokens

        for section in sections[1:]:
            section_tokens = self.estimate_tokens(section)
            if current_tokens + section_tokens > max_tokens:
                remaining = max_tokens - current_tokens
                if remaining > 20:
                    truncated_section, _ = self._truncate(section, remaining)
                    result_parts.append(truncated_section)
                break
            result_parts.append(section)
            current_tokens += section_tokens

        result = "\n".join(result_parts)
        saved = self.estimate_tokens(text) - self.estimate_tokens(result)
        return result, saved

    def _prioritize_content(self, text: str, max_tokens: int) -> tuple[str, int]:
        lines = text.splitlines()
        prioritized: list[str] = []
        remaining_tokens = max_tokens

        high_priority: list[str] = []
        medium_priority: list[str] = []
        low_priority: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("**") or stripped.isupper():
                high_priority.append(line)
            elif len(stripped) > 100:
                medium_priority.append(line)
            else:
                low_priority.append(line)

        for priority_list in [high_priority, medium_priority]:
            for item in priority_list:
                tokens = self.estimate_tokens(item)
                if tokens <= remaining_tokens:
                    prioritized.append(item)
                    remaining_tokens -= tokens
                else:
                    break

        if remaining_tokens > 0:
            for item in low_priority:
                tokens = self.estimate_tokens(item)
                if tokens <= remaining_tokens:
                    prioritized.append(item)
                    remaining_tokens -= tokens
                else:
                    break

        result = "\n".join(prioritized)
        saved = self.estimate_tokens(text) - self.estimate_tokens(result)
        return result, max(0, saved)

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        return len(text.split())
