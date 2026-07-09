from __future__ import annotations

import io
from typing import Any

from pypdf import PdfReader

from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult, Section


class PDFParser(BaseDocumentParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        if source.file_path:
            reader = PdfReader(source.file_path)
        elif source.content:
            content_bytes = source.content.encode("utf-8") if isinstance(source.content, str) else source.content
            reader = PdfReader(io.BytesIO(content_bytes))
        else:
            return ParseResult(title=source.filename or "Untitled")
        content_parts: list[str] = []
        sections: list[Section] = []
        metadata: dict[str, Any] = {}

        if reader.metadata:
            metadata = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "producer": reader.metadata.get("/Producer", ""),
                "page_count": len(reader.pages),
            }

        title = str(metadata.get("title", "")) or source.filename or "Untitled"

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = self._clean_text(text)
            content_parts.append(text)

            lines = text.splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped and len(stripped) < 200 and self._is_likely_heading(stripped):
                    sections.append(Section(
                        heading=stripped,
                        content="",
                        level=0,
                        metadata={"page": i + 1},
                    ))

        content = "\n\n".join(content_parts)

        return ParseResult(
            title=title,
            content=content,
            sections=sections,
            metadata=metadata,
            word_count=self._count_words(content),
            character_count=len(content),
        )

    def _clean_text(self, text: str) -> str:
        import re
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(\n\s*){3,}", "\n\n", text)
        return text.strip()

    def _is_likely_heading(self, text: str) -> bool:
        if len(text) < 2 or len(text) > 150:
            return False
        if text.endswith((".", "!", "?")):
            return False
        if text.isupper() and len(text) > 3:
            return True
        return False

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()
