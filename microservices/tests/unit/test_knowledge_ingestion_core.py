from __future__ import annotations

import pytest

from application.knowledge_ingestion.deduplicator import KnowledgeDeduplicator
from application.knowledge_ingestion.exceptions import ValidationError
from application.knowledge_ingestion.health import (
    KnowledgeImportHealthChecker,
)
from application.knowledge_ingestion.metrics import (
    IngestionMetrics,
    KnowledgeImportMetricsCollector,
)
from application.knowledge_ingestion.models import (
    ImportSource,
    ImportSourceType,
    ImportStatisticsData,
    NormalizedDocument,
    ParsedDocument,
)
from application.knowledge_ingestion.normalizer import KnowledgeNormalizer
from application.knowledge_ingestion.statistics import KnowledgeImportStatisticsCollector
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from application.knowledge_ingestion.version_manager import KnowledgeVersionManager
from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.value_objects import (
    DocumentType,
    KnowledgeVersion,
)


class TestKnowledgeNormalizer:
    def setup_method(self) -> None:
        self.normalizer = KnowledgeNormalizer()

    def test_normalize_whitespace(self) -> None:
        parsed = ParsedDocument(content="hello    world", title="test")
        result = self.normalizer.normalize(parsed)
        assert "hello    world" not in result.content

    def test_normalize_unicode(self) -> None:
        parsed = ParsedDocument(content="\u0065\u0301", title="test")
        result = self.normalizer.normalize(parsed)
        assert result.content == "\u00e9"

    def test_normalize_removes_control_characters(self) -> None:
        parsed = ParsedDocument(content="hello\x00world\x1f", title="test")
        result = self.normalizer.normalize(parsed)
        assert "hello" in result.content
        assert "world" in result.content
        assert "\x00" not in result.content
        assert "\x1f" not in result.content

    def test_normalize_preserves_newlines(self) -> None:
        parsed = ParsedDocument(content="line1\nline2", title="test")
        result = self.normalizer.normalize(parsed)
        assert "\n" in result.content
        assert "line1" in result.content
        assert "line2" in result.content

    def test_normalize_truncates_long_title(self) -> None:
        long_title = "a" * 2000
        parsed = ParsedDocument(content="content", title=long_title)
        result = self.normalizer.normalize(parsed)
        assert len(result.title) <= 1000

    def test_normalize_adds_checksum(self) -> None:
        parsed = ParsedDocument(content="hello world", title="test")
        result = self.normalizer.normalize(parsed)
        assert result.checksum != ""
        assert isinstance(result.checksum, str)

    def test_normalize_sets_language_default(self) -> None:
        parsed = ParsedDocument(content="hello", title="test")
        result = self.normalizer.normalize(parsed)
        assert result.language == "en"

    def test_normalize_preserves_language(self) -> None:
        parsed = ParsedDocument(content="bonjour", title="test", language="fr")
        result = self.normalizer.normalize(parsed)
        assert result.language == "fr"

    def test_normalize_counts_words_and_characters(self) -> None:
        parsed = ParsedDocument(content="three words here", title="test")
        result = self.normalizer.normalize(parsed)
        assert result.word_count == 3
        assert result.character_count == 16

    def test_normalize_cleans_metadata(self) -> None:
        parsed = ParsedDocument(
            content="content",
            title="test",
            metadata={"  key  ": "  value  ", "  ": "should be skipped"},
        )
        result = self.normalizer.normalize(parsed)
        assert "key" in result.metadata
        assert result.metadata["key"] == "value"
        assert "" not in result.metadata

    def test_normalize_batch(self) -> None:
        docs = [
            ParsedDocument(content="doc one", title="one"),
            ParsedDocument(content="doc two", title="two"),
        ]
        results = self.normalizer.normalize_batch(docs)
        assert len(results) == 2
        assert isinstance(results[0], NormalizedDocument)
        assert isinstance(results[1], NormalizedDocument)

    def test_normalize_returns_normalized_document(self) -> None:
        parsed = ParsedDocument(content="Hello world!", title="Test Doc")
        result = self.normalizer.normalize(parsed)
        assert isinstance(result, NormalizedDocument)
        assert result.title == "Test Doc"
        assert "Hello" in result.content
        assert result.checksum != ""

    def test_normalize_normalizes_sections_deduplicates(self) -> None:
        sections = [("Intro", "text", 1), ("Intro", "text", 1)]
        parsed = ParsedDocument(content="content", title="test", sections=sections)
        result = self.normalizer.normalize(parsed)
        assert len(result.sections) == 1

    def test_normalize_normalizes_sections_truncates_heading(self) -> None:
        long_heading = "a" * 1000
        sections = [(long_heading, "text", 1)]
        parsed = ParsedDocument(content="content", title="test", sections=sections)
        result = self.normalizer.normalize(parsed)
        assert len(result.sections[0][0]) <= 500


