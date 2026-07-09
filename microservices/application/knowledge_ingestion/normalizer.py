from __future__ import annotations

import re
import unicodedata
from typing import Any

from application.knowledge_ingestion.exceptions import NormalizationError
from application.knowledge_ingestion.models import NormalizedDocument, ParsedDocument
from domain.knowledge.value_objects import compute_checksum


class KnowledgeNormalizer:
    MAX_HEADING_LENGTH = 500
    MAX_TITLE_LENGTH = 1000

    def normalize(self, parsed: ParsedDocument) -> NormalizedDocument:
        try:
            content = self._normalize_whitespace(parsed.content)
            content = self._normalize_unicode(content)
            content = self._normalize_line_endings(content)
            content = self._remove_control_characters(content)

            title = parsed.title.strip()
            if len(title) > self.MAX_TITLE_LENGTH:
                title = title[: self.MAX_TITLE_LENGTH]

            sections = self._normalize_sections(parsed.sections)
            metadata = self._clean_metadata(parsed.metadata)

            checksum = compute_checksum(content)

            return NormalizedDocument(
                title=title,
                content=content.strip(),
                metadata=metadata,
                sections=sections,
                language=parsed.language or "en",
                checksum=checksum,
                word_count=len(content.split()),
                character_count=len(content),
            )
        except Exception as e:
            raise NormalizationError(f"Normalization failed: {e}") from e

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r"\t+", " ", text)
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    def _normalize_unicode(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        return text

    def _normalize_line_endings(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text

    def _remove_control_characters(self, text: str) -> str:
        chars: list[str] = []
        for ch in text:
            if ch == "\n" or ch == "\t":
                chars.append(ch)
            elif unicodedata.category(ch).startswith("C") and ch not in ("\n", "\t", "\r"):
                continue
            else:
                chars.append(ch)
        return "".join(chars)

    def _normalize_sections(
        self, sections: list[tuple[str, str, int]]
    ) -> list[tuple[str, str, int]]:
        result: list[tuple[str, str, int]] = []
        seen: set[str] = set()
        for heading, content, level in sections:
            heading = heading.strip()
            if not heading or heading in seen:
                continue
            if len(heading) > self.MAX_HEADING_LENGTH:
                heading = heading[: self.MAX_HEADING_LENGTH]
            seen.add(heading)
            result.append((heading, content.strip(), min(level, 6)))
        return result

    def _clean_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in metadata.items():
            str_key = str(key).strip()
            if not str_key:
                continue
            if isinstance(value, str):
                cleaned[str_key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                cleaned[str_key] = value
            elif isinstance(value, list):
                cleaned[str_key] = [str(v).strip() if isinstance(v, str) else v for v in value]
            elif isinstance(value, dict):
                cleaned[str_key] = self._clean_metadata(value)
            else:
                cleaned[str_key] = str(value).strip()
        return cleaned

    def normalize_batch(self, documents: list[ParsedDocument]) -> list[NormalizedDocument]:
        return [self.normalize(doc) for doc in documents]
