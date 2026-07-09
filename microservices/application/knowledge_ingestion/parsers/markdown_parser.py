from __future__ import annotations

from typing import Any

from markdown_it import MarkdownIt

from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult


class MarkdownParser(BaseDocumentParser):
    def __init__(self) -> None:
        self._md = MarkdownIt("commonmark", {"html": True})

    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["text/markdown", "text/x-markdown"]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        content = self._read_content(source)
        if not content:
            return ParseResult(title=source.filename or "Untitled")

        sections = self._extract_sections_from_markdown(content)
        title = source.filename or "Untitled"
        if sections and sections[0].heading and sections[0].level == 1:
            title = sections[0].heading

        metadata: dict[str, Any] = {}
        front_matter = self._extract_front_matter(content)
        if front_matter:
            metadata.update(front_matter)
            title = str(front_matter.get("title", title))

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

    def _extract_front_matter(self, text: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 3:
                front = text[3:end].strip()
                for line in front.splitlines():
                    if ":" in line:
                        key, _, val = line.partition(":")
                        metadata[key.strip()] = val.strip().strip('"').strip("'")
        return metadata

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()
