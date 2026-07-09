from __future__ import annotations

from datetime import datetime

import pytest

from application.embedding.batching import BatchProgress, EmbeddingBatchProcessor
from application.embedding.chunking import (
    ChunkerFactory,
    ChunkingResult,
    FixedSizeChunker,
    HeadingAwareChunker,
    ParagraphChunker,
    SentenceChunker,
    SlidingWindowChunker,
)
from application.embedding.exceptions import (
    EmbeddingChunkingError,
    EmbeddingConfigurationError,
    EmbeddingConnectionError,
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingSerializationError,
    EmbeddingTimeoutError,
    EmbeddingValidationError,
)
from application.embedding.health import EmbeddingHealth, EmbeddingHealthChecker, EmbeddingHealthStatus
from application.embedding.metrics import EmbeddingMetricsCollector
from application.embedding.models import (
    EmbeddingBatchResult,
    EmbeddingConfiguration,
    EmbeddingMetadata,
    EmbeddingProviderType,
    EmbeddingRequest,
    EmbeddingResponse,
)
from application.embedding.pipeline import EmbeddingPipeline
from application.embedding.provider import BaseEmbeddingProvider
from application.embedding.scheduler import EmbeddingScheduler, EmbeddingScheduleStatus
from application.embedding.statistics import EmbeddingStatisticsCollector
from application.embedding.validator import EmbeddingValidator
from domain.knowledge.value_objects import ChunkingStrategy, DocumentId


class _TestProvider(BaseEmbeddingProvider):
    @property
    def provider_type(self) -> EmbeddingProviderType:
        return EmbeddingProviderType.CUSTOM

    def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return EmbeddingResponse(
            chunk_id=request.chunk_id,
            embedding=[0.1] * 768,
            dimension=768,
            model=request.model,
            tokens_used=10,
            latency_ms=5.0,
        )

    def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
        return [self.generate(r) for r in requests]


class TestEmbeddingModels:
    def test_embedding_request_defaults(self) -> None:
        req = EmbeddingRequest()
        assert req.chunk_id == ""
        assert req.text == ""
        assert req.model == ""
        assert req.provider == EmbeddingProviderType.CUSTOM
        assert req.parameters == {}

    def test_embedding_response_defaults(self) -> None:
        resp = EmbeddingResponse()
        assert resp.chunk_id == ""
        assert resp.embedding == []
        assert resp.dimension == 0
        assert resp.model == ""
        assert resp.tokens_used == 0
        assert resp.latency_ms == 0.0
        assert resp.metadata == {}

    def test_embedding_batch_result_defaults(self) -> None:
        result = EmbeddingBatchResult()
        assert result.document_id == ""
        assert result.chunks == []
        assert result.embeddings == []
        assert result.success is False
        assert result.error is None
        assert result.latency_ms == 0.0
        assert result.metadata == {}

    def test_embedding_configuration_defaults(self) -> None:
        config = EmbeddingConfiguration()
        assert config.provider == EmbeddingProviderType.CUSTOM
        assert config.model == ""
        assert config.api_key == ""
        assert config.dimensions == 768
        assert config.max_retries == 3
        assert config.timeout == 30.0
        assert config.batch_size == 32
        assert config.max_tokens_per_chunk == 8191
        assert config.overlap_tokens == 200
        assert config.chunking_strategy == ChunkingStrategy.FIXED_SIZE
        assert config.enable_deduplication is True

    def test_embedding_provider_type_values(self) -> None:
        assert EmbeddingProviderType.OPENAI.value == "openai"
        assert EmbeddingProviderType.GEMINI.value == "gemini"
        assert EmbeddingProviderType.NVIDIA.value == "nvidia"
        assert EmbeddingProviderType.VOYAGE.value == "voyage"
        assert EmbeddingProviderType.COHERE.value == "cohere"
        assert EmbeddingProviderType.SENTENCE_TRANSFORMERS.value == "sentence_transformers"
        assert EmbeddingProviderType.CUSTOM.value == "custom"

    def test_embedding_metadata_defaults(self) -> None:
        meta = EmbeddingMetadata()
        assert meta.model == ""
        assert meta.provider == EmbeddingProviderType.CUSTOM
        assert meta.dimension == 0
        assert meta.tokens_used == 0
        assert meta.latency_ms == 0.0
        assert isinstance(meta.timestamp, datetime)
        assert meta.extra == {}


