from __future__ import annotations

import time
from typing import Any

from application.knowledge_ingestion.exceptions import (
    UnsupportedSourceError,
    ValidationError,
)
from application.knowledge_ingestion.models import (
    ImportSource,
    ImportSourceType,
    KnowledgeImportResult,
)
from application.knowledge_ingestion.parsers.base import BaseDocumentParser
from application.knowledge_ingestion.parsers.docx_parser import DOCXParser
from application.knowledge_ingestion.parsers.html_parser import HTMLParser
from application.knowledge_ingestion.parsers.markdown_parser import MarkdownParser
from application.knowledge_ingestion.parsers.pdf_parser import PDFParser
from application.knowledge_ingestion.parsers.txt_parser import TXTParser
from application.knowledge_ingestion.parsers.website_parser import WebsiteParser
from application.knowledge_ingestion.processor import KnowledgeProcessor
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from domain.knowledge.repository import KnowledgeRepository
from domain.knowledge.value_objects import DocumentSource, DocumentType


class KnowledgeImporter:
    def __init__(
        self,
        processor: KnowledgeProcessor,
        repository: KnowledgeRepository,
        validator: KnowledgeImportValidator | None = None,
    ) -> None:
        self._processor = processor
        self._repository = repository
        self._validator = validator or KnowledgeImportValidator()
        self._parsers: list[BaseDocumentParser] = [
            PDFParser(),
            DOCXParser(),
            MarkdownParser(),
            HTMLParser(),
            TXTParser(),
            WebsiteParser(),
        ]

    def register_parser(self, parser: BaseDocumentParser) -> None:
        self._parsers.append(parser)

    def find_parser(self, source: ImportSource) -> BaseDocumentParser | None:
        for parser in self._parsers:
            if parser.supports(source):
                return parser
        return None

    async def import_document(
        self,
        source: ImportSource,
        doc_type: DocumentType | None = None,
        correlation_id: str = "",
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> KnowledgeImportResult:
        start = time.monotonic()

        try:
            self._validator.validate_source(source)

            parser = self.find_parser(source)
            if parser is None:
                raise UnsupportedSourceError(
                    f"No parser found for source: {source.filename or source.url}"
                )

            resolved_doc_type = doc_type or self._resolve_doc_type(source, parser)

            parse_result = parser.parse(source)

            doc_source = DocumentSource(
                filename=source.filename,
                path=source.file_path,
                url=source.url,
                mime_type=source.mime_type,
                size_bytes=source.size_bytes,
                metadata=source.metadata,
            )

            existing = None
            if source.source_type == ImportSourceType.FILE_UPLOAD and source.filename:
                existing = await self._repository.get_by_title(parse_result.title)

            result = await self._processor.process(
                parse_result=parse_result,
                source=doc_source,
                doc_type=resolved_doc_type,
                correlation_id=correlation_id,
                tags=tags,
                existing_document=existing,
                **{k: v for k, v in kwargs.items() if k in ("chunking_strategy", "max_chunk_size", "chunk_overlap")},
            )

            result.latency_ms = (time.monotonic() - start) * 1000

            return result

        except (UnsupportedSourceError, ValidationError) as e:
            return KnowledgeImportResult(
                success=False,
                error=str(e),
                latency_ms=(time.monotonic() - start) * 1000,
                correlation_id=correlation_id,
            )
        except Exception as e:
            return KnowledgeImportResult(
                success=False,
                error=f"Import failed: {e}",
                latency_ms=(time.monotonic() - start) * 1000,
                correlation_id=correlation_id,
            )

    async def import_batch(
        self,
        sources: list[ImportSource],
        correlation_id: str = "",
        tags: list[str] | None = None,
    ) -> list[KnowledgeImportResult]:
        results: list[KnowledgeImportResult] = []
        for source in sources:
            result = await self.import_document(
                source=source,
                correlation_id=correlation_id,
                tags=tags,
            )
            results.append(result)
        return results

    def _resolve_doc_type(self, source: ImportSource, parser: BaseDocumentParser) -> DocumentType:
        if isinstance(parser, WebsiteParser):
            return DocumentType.WEBSITE
        if isinstance(parser, PDFParser):
            return DocumentType.PDF
        if isinstance(parser, DOCXParser):
            return DocumentType.DOCX
        if isinstance(parser, MarkdownParser):
            return DocumentType.MARKDOWN
        if isinstance(parser, HTMLParser):
            return DocumentType.HTML
        if isinstance(parser, TXTParser):
            return DocumentType.TXT
        return DocumentType.CUSTOM