class TestKnowledgeDeduplicator:
    def setup_method(self) -> None:
        self.dedup = KnowledgeDeduplicator()

    def test_checksum_computation(self) -> None:
        cs1 = self.dedup.compute_checksum("hello world")
        cs2 = self.dedup.compute_checksum("hello world")
        cs3 = self.dedup.compute_checksum("different")
        assert cs1 == cs2
        assert cs1 != cs3
        assert isinstance(cs1, str)
        assert len(cs1) == 64

    def test_is_duplicate_not_found(self) -> None:
        assert self.dedup.is_duplicate("nonexistent") is False

    def test_is_duplicate_found(self) -> None:
        self.dedup.mark_processed("abc123", "doc-1")
        assert self.dedup.is_duplicate("abc123") is True

    def test_is_duplicate_same_document(self) -> None:
        self.dedup.mark_processed("abc123", "doc-1")
        assert self.dedup.is_duplicate("abc123", "doc-1") is False

    def test_mark_processed_then_check(self) -> None:
        self.dedup.mark_processed("checksum-1", "doc-1")
        self.dedup.mark_processed("checksum-2", "doc-2")
        assert self.dedup.is_duplicate("checksum-1") is True
        assert self.dedup.is_duplicate("checksum-2") is True
        assert self.dedup.is_duplicate("checksum-3") is False

    def test_find_duplicate_chunks_none(self) -> None:
        checksums = ["a", "b", "c"]
        result = self.dedup.find_duplicate_chunks(checksums)
        assert result == set()

    def test_find_duplicate_chunks_some(self) -> None:
        self.dedup.find_duplicate_chunks(["chunk-a"])
        result = self.dedup.find_duplicate_chunks(["chunk-a", "chunk-b"])
        assert result == {0}

    def test_find_duplicate_chunks_with_doc_id(self) -> None:
        self.dedup.find_duplicate_chunks(["chunk-a"], "doc-1")
        result = self.dedup.find_duplicate_chunks(["chunk-a", "chunk-b"], "doc-2")
        assert result == {0}

    def test_register_chunk_checksum(self) -> None:
        self.dedup.register_chunk_checksum("chk1", "doc-1")
        self.dedup.register_chunk_checksum("chk1", "doc-2")
        result = self.dedup.find_duplicate_chunks(["chk1", "chk2"], "doc-3")
        assert result == {0}

    def test_deduplicate_content_no_existing(self) -> None:
        result = self.dedup.deduplicate_content("new content")
        assert result == "new content"

    def test_deduplicate_content_removes_duplicates(self) -> None:
        existing = "line1\nline2\nline3"
        new_content = "line1\nline2\nnew_line\nline3"
        result = self.dedup.deduplicate_content(new_content, existing)
        assert "line1" not in result
        assert "line2" not in result
        assert "new_line" in result

    def test_clear(self) -> None:
        self.dedup.mark_processed("abc", "doc-1")
        self.dedup.clear()
        assert self.dedup.is_duplicate("abc") is False