class TestEmbeddingExceptions:
    def test_error_hierarchy(self) -> None:
        assert issubclass(EmbeddingConnectionError, EmbeddingError)
        assert issubclass(EmbeddingTimeoutError, EmbeddingError)
        assert issubclass(EmbeddingValidationError, EmbeddingError)
        assert issubclass(EmbeddingProviderError, EmbeddingError)
        assert issubclass(EmbeddingConfigurationError, EmbeddingError)
        assert issubclass(EmbeddingSerializationError, EmbeddingError)
        assert issubclass(EmbeddingChunkingError, EmbeddingError)

    def test_error_with_detail(self) -> None:
        err = EmbeddingError("Failed", detail="Connection refused")
        assert err.detail == "Connection refused"

    def test_connection_error(self) -> None:
        err = EmbeddingConnectionError("Could not connect")
        assert err.message == "Could not connect"

    def test_timeout_error(self) -> None:
        err = EmbeddingTimeoutError("Request timed out")
        assert err.message == "Request timed out"

    def test_validation_error(self) -> None:
        err = EmbeddingValidationError("Invalid input")
        assert err.message == "Invalid input"


class TestEmbeddingValidator:
    def setup_method(self) -> None:
        self.validator = EmbeddingValidator()

    def test_validate_request_valid(self) -> None:
        req = EmbeddingRequest(chunk_id="c1", text="hello world", model="m1")
        self.validator.validate_request(req)

    def test_validate_request_missing_text(self) -> None:
        req = EmbeddingRequest(chunk_id="c1", model="m1")
        with pytest.raises(EmbeddingValidationError, match="text is required"):
            self.validator.validate_request(req)

    def test_validate_response_valid(self) -> None:
        resp = EmbeddingResponse(chunk_id="c1", embedding=[0.1, 0.2])
        assert self.validator.validate_response(resp) is True

    def test_validate_chunk_valid(self) -> None:
        self.validator.validate_chunk("some text")

    def test_validate_chunk_empty(self) -> None:
        with pytest.raises(EmbeddingValidationError, match="Chunk text cannot be empty"):
            self.validator.validate_chunk("")

    def test_validate_chunks_deduplication(self) -> None:
        result = self.validator.validate_chunks(["a", "b", "a", "c"])
        assert result == ["a", "b", "c"]

    def test_validate_chunks_filters_empty(self) -> None:
        result = self.validator.validate_chunks(["a", "", "b", "  "])
        assert result == ["a", "b"]

    def test_validate_configuration_valid(self) -> None:
        config = EmbeddingConfiguration(
            model="test-model",
            dimensions=768,
            max_retries=3,
            timeout=30.0,
            batch_size=32,
            max_tokens_per_chunk=8191,
            overlap_tokens=200,
        )
        self.validator.validate_configuration(config)

    def test_validate_embedding_dimension_match(self) -> None:
        assert self.validator.validate_embedding_dimension(768, 768) is True

    def test_validate_embedding_dimension_mismatch(self) -> None:
        assert self.validator.validate_embedding_dimension(512, 768) is False


