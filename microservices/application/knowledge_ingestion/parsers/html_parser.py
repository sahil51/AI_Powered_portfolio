from __future__ import annotations

from html.parser import HTMLParser as StdlibHTMLParser
from typing import Any

from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult


class _HTMLTextExtractor(StdlibHTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._skip_tags: set[str] = {"script", "style", "nav", "footer", "header"}
        self._skip = False
        self._tag_stack: list[str] = []
        self._title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        if tag in self._skip_tags:
            self._skip = True
        if tag == "title":
            self._title = ""

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()
        if tag in self._skip_tags:
            self._skip = False
        if tag in ("p", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div"):
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == "title":
            self._title += data
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._text_parts.append(stripped + " ")

    def get_text(self) -> str:
        import re
        text = "".join(self._text_parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def get_title(self) -> str:
        return self._title.strip()


class HTMLParser(BaseDocumentParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["text/html"]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        content = self._read_content(source)
        if not content:
            return ParseResult(title=source.filename or "Untitled")

        extractor = _HTMLTextExtractor()
        extractor.feed(content)
        text = extractor.get_text()
        title = extractor.get_title() or source.filename or "Untitled"

        sections = self._extract_sections_from_markdown(text)

        metadata: dict[str, Any] = {
            "title": title,
            "source": source.url or source.file_path or "",
        }

        return ParseResult(
            title=title,
            content=text,
            sections=sections,
            metadata=metadata,
            word_count=self._count_words(text),
            character_count=len(text),
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