class TestKnowledgeVersionManager:
    def setup_method(self) -> None:
        self.vm = KnowledgeVersionManager()

    def test_detect_changes_no_changes(self) -> None:
        existing = KnowledgeDocument(title="Same", checksum="abc")
        incoming = NormalizedDocument(title="Same", checksum="abc", metadata={"author": ""})
        changes = self.vm.detect_changes(existing, incoming)
        assert changes == []

    def test_detect_changes_title(self) -> None:
        existing = KnowledgeDocument(title="Old", checksum="abc")
        incoming = NormalizedDocument(title="New", checksum="abc")
        changes = self.vm.detect_changes(existing, incoming)
        assert "title_updated" in changes

    def test_detect_changes_content(self) -> None:
        existing = KnowledgeDocument(title="Same", checksum="old")
        incoming = NormalizedDocument(title="Same", checksum="new")
        changes = self.vm.detect_changes(existing, incoming)
        assert "content_updated" in changes

    def test_detect_changes_metadata(self) -> None:
        existing = KnowledgeDocument(
            title="Same",
            checksum="abc",
            metadata=KnowledgeMetadata(author="old_author", description="old_desc"),
        )
        incoming = NormalizedDocument(title="Same", checksum="abc", metadata={"author": "new_author", "description": "new_desc"})
        changes = self.vm.detect_changes(existing, incoming)
        assert "metadata_updated" in changes

    def test_bump_version_major_for_content(self) -> None:
        result = self.vm.bump_version("1.0.0", ["content_updated"])
        assert result == "1.1.0"

    def test_bump_version_patch_for_title(self) -> None:
        result = self.vm.bump_version("1.0.0", ["title_updated"])
        assert result == "1.0.1"

    def test_bump_version_patch_for_metadata(self) -> None:
        result = self.vm.bump_version("1.0.0", ["metadata_updated"])
        assert result == "1.0.1"

    def test_bump_version_no_changes(self) -> None:
        result = self.vm.bump_version("1.2.3", [])
        assert result == "1.2.3"

    def test_bump_version_invalid_version(self) -> None:
        result = self.vm.bump_version("invalid", ["content_updated"])
        assert result == "1.0.0"

    def test_should_reprocess_true_for_content(self) -> None:
        existing = KnowledgeDocument(title="Same", checksum="old")
        assert self.vm.should_reprocess(existing, ["content_updated"]) is True

    def test_should_reprocess_false_for_title(self) -> None:
        existing = KnowledgeDocument(title="Same", checksum="old")
        assert self.vm.should_reprocess(existing, ["title_updated"]) is False

    def test_create_version_info_new_document(self) -> None:
        incoming = NormalizedDocument(title="New", content="hello", checksum="abc")
        info = self.vm.create_version_info(None, incoming)
        assert info["old_version"] == "0.0.0"
        assert info["new_version"] == "0.0.0"
        assert info["needs_reprocess"] is True
        assert info["changes"] == []

    def test_create_version_info_existing_no_changes(self) -> None:
        existing = KnowledgeDocument(title="Same", checksum="abc", metadata=KnowledgeMetadata())
        incoming = NormalizedDocument(title="Same", checksum="abc", metadata={})
        info = self.vm.create_version_info(existing, incoming)
        assert info["old_version"] == "1.0.0"
        assert info["new_version"] == "1.0.0"
        assert info["needs_reprocess"] is False

    def test_create_version_info_existing_with_changes(self) -> None:
        existing = KnowledgeDocument(
            title="Old",
            checksum="old",
            metadata=KnowledgeMetadata(),
            version=KnowledgeVersion("1.0.0"),
        )
        incoming = NormalizedDocument(title="New", checksum="new", metadata={})
        info = self.vm.create_version_info(existing, incoming)
        assert info["old_version"] == "1.0.0"
        assert info["needs_reprocess"] is True

    def test_apply_version(self) -> None:
        doc = KnowledgeDocument(title="Test")
        result = self.vm.apply_version(doc, "2.0.0")
        assert result.version.value == "2.0.0"
        assert result.updated_at is not None


