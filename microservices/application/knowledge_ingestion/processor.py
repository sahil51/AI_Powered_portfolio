from __future__ import annotations

import time

from application.embedding.pipeline import EmbeddingPipeline
from application.knowledge_ingestion.deduplicator import KnowledgeDeduplicator
from application.knowledge_ingestion.exceptions import (
    DeduplicationError,
    IngestionCancelledError,
    NormalizationError,
    ParsingError,
    ValidationError,
)
from application.knowledge_ingestion.models import (
    KnowledgeImportResult,
    ParsedDocument,
)
from application.knowledge_ingestion.normalizer import KnowledgeNormalizer
from application.knowledge_ingestion.parsers.base import ParseResult
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from application.knowledge_ingestion.version_manager import KnowledgeVersionManager
from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.factory import KnowledgeFactory
from domain.knowledge.lifecycle import KnowledgeLifecycle
from domain.knowledge.repository import KnowledgeRepository
from domain.knowledge.value_objects import (
    ChunkId,
    ChunkingStrategy,
    DocumentSource,
    DocumentType,
    compute_checksum,
)


class KnowledgeProcessor:
    def __init__(
        self,
        repository: KnowledgeRepository,
        embedding_pipeline: EmbeddingPipeline | None = None,
        normalizer: KnowledgeNormalizer | None = None,
        deduplicator: KnowledgeDeduplicator | None = None,
        version_manager: KnowledgeVersionManager | None = None,
        validator: KnowledgeImportValidator | None = None,
        lifecycle: KnowledgeLifecycle | None = None,
        factory: KnowledgeFactory | None = None,
    ) -> None:
        self._repository = repository
        self._embedding_pipeline = embedding_pipeline
        self._normalizer = normalizer or KnowledgeNormalizer()
        self._deduplicator = deduplicator or KnowledgeDeduplicator()
        self._version_manager = version_manager or KnowledgeVersionManager()
        self._validator = validator or KnowledgeImportValidator()
        self._lifecycle = lifecycle or KnowledgeLifecycle()
        self._factory = factory or KnowledgeFactory()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _check_cancelled(self) -> None:
        if self._cancelled:
            raise IngestionCancelledError("Processing was cancelled")

    async def process(
        self,
        parse_result: ParseResult,
        source: DocumentSource,
        doc_type: DocumentType,
        correlation_id: str = "",
        tags: list[str] | None = None,
        existing_document: KnowledgeDocument | None = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        max_chunk_size: int = 2000,
        chunk_overlap: int = 200,
    ) -> KnowledgeImportResult:
        start = time.monotonic()
        result = KnowledgeImportResult(correlation_id=correlation_id)

        try:
            self._check_cancelled()

            parsed = ParsedDocument(
                title=parse_result.title,
                content=parse_result.content,
                metadata=parse_result.metadata,
                sections=[(s.heading, s.content, s.level) for s in parse_result.sections],
                language=parse_result.language,
                word_count=parse_result.word_count,
                character_count=parse_result.character_count,
            )

            self._validator.validate_parsed_document(parsed)

            self._check_cancelled()

            normalized = self._normalizer.normalize(parsed)

            self._check_cancelled()

            doc_checksum = normalized.checksum

            if existing_document and existing_document.checksum == doc_checksum:
                return KnowledgeImportResult(
                    document_id=existing_document.document_id,
                    success=True,
                    error="",
                    chunk_count=len(existing_document.chunks),
                    version=str(existing_document.version.value),
                    checksum=doc_checksum,
                    latency_ms=(time.monotonic() - start) * 1000,
                    correlation_id=correlation_id,
                )

            version_info = self._version_manager.create_version_info(existing_document, normalized)

            if existing_document is None:
                doc = self._factory.create(
                    title=normalized.title,
                    doc_type=doc_type,
                    source=source,
                    correlation_id=correlation_id,
                    tags=tags or [],
                )
                doc.checksum = doc_checksum
            else:
                doc = existing_document
                doc.title = normalized.title
                doc.checksum = doc_checksum
                doc.updated_at = __import__("datetime").datetime.utcnow()

            self._lifecycle.upload(doc)
            self._lifecycle.start_processing(doc)

            self._check_cancelled()

            chunks = self._create_chunks(
                doc=doc,
                content=normalized.content,
                sections=normalized.sections,
                strategy=chunking_strategy,
                max_size=max_chunk_size,
                overlap=chunk_overlap,
            )

            for chunk in chunks:
                self._lifecycle.chunk(doc, [chunk], chunking_strategy)

            self._check_cancelled()

            if version_info["needs_reprocess"] or not existing_document:
                if self._embedding_pipeline is not None:
                    embed_result = self._embedding_pipeline.process_document(doc)
                    if embed_result.success:
                        self._lifecycle.embed(doc)
                else:
                    self._lifecycle.embed(doc)

            self._check_cancelled()

            self._lifecycle.index(doc)
            self._lifecycle.activate(doc)

            await self._repository.save(doc)

            self._deduplicator.mark_processed(doc_checksum, str(doc.document_id.value))

            for chunk in doc.chunks:
                self._deduplicator.register_chunk_checksum(chunk.checksum, str(doc.document_id.value))

            self._check_cancelled()

            latency = (time.monotonic() - start) * 1000

            result = KnowledgeImportResult(
                document_id=doc.document_id,
                success=True,
                error="",
                chunk_count=len(chunks),
                version=version_info["new_version"],
                checksum=doc_checksum,
                latency_ms=latency,
                correlation_id=correlation_id,
            )

        except IngestionCancelledError:
            result.success = False
            result.error = "Processing cancelled"
        except (ValidationError, ParsingError, NormalizationError, DeduplicationError) as e:
            result.success = False
            result.error = str(e)
        except Exception as e:
            result.success = False
            result.error = f"Processing failed: {e}"

        result.latency_ms = (time.monotonic() - start) * 1000
        return result

    def _create_chunks(
        self,
        doc: KnowledgeDocument,
        content: str,
        sections: list[tuple[str, str, int]],
        strategy: ChunkingStrategy,
        max_size: int,
        overlap: int,
    ) -> list[KnowledgeChunk]:
        from application.embedding.chunking import ChunkerFactory

        chunker = ChunkerFactory.create(strategy, max_size=max_size, overlap=overlap)
        chunk_result = chunker.chunk(content)
        raw_chunks = chunk_result.chunks

        chunks: list[KnowledgeChunk] = []
        for i, chunk_text in enumerate(raw_chunks):
            section_heading = ""
            for heading, _content, _level in sections:
                if chunk_text.startswith(_content[:50]) if _content else False:
                    section_heading = heading
                    break

            chunk = KnowledgeChunk(
                chunk_id=ChunkId(),
                document_id=str(doc.document_id.value),
                chunk_index=i,
                text=chunk_text,
                token_count=len(chunk_text.split()),
                character_count=len(chunk_text),
                section=section_heading,
                heading=section_heading,
                checksum=compute_checksum(chunk_text),
                version=doc.version,
            )
            chunks.append(chunk)

        return chunks

    async def process_batch(
        self,
        items: list[tuple[ParseResult, DocumentSource, DocumentType]],
        correlation_id: str = "",
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        max_chunk_size: int = 2000,
        chunk_overlap: int = 200,
    ) -> list[KnowledgeImportResult]:
        results: list[KnowledgeImportResult] = []
        for parse_result, source, doc_type in items:
            result = await self.process(
                parse_result=parse_result,
                source=source,
                doc_type=doc_type,
                correlation_id=correlation_id,
                chunking_strategy=chunking_strategy,
                max_chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
            )
            results.append(result)
        return results
