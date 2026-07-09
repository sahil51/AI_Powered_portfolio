from __future__ import annotations

from typing import Any

from application.knowledge_ingestion.exceptions import ValidationError
from application.knowledge_ingestion.models import ImportSource, ImportSourceType, ParsedDocument
from domain.knowledge.value_objects import DocumentType


class KnowledgeImportValidator:
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
    MAX_CONTENT_LENGTH = 10_000_000
    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf", ".docx", ".txt", ".md", ".html", ".htm",
    }
    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "text/html",
        "text/x-markdown",
    }

    def validate_source(self, source: ImportSource) -> None:
        if source.source_type == ImportSourceType.FILE_UPLOAD:
            self._validate_file_source(source)
        elif source.source_type == ImportSourceType.URL:
            self._validate_url_source(source)
        elif source.source_type == ImportSourceType.WEBSITE:
            self._validate_website_source(source)
        elif source.source_type == ImportSourceType.API:
            self._validate_api_source(source)

    def _validate_file_source(self, source: ImportSource) -> None:
        if not source.file_path and not source.content:
            raise ValidationError("File source must have a file path or content")
        if source.size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size {source.size_bytes} exceeds maximum {self.MAX_FILE_SIZE_BYTES}"
            )
        ext = self._get_extension(source.filename or source.file_path)
        if ext and ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Unsupported file extension: {ext}")
        if source.mime_type and source.mime_type not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(f"Unsupported MIME type: {source.mime_type}")

    def _validate_url_source(self, source: ImportSource) -> None:
        if not source.url:
            raise ValidationError("URL source must have a URL")
        if not source.url.startswith(("http://", "https://")):
            raise ValidationError(f"Invalid URL: {source.url}")

    def _validate_website_source(self, source: ImportSource) -> None:
        if not source.url:
            raise ValidationError("Website source must have a URL")

    def _validate_api_source(self, source: ImportSource) -> None:
        if not source.content and not source.url:
            raise ValidationError("API source must have content or URL")

    def validate_parsed_document(self, doc: ParsedDocument) -> None:
        if not doc.title and not doc.content:
            raise ValidationError("Parsed document must have a title or content")
        if len(doc.content) > self.MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Content length {len(doc.content)} exceeds maximum {self.MAX_CONTENT_LENGTH}"
            )

    def validate_doc_type(self, doc_type: DocumentType) -> None:
        if doc_type == DocumentType.CUSTOM:
            raise ValidationError("Custom document type requires explicit configuration")

    def _get_extension(self, path: str) -> str:
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()

    def validate_metadata(self, metadata: dict[str, Any]) -> None:
        max_metadata_size = 1024 * 100
        serialized = str(metadata)
        if len(serialized) > max_metadata_size:
            raise ValidationError(f"Metadata too large ({len(serialized)} bytes)")
        for key in metadata:
            if not isinstance(key, str):
                raise ValidationError(f"Metadata key must be string, got {type(key)}")
            if len(key) > 256:
                raise ValidationError(f"Metadata key too long: {key[:50]}...")