class TestKnowledgeImportValidator:
    def setup_method(self) -> None:
        self.validator = KnowledgeImportValidator()

    def test_validate_source_file_valid(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            file_path="test.pdf",
            filename="test.pdf",
            mime_type="application/pdf",
            size_bytes=1000,
        )
        self.validator.validate_source(source)

    def test_validate_source_file_no_path_or_content(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD)
        with pytest.raises(ValidationError, match="File source must have a file path or content"):
            self.validator.validate_source(source)

    def test_validate_source_file_exceeds_max_size(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            file_path="test.pdf",
            size_bytes=200 * 1024 * 1024,
        )
        with pytest.raises(ValidationError, match="exceeds maximum"):
            self.validator.validate_source(source)

    def test_validate_source_file_bad_extension(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.exe",
            content="data",
        )
        with pytest.raises(ValidationError, match="Unsupported file extension"):
            self.validator.validate_source(source)

    def test_validate_source_file_bad_mime(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.FILE_UPLOAD,
            filename="test.pdf",
            mime_type="application/x-bad",
            content="data",
        )
        with pytest.raises(ValidationError, match="Unsupported MIME type"):
            self.validator.validate_source(source)

    def test_validate_source_url_valid(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.URL,
            url="https://example.com/doc.pdf",
        )
        self.validator.validate_source(source)

    def test_validate_source_url_missing(self) -> None:
        source = ImportSource(source_type=ImportSourceType.URL)
        with pytest.raises(ValidationError, match="URL source must have a URL"):
            self.validator.validate_source(source)

    def test_validate_source_url_invalid_scheme(self) -> None:
        source = ImportSource(
            source_type=ImportSourceType.URL,
            url="ftp://example.com/doc.pdf",
        )
        with pytest.raises(ValidationError, match="Invalid URL"):
            self.validator.validate_source(source)

    def test_validate_source_website_missing_url(self) -> None:
        source = ImportSource(source_type=ImportSourceType.WEBSITE)
        with pytest.raises(ValidationError, match="Website source must have a URL"):
            self.validator.validate_source(source)

    def test_validate_parsed_document_valid(self) -> None:
        doc = ParsedDocument(title="Test", content="Hello world")
        self.validator.validate_parsed_document(doc)

    def test_validate_parsed_document_empty(self) -> None:
        doc = ParsedDocument()
        with pytest.raises(ValidationError, match="must have a title or content"):
            self.validator.validate_parsed_document(doc)

    def test_validate_parsed_document_too_long(self) -> None:
        doc = ParsedDocument(title="Test", content="x" * 20_000_000)
        with pytest.raises(ValidationError, match="exceeds maximum"):
            self.validator.validate_parsed_document(doc)

    def test_validate_doc_type_custom_raises(self) -> None:
        with pytest.raises(ValidationError, match="Custom document type requires explicit configuration"):
            self.validator.validate_doc_type(DocumentType.CUSTOM)

    def test_validate_doc_type_pdf_ok(self) -> None:
        self.validator.validate_doc_type(DocumentType.PDF)

    def test_validate_metadata_valid(self) -> None:
        self.validator.validate_metadata({"author": "test", "version": "1.0"})

    def test_validate_metadata_non_string_key(self) -> None:
        with pytest.raises(ValidationError, match="Metadata key must be string"):
            self.validator.validate_metadata({1: "value"})

    def test_validate_metadata_key_too_long(self) -> None:
        with pytest.raises(ValidationError, match="Metadata key too long"):
            self.validator.validate_metadata({"a" * 300: "value"})

    def test_validate_metadata_too_large(self) -> None:
        large = {"key": "x" * 200_000}
        with pytest.raises(ValidationError, match="Metadata too large"):
            self.validator.validate_metadata(large)


class TestKnowledgeImportHealthChecker:
    def setup_method(self) -> None:
        self.checker = KnowledgeImportHealthChecker()

    def test_initial_health(self) -> None:
        status = self.checker.check()
        assert status["status"] == "healthy"
        assert status["total_imports"] == 0
        assert status["failed_imports"] == 0
        assert status["consecutive_failures"] == 0
        assert status["success_rate"] == 1.0

    def test_record_success_resets_failures(self) -> None:
        self.checker.record_failure("error1")
        self.checker.record_failure("error2")
        self.checker.record_success()
        status = self.checker.check()
        assert status["consecutive_failures"] == 0
        assert status["status"] == "healthy"

    def test_record_failure_transitions_to_degraded(self) -> None:
        for _ in range(5):
            self.checker.record_failure("error")
        status = self.checker.check()
        assert status["status"] == "degraded"
        assert status["consecutive_failures"] == 5

    def test_record_failure_transitions_to_unhealthy(self) -> None:
        for _ in range(20):
            self.checker.record_failure("error")
        status = self.checker.check()
        assert status["status"] == "unhealthy"

    def test_success_rate_calculation(self) -> None:
        self.checker.record_success()
        self.checker.record_success()
        self.checker.record_failure("err")
        status = self.checker.check()
        assert status["success_rate"] == pytest.approx(2.0 / 3.0)

    def test_success_rate_no_imports(self) -> None:
        assert self.checker._calculate_success_rate() == 1.0

    def test_reset(self) -> None:
        self.checker.record_failure("err")
        self.checker.reset()
        status = self.checker.check()
        assert status["total_imports"] == 0
        assert status["status"] == "healthy"