class TestChunkingStrategies:
    def test_fixed_size_chunker(self) -> None:
        chunker = FixedSizeChunker(max_size=3, overlap=0)
        result = chunker.chunk("a b c d e f g h")
        assert len(result.chunks) == 3
        assert result.chunks[0] == "a b c"
        assert result.chunks[1] == "d e f"
        assert result.chunks[2] == "g h"
        assert result.chunk_count == 3
        assert result.strategy == ChunkingStrategy.FIXED_SIZE

    def test_fixed_size_chunker_respects_max_size(self) -> None:
        chunker = FixedSizeChunker(max_size=2, overlap=0)
        result = chunker.chunk("hello world foo bar")
        assert all(len(c.split()) <= 2 for c in result.chunks)

    def test_sliding_window_chunker(self) -> None:
        chunker = SlidingWindowChunker(max_size=4, overlap=2)
        result = chunker.chunk("a b c d e f g")
        assert len(result.chunks) == 3
        assert result.overlap == 2
        assert result.strategy == ChunkingStrategy.SLIDING_WINDOW

    def test_paragraph_chunker(self) -> None:
        chunker = ParagraphChunker(max_size=2000)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = chunker.chunk(text)
        assert result.chunk_count >= 1
        assert result.strategy == ChunkingStrategy.PARAGRAPH

    def test_heading_aware_chunker(self) -> None:
        chunker = HeadingAwareChunker(max_size=2000)
        text = "# Intro\nHello\n## Details\nMore info"
        result = chunker.chunk(text)
        assert result.chunk_count >= 1
        assert result.strategy == ChunkingStrategy.HEADING_AWARE

    def test_sentence_chunker(self) -> None:
        chunker = SentenceChunker(max_size=2000)
        text = "First sentence. Second sentence. Third sentence."
        result = chunker.chunk(text)
        assert result.chunk_count >= 1
        assert result.strategy == ChunkingStrategy.SENTENCE

    def test_chunker_factory_creates_correct_chunker(self) -> None:
        assert isinstance(ChunkerFactory.create(ChunkingStrategy.FIXED_SIZE), FixedSizeChunker)
        assert isinstance(ChunkerFactory.create(ChunkingStrategy.SLIDING_WINDOW), SlidingWindowChunker)
        assert isinstance(ChunkerFactory.create(ChunkingStrategy.PARAGRAPH), ParagraphChunker)
        assert isinstance(ChunkerFactory.create(ChunkingStrategy.HEADING_AWARE), HeadingAwareChunker)
        assert isinstance(ChunkerFactory.create(ChunkingStrategy.SENTENCE), SentenceChunker)

    def test_chunking_result_defaults(self) -> None:
        result = ChunkingResult()
        assert result.chunks == []
        assert result.chunk_count == 0
        assert result.strategy == ChunkingStrategy.FIXED_SIZE
        assert result.overlap == 0


class TestEmbeddingBatchProcessor:
    def setup_method(self) -> None:
        self.processor = EmbeddingBatchProcessor()

    def test_split_into_batches(self) -> None:
        requests = [EmbeddingRequest(text="a"), EmbeddingRequest(text="b"), EmbeddingRequest(text="c")]
        batches = self.processor.split_into_batches(requests, 2)
        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_split_into_batches_empty(self) -> None:
        batches = self.processor.split_into_batches([], 2)
        assert batches == []

    def test_split_into_batches_invalid_size(self) -> None:
        with pytest.raises(ValueError, match="batch_size must be positive"):
            self.processor.split_into_batches([EmbeddingRequest()], 0)

    def test_batch_progress_defaults(self) -> None:
        progress = BatchProgress()
        assert progress.completed == 0
        assert progress.failed == 0
        assert progress.total == 0

    def test_batch_progress_remaining(self) -> None:
        progress = BatchProgress(completed=5, failed=2, total=10)
        assert progress.remaining == 3


