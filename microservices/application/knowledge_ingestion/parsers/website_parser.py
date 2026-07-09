from __future__ import annotations

from typing import Any

import httpx

from application.knowledge_ingestion.exceptions import ParsingError
from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult
from application.knowledge_ingestion.parsers.html_parser import _HTMLTextExtractor


class WebsiteParser(BaseDocumentParser):
    def __init__(self, timeout: float = 30.0, max_size_bytes: int = 5 * 1024 * 1024) -> None:
        self._timeout = timeout
        self._max_size_bytes = max_size_bytes

    @property
    def supported_extensions(self) -> list[str]:
        return [".html", ".htm", ""]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["text/html", "application/xhtml+xml"]

    def supports(self, source: ImportSource) -> bool:
        return bool(source.url) and source.source_type.value in ("url", "website")

    def parse(self, source: ImportSource) -> ParseResult:
        content = self._fetch_content(source)
        if not content:
            return ParseResult(title=source.url or "Untitled")

        extractor = _HTMLTextExtractor()
        extractor.feed(content)
        text = extractor.get_text()
        title = extractor.get_title() or source.url or "Untitled"

        sections = self._extract_sections_from_markdown(text)

        metadata: dict[str, Any] = {
            "source_url": source.url or "",
            "fetched_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

        return ParseResult(
            title=title,
            content=text,
            sections=sections,
            metadata=metadata,
            word_count=self._count_words(text),
            character_count=len(text),
        )

    def _fetch_content(self, source: ImportSource) -> str:
        if source.content:
            return source.content
        if not source.url:
            return ""
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                response = client.get(source.url)
                response.raise_for_status()
                content_length = len(response.content)
                if content_length > self._max_size_bytes:
                    raise ParsingError(
                        f"Response size {content_length} exceeds maximum {self._max_size_bytes}"
                    )
                return response.text
        except httpx.TimeoutException:
            raise ParsingError(f"Timeout fetching {source.url}")
        except httpx.HTTPStatusError as e:
            raise ParsingError(f"HTTP error fetching {source.url}: {e.response.status_code}")
        except httpx.RequestError as e:
            raise ParsingError(f"Request error fetching {source.url}: {e}")

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()
