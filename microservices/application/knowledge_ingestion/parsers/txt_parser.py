from __future__ import annotations

from typing import Any

from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult


class TXTParser(BaseDocumentParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".txt"]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["text/plain"]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        content = self._read_content(source)
        if not content:
            return ParseResult(title=source.filename or "Untitled")

        title = source.filename or "Untitled"
        sections = self._extract_sections_from_markdown(content)

        metadata: dict[str, Any] = {
            "encoding": "utf-8",
        }

        return ParseResult(
            title=title,
            content=content,
            sections=sections,
            metadata=metadata,
            word_count=self._count_words(content),
            character_count=len(content),
        )

    def _read_content(self, source: ImportSource) -> str:
        if source.content:
            return source.content
        if source.file_path:
            with open(source.file_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()