class TestEmbeddingScheduler:
    def setup_method(self) -> None:
        self.scheduler = EmbeddingScheduler()

    def test_schedule_document(self) -> None:
        doc_id = DocumentId()
        item = self.scheduler.schedule(doc_id, priority=5)
        assert item.document_id == doc_id
        assert item.status == EmbeddingScheduleStatus.PENDING
        assert item.priority == 5

    def test_get_status(self) -> None:
        doc_id = DocumentId()
        item = self.scheduler.schedule(doc_id)
        assert self.scheduler.get_status(item.item_id) == EmbeddingScheduleStatus.PENDING
        assert self.scheduler.get_status("nonexistent") is None

    def test_cancel(self) -> None:
        doc_id = DocumentId()
        item = self.scheduler.schedule(doc_id)
        assert self.scheduler.cancel(item.item_id) is True
        assert self.scheduler.get_status(item.item_id) == EmbeddingScheduleStatus.CANCELLED
        assert self.scheduler.cancel("nonexistent") is False

    def test_queue_depth(self) -> None:
        assert self.scheduler.get_queue_depth() == 0
        self.scheduler.schedule(DocumentId())
        self.scheduler.schedule(DocumentId())
        assert self.scheduler.get_queue_depth() == 2


class TestEmbeddingMetrics:
    def setup_method(self) -> None:
        self.collector = EmbeddingMetricsCollector()

    def test_initial_metrics(self) -> None:
        assert self.collector.metrics.total_requests == 0

    def test_record_request_success(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True)
        assert self.collector.metrics.total_requests == 1
        assert self.collector.metrics.successful == 1

    def test_record_request_failure(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=False)
        assert self.collector.metrics.failed == 1

    def test_record_request_retry(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True, retry=True)
        assert self.collector.metrics.retry_count == 1

    def test_record_chunk_processed(self) -> None:
        self.collector.record_chunk_processed()
        assert self.collector.metrics.total_chunks_processed == 1

    def test_record_document_processed(self) -> None:
        self.collector.record_document_processed()
        assert self.collector.metrics.total_documents_processed == 1

    def test_avg_latency(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True)
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 200.0, success=True)
        assert self.collector.metrics.avg_latency_ms == 150.0

    def test_requests_by_provider(self) -> None:
        self.collector.record_request(EmbeddingProviderType.OPENAI, "gpt-4", 100.0, success=True)
        self.collector.record_request(EmbeddingProviderType.GEMINI, "gemini-pro", 50.0, success=True)
        assert self.collector.metrics.requests_by_provider.get("openai") == 1
        assert self.collector.metrics.requests_by_provider.get("gemini") == 1

    def test_requests_by_model(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "text-embedding-ada-002", 100.0, success=True)
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "text-embedding-3-small", 50.0, success=True)
        assert self.collector.metrics.requests_by_model.get("text-embedding-ada-002") == 1
        assert self.collector.metrics.requests_by_model.get("text-embedding-3-small") == 1

    def test_reset(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True)
        self.collector.reset()
        assert self.collector.metrics.total_requests == 0


class TestEmbeddingHealth:
    def test_healthy_no_metrics(self) -> None:
        checker = EmbeddingHealthChecker()
        health = checker.check()
        assert health.status == EmbeddingHealthStatus.HEALTHY
        assert health.total_requests == 0

    def test_healthy_good_metrics(self) -> None:
        checker = EmbeddingHealthChecker()
        metrics = EmbeddingMetricsCollector()
        metrics.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True)
        health = checker.check(metrics.metrics)
        assert health.status == EmbeddingHealthStatus.HEALTHY

    def test_degraded_low_success(self) -> None:
        checker = EmbeddingHealthChecker(min_success_rate=0.9)
        metrics = EmbeddingMetricsCollector()
        metrics.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=True)
        metrics.record_request(EmbeddingProviderType.CUSTOM, "model1", 100.0, success=False)
        health = checker.check(metrics.metrics)
        assert health.status == EmbeddingHealthStatus.DEGRADED

    def test_consecutive_failures_unhealthy(self) -> None:
        checker = EmbeddingHealthChecker(max_consecutive_failures=2)
        checker.record_failure("err1")
        checker.record_failure("err2")
        checker.record_failure("err3")
        health = checker.check()
        assert health.status == EmbeddingHealthStatus.UNHEALTHY


