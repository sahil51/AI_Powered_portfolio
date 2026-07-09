from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.knowledge_ingestion.importer import KnowledgeImporter
from application.knowledge_ingestion.models import (
    ImportSource,
    ImportSourceType,
    KnowledgeImportResult,
    ParsedDocument,
)
from application.knowledge_ingestion.parsers.base import ParseResult
from application.knowledge_ingestion.processor import KnowledgeProcessor
from application.knowledge_ingestion.scheduler import (
    KnowledgeScheduler,
    SchedulePriority,
    ScheduleStatus,
)
from application.knowledge_ingestion.service import KnowledgeIngestionService
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.value_objects import (
    DocumentId,
    DocumentSource,
    DocumentType,
    KnowledgeVersion,
)


class TestKnowledgeProcessor:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.embedding_pipeline = MagicMock()
        self.embedding_pipeline.process_document.return_value = MagicMock(success=True)
        self.processor = KnowledgeProcessor(
            repository=self.repository,
            embedding_pipeline=self.embedding_pipeline,
        )

    def _make_parse_result(self, title: str = "Test", content: str = "") -> ParseResult:
        if not content:
            content = "Hello world. " * 50
        return ParseResult(title=title, content=content, word_count=len(content.split()), character_count=len(content))

    @pytest.mark.asyncio
    async def test_process_with_sync_embedding_pipeline(self) -> None:
        parse_result = self._make_parse_result()
        source = DocumentSource(filename="test.pdf", mime_type="application/pdf")
        result = await self.processor.process(
            parse_result=parse_result,
            source=source,
            doc_type=DocumentType.PDF,
            correlation_id="corr-1",
        )
        assert result.success is True
        assert result.document_id is not None
        self.repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_with_none_embedding_pipeline(self) -> None:
        processor = KnowledgeProcessor(repository=self.repository, embedding_pipeline=None)
        parse_result = self._make_parse_result()
        source = DocumentSource(filename="test.txt", mime_type="text/plain")
        result = await processor.process(
            parse_result=parse_result,
            source=source,
            doc_type=DocumentType.TXT,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_with_existing_document_duplicate_checksum(self) -> None:
        content = "Hello world. " * 50
        existing = KnowledgeDocument(
            document_id=DocumentId(),
            title="Test",
            checksum=self.processor._normalizer.normalize(
                ParsedDocument(title="Test", content=content)
            ).checksum,
            chunks=[KnowledgeChunk(text=content[:100])],
            version=KnowledgeVersion("1.0.0"),
        )

        parse_result = self._make_parse_result(content=content)
        source = DocumentSource(filename="test.pdf", mime_type="application/pdf")
        result = await self.processor.process(
            parse_result=parse_result,
            source=source,
            doc_type=DocumentType.PDF,
            existing_document=existing,
        )
        assert result.success is True
        assert result.document_id == existing.document_id
        assert result.version == "1.0.0"
        self.repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_cancellation(self) -> None:
        self.processor.cancel()
        parse_result = self._make_parse_result()
        source = DocumentSource(filename="test.pdf", mime_type="application/pdf")
        result = await self.processor.process(
            parse_result=parse_result,
            source=source,
            doc_type=DocumentType.PDF,
        )
        assert result.success is False
        assert "cancelled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_batch(self) -> None:
        items = [
            (self._make_parse_result("Doc1", "Hello world. " * 50), DocumentSource(filename="a.pdf"), DocumentType.PDF),
            (self._make_parse_result("Doc2", "Hello world. " * 50), DocumentSource(filename="b.pdf"), DocumentType.PDF),
        ]
        results = await self.processor.process_batch(items, correlation_id="batch-1")
        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_process_handles_validation_error(self) -> None:
        parse_result = self._make_parse_result(content="")
        parse_result.title = ""
        source = DocumentSource(filename="test.pdf", mime_type="application/pdf")
        result = await self.processor.process(
            parse_result=parse_result,
            source=source,
            doc_type=DocumentType.PDF,
        )
        assert result.success is False


class TestKnowledgeImporter:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.validator = KnowledgeImportValidator()
        self.processor = MagicMock()
        self.processor.process = AsyncMock()
        self.processor.process.return_value = KnowledgeImportResult(
            document_id=DocumentId(),
            success=True,
            chunk_count=3,
            version="1.0.0",
            checksum="abc",
        )
        self.importer = KnowledgeImporter(
            processor=self.processor,
            repository=self.repository,
            validator=self.validator,
        )

    @pytest.mark.asyncio
    async def test_import_document_with_source_validation(self) -> None:
        mock_parser = MagicMock()
        mock_parser.supports.return_value = True
        mock_parser.parse.return_value = ParseResult(title="test", content="Hello world. " * 50)
        self.importer.find_parser = MagicMock(return_value=mock_parser)
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="pdf content",
            mime_type="application/pdf",
        )
        result = await self.importer.import_document(
            source=source,
            doc_type=DocumentType.PDF,
            correlation_id="corr-1",
        )
        assert result.success is True
        self.processor.process.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_import_document_validation_failure(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.exe",
            content="bad",
        )
        result = await self.importer.import_document(
            source=source,
            correlation_id="corr-1",
        )
        assert result.success is False
        assert "Unsupported file extension" in result.error

    @pytest.mark.asyncio
    async def test_import_document_unsupported_extension(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.xyz",
            content="data",
            mime_type="application/x-xyz",
        )
        result = await self.importer.import_document(source=source)
        assert result.success is False
        assert "extension" in result.error

    @pytest.mark.asyncio
    async def test_import_batch(self) -> None:
        sources = [
            ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="a.pdf", content="a", mime_type="application/pdf"),
            ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="b.pdf", content="b", mime_type="application/pdf"),
        ]
        results = await self.importer.import_batch(sources, correlation_id="batch-1")
        assert len(results) == 2

    def test_find_parser_by_filename(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.md")
        parser = self.importer.find_parser(source)
        assert parser is not None
        from application.knowledge_ingestion.parsers import MarkdownParser
        assert isinstance(parser, MarkdownParser)

    def test_find_parser_by_mime_type(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, mime_type="text/html")
        parser = self.importer.find_parser(source)
        assert parser is not None
        from application.knowledge_ingestion.parsers import HTMLParser
        assert isinstance(parser, HTMLParser)

    def test_find_parser_no_match(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.unknown")
        assert self.importer.find_parser(source) is None


class TestKnowledgeScheduler:
    def setup_method(self) -> None:
        self.ingestion_service = MagicMock()
        self.ingestion_service.import_batch = AsyncMock()
        self.ingestion_service.import_batch.return_value = [
            KnowledgeImportResult(success=True),
        ]
        self.scheduler = KnowledgeScheduler(self.ingestion_service)

    def test_schedule_creates_job(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        job_id = self.scheduler.schedule([source], correlation_id="test-1")
        assert job_id is not None
        assert isinstance(job_id, str)
        job = self.scheduler.get_job(job_id)
        assert job is not None
        assert job.status == ScheduleStatus.SCHEDULED

    def test_schedule_with_priority(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        job_id = self.scheduler.schedule(
            [source], priority=SchedulePriority.HIGH, correlation_id="high-pri"
        )
        job = self.scheduler.get_job(job_id)
        assert job is not None
        assert job.priority == SchedulePriority.HIGH

    @pytest.mark.asyncio
    async def test_execute_pending(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        self.scheduler.schedule([source], correlation_id="exec-test")
        results = await self.scheduler.execute_pending()
        assert len(results) > 0
        self.ingestion_service.import_batch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_pending_no_ready_jobs(self) -> None:
        from datetime import datetime, timedelta
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        self.scheduler.schedule(
            [source],
            schedule_at=datetime.utcnow() + timedelta(hours=1),
            correlation_id="future",
        )
        results = await self.scheduler.execute_pending()
        assert results == []

    def test_cancel_job(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        job_id = self.scheduler.schedule([source], correlation_id="cancel-test")
        self.scheduler.cancel_job(job_id)
        job = self.scheduler.get_job(job_id)
        assert job is not None
        assert job.status == ScheduleStatus.CANCELLED

    def test_cancel_job_not_found(self) -> None:
        from application.knowledge_ingestion.exceptions import SchedulerError
        with pytest.raises(SchedulerError, match="Job not found"):
            self.scheduler.cancel_job("nonexistent")

    def test_get_failed_jobs(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        job_id = self.scheduler.schedule([source], correlation_id="fail-test")
        job = self.scheduler.get_job(job_id)
        job.status = ScheduleStatus.FAILED
        failed = self.scheduler.get_failed_jobs()
        assert len(failed) == 1
        assert failed[0].id == job_id

    def test_get_pending_count(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="data",
            mime_type="application/pdf",
        )
        self.scheduler.schedule([source], correlation_id="cnt-1")
        self.scheduler.schedule([source], correlation_id="cnt-2")
        assert self.scheduler.get_pending_count() == 2


class TestKnowledgeIngestionService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.validator = KnowledgeImportValidator()
        self.processor = MagicMock()
        self.processor.process = AsyncMock()
        self.importer = KnowledgeImporter(
            processor=self.processor,
            repository=self.repository,
            validator=self.validator,
        )
        self.service = KnowledgeIngestionService(
            importer=self.importer,
            validator=self.validator,
        )

    @pytest.mark.asyncio
    async def test_import_document_success(self) -> None:
        mock_parser = MagicMock()
        mock_parser.supports.return_value = True
        mock_parser.parse.return_value = ParseResult(title="test", content="Hello world. " * 50)
        self.importer.find_parser = MagicMock(return_value=mock_parser)
        self.processor.process.return_value = KnowledgeImportResult(
            document_id=DocumentId(),
            success=True,
            chunk_count=3,
            version="1.0.0",
            checksum="abc",
        )
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="test content",
            mime_type="application/pdf",
            size_bytes=100,
        )
        result = await self.service.import_document(
            source=source,
            doc_type=DocumentType.PDF,
            correlation_id="corr-1",
        )
        assert result.success is True
        assert result.document_id is not None

    @pytest.mark.asyncio
    async def test_import_document_failure(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.xyz",
            content="bad data",
        )
        result = await self.service.import_document(
            source=source,
            correlation_id="corr-2",
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_import_document_exception_handling(self) -> None:
        self.processor.process.side_effect = RuntimeError("Unexpected failure")
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            content="good content",
            mime_type="application/pdf",
            size_bytes=100,
        )
        result = await self.service.import_document(
            source=source,
            doc_type=DocumentType.PDF,
            correlation_id="corr-3",
        )
        assert result.success is False
        assert "Unexpected failure" in result.error or "Import failed" in result.error

    @pytest.mark.asyncio
    async def test_import_batch(self) -> None:
        self.processor.process.return_value = KnowledgeImportResult(success=True)
        sources = [
            ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="a.pdf", content="a", mime_type="application/pdf"),
            ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="b.pdf", content="b", mime_type="application/pdf"),
        ]
        results = await self.service.import_batch(sources, correlation_id="batch-1")
        assert len(results) == 2

    def test_health_check(self) -> None:
        health = self.service.health_check()
        assert "status" in health
        assert health["status"] == "healthy"

    def test_get_metrics(self) -> None:
        metrics = self.service.get_metrics()
        assert "total_imports" in metrics
        assert metrics["total_imports"] == 0

    def test_get_statistics(self) -> None:
        from application.knowledge_ingestion.models import ImportStatisticsData
        stats = self.service.get_statistics()
        assert isinstance(stats, ImportStatisticsData)

    def test_reset_metrics(self) -> None:
        self.service.reset_metrics()
        metrics = self.service.get_metrics()
        assert metrics["total_imports"] == 0

    def test_reset_statistics(self) -> None:
        self.service.reset_statistics()
        stats = self.service.get_statistics()
        assert stats.total_imports == 0