class TestKnowledgeImportMetricsCollector:
    def setup_method(self) -> None:
        self.collector = KnowledgeImportMetricsCollector()

    def test_initial_metrics(self) -> None:
        metrics = self.collector.get_metrics()
        assert metrics["total_imports"] == 0
        assert metrics["successful_imports"] == 0
        assert metrics["failed_imports"] == 0
        assert metrics["total_chunks_created"] == 0

    def test_record_import_increments_counters(self) -> None:
        self.collector.record_import(
            source_type="file_upload",
            doc_type="pdf",
            latency_ms=100.0,
            chunk_count=5,
            bytes_processed=1000,
        )
        metrics = self.collector.get_metrics()
        assert metrics["total_imports"] == 1
        assert metrics["successful_imports"] == 1
        assert metrics["total_chunks_created"] == 5
        assert metrics["total_bytes_processed"] == 1000
        assert metrics["average_latency_ms"] == 100.0
        assert metrics["peak_latency_ms"] == 100.0

    def test_record_import_tracks_peak_latency(self) -> None:
        self.collector.record_import("file", "pdf", 50.0, 1, 100)
        self.collector.record_import("file", "pdf", 200.0, 1, 100)
        metrics = self.collector.get_metrics()
        assert metrics["average_latency_ms"] == 125.0
        assert metrics["peak_latency_ms"] == 200.0

    def test_record_import_tracks_by_source(self) -> None:
        self.collector.record_import("website", "html", 10.0, 2, 500)
        self.collector.record_import("website", "html", 20.0, 3, 600)
        metrics = self.collector.get_metrics()
        assert metrics["imports_by_source"].get("website:html") == 2

    def test_record_failure_increments_failed(self) -> None:
        self.collector.record_failure("file_upload", "Parsing error")
        metrics = self.collector.get_metrics()
        assert metrics["total_imports"] == 1
        assert metrics["failed_imports"] == 1
        assert metrics["successful_imports"] == 0

    def test_record_failure_tracks_error_type(self) -> None:
        self.collector.record_failure("file_upload", "Parsing error")
        self.collector.record_failure("file_upload", "Parsing error")
        self.collector.record_failure("file_upload", "Validation error")
        metrics = self.collector.get_metrics()
        assert metrics["failures_by_error"].get("Parsing error") == 2
        assert metrics["failures_by_error"].get("Validation error") == 1

    def test_reset(self) -> None:
        self.collector.record_import("file", "pdf", 10.0, 1, 100)
        self.collector.reset()
        metrics = self.collector.get_metrics()
        assert metrics["total_imports"] == 0

    def test_metrics_property(self) -> None:
        assert isinstance(self.collector.metrics, IngestionMetrics)


class TestKnowledgeImportStatisticsCollector:
    def setup_method(self) -> None:
        self.collector = KnowledgeImportStatisticsCollector()

    def test_initial_statistics(self) -> None:
        stats = self.collector.get_statistics()
        assert isinstance(stats, ImportStatisticsData)
        assert stats.total_imports == 0

    def test_record_import_success(self) -> None:
        self.collector.record_import(
            source_type="file_upload",
            doc_type="pdf",
            success=True,
            chunk_count=5,
            bytes_processed=1000,
            latency_ms=50.0,
        )
        stats = self.collector.get_statistics()
        assert stats.total_imports == 1
        assert stats.successful_imports == 1
        assert stats.failed_imports == 0
        assert stats.total_chunks == 5
        assert stats.total_bytes == 1000
        assert stats.total_latency_ms == 50.0

    def test_record_import_failure(self) -> None:
        self.collector.record_import(
            source_type="file_upload",
            doc_type="pdf",
            success=False,
        )
        stats = self.collector.get_statistics()
        assert stats.total_imports == 1
        assert stats.successful_imports == 0
        assert stats.failed_imports == 1

    def test_record_import_tracks_by_source_and_type(self) -> None:
        self.collector.record_import("website", "html", True)
        self.collector.record_import("file_upload", "pdf", True)
        self.collector.record_import("website", "html", False)
        stats = self.collector.get_statistics()
        assert stats.imports_by_source["website"] == 2
        assert stats.imports_by_source["file_upload"] == 1
        assert stats.imports_by_type["html"] == 2
        assert stats.imports_by_type["pdf"] == 1

    def test_record_failure_by_error_type(self) -> None:
        self.collector.record_failure("ParsingError")
        self.collector.record_failure("ParsingError")
        self.collector.record_failure("ValidationError")
        stats = self.collector.get_statistics()
        assert stats.errors_by_type["ParsingError"] == 2
        assert stats.errors_by_type["ValidationError"] == 1

    def test_reset(self) -> None:
        self.collector.record_import("file", "pdf", True)
        self.collector.reset()
        stats = self.collector.get_statistics()
        assert stats.total_imports == 0