class TestEmbeddingStatistics:
    def setup_method(self) -> None:
        self.collector = EmbeddingStatisticsCollector()

    def test_initial_statistics(self) -> None:
        stats = self.collector.statistics
        assert stats.total_requests == 0
        assert stats.success_rate == 1.0

    def test_record_request_success(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=True)
        assert self.collector.statistics.total_requests == 1
        assert self.collector.statistics.successful_requests == 1

    def test_record_request_failure(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=False)
        assert self.collector.statistics.failed_requests == 1

    def test_record_chunk(self) -> None:
        self.collector.record_chunk("pdf")
        assert self.collector.statistics.total_chunks == 1

    def test_record_tokens(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=True)
        self.collector.record_tokens(100)
        assert self.collector.statistics.total_tokens == 100
        assert self.collector.statistics.avg_tokens_per_request == 100.0

    def test_requests_by_provider(self) -> None:
        self.collector.record_request(EmbeddingProviderType.OPENAI, "gpt-4", success=True)
        self.collector.record_request(EmbeddingProviderType.GEMINI, "gemini-pro", success=True)
        assert self.collector.statistics.requests_by_provider.get("openai") == 1
        assert self.collector.statistics.requests_by_provider.get("gemini") == 1

    def test_success_rate(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=True)
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=False)
        assert self.collector.statistics.success_rate == 0.5

    def test_reset(self) -> None:
        self.collector.record_request(EmbeddingProviderType.CUSTOM, "model1", success=True)
        self.collector.reset()
        assert self.collector.statistics.total_requests == 0


class TestEmbeddingProvider:
    def test_base_provider_instantiation(self) -> None:
        class _ConcreteProvider(BaseEmbeddingProvider):
            @property
            def provider_type(self) -> EmbeddingProviderType:
                return EmbeddingProviderType.CUSTOM

            def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
                return EmbeddingResponse()

            def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
                return [self.generate(r) for r in requests]

        config = EmbeddingConfiguration(model="test")
        provider = _ConcreteProvider(config)
        assert provider.provider_type == EmbeddingProviderType.CUSTOM
        assert provider.configuration.model == "test"

    def test_base_provider_validate_configuration(self) -> None:
        class _ConcreteProvider(BaseEmbeddingProvider):
            @property
            def provider_type(self) -> EmbeddingProviderType:
                return EmbeddingProviderType.CUSTOM

            def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
                return EmbeddingResponse()

            def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
                return [self.generate(r) for r in requests]

        config = EmbeddingConfiguration(
            model="test-model",
            dimensions=768,
            max_retries=3,
            timeout=30.0,
            batch_size=32,
            max_tokens_per_chunk=8191,
            overlap_tokens=200,
        )
        provider = _ConcreteProvider(config)
        assert provider.validate_configuration(config) is True


class TestEmbeddingPipeline:
    def setup_method(self) -> None:
        config = EmbeddingConfiguration(
            model="test-model",
            dimensions=768,
            max_retries=3,
            timeout=30.0,
            batch_size=32,
            max_tokens_per_chunk=8191,
            overlap_tokens=200,
        )
        self._config = config
        self._provider = _TestProvider(config)
        self.pipeline = EmbeddingPipeline(provider=self._provider, config=self._config)

    def test_pipeline_initialization(self) -> None:
        assert self.pipeline is not None
        assert self.pipeline.configuration.model == "test-model"

    def test_pipeline_configuration(self) -> None:
        assert self.pipeline.configuration is self._config
        assert self.pipeline.configuration.dimensions == 768

    def test_pipeline_provider(self) -> None:
        assert self.pipeline.provider is self._provider
        assert self.pipeline.provider.provider_type == EmbeddingProviderType.CUSTOM

    def test_pipeline_health(self) -> None:
        health = self.pipeline.health()
        assert isinstance(health, EmbeddingHealth)
        assert health.status == EmbeddingHealthStatus.HEALTHY

    def test_pipeline_reset_metrics(self) -> None:
        self.pipeline.reset_metrics()
        assert self.pipeline.metrics.total_requests == 0
