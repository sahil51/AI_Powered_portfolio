from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.knowledge_context.builder import KnowledgeContextBuilder
from application.knowledge_context.cache import KnowledgeContextCache
from application.knowledge_context.exceptions import ContextRetrievalError, ContextValidationError
from application.knowledge_context.health import KnowledgeContextHealthChecker, KnowledgeContextHealthStatus
from application.knowledge_context.metrics import KnowledgeContextMetricsCollector
from application.knowledge_context.models import (
    AssembledContext,
    ChunkSelectionStrategy,
    CompressionStrategy,
    ContextSourcePriority,
    ContextStatisticsData,
    KnowledgeContextChunk,
    KnowledgeContextConfig,
    KnowledgeContextResult,
    TokenBudget,
)
from application.knowledge_context.policy import KnowledgeContextPolicy
from application.knowledge_context.statistics import KnowledgeContextStatisticsCollector
from application.knowledge_context.validator import KnowledgeContextValidator
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.value_objects import ChunkId


@pytest.fixture
def sample_knowledge_chunk():
    return KnowledgeChunk(
        chunk_id=ChunkId(),
        document_id="doc-1",
        text="test content",
        token_count=10,
        checksum="chk1",
    )


@pytest.fixture
def sample_context_chunk(sample_knowledge_chunk):
    return KnowledgeContextChunk(
        chunk=sample_knowledge_chunk,
        document_title="Test Doc",
        document_type="pdf",
        score=0.95,
        rank=1,
        source_priority=ContextSourcePriority.KNOWLEDGE,
    )


class TestKnowledgeContextConfig:
    def test_defaults(self):
        config = KnowledgeContextConfig()
        assert config.max_knowledge_tokens == 2048
        assert config.max_retrieved_chunks == 20
        assert config.min_relevance_score == 0.3
        assert config.enable_compression is True
        assert config.enable_deduplication is True
        assert config.enable_section_grouping is True
        assert config.enable_semantic_ordering is False
        assert config.enable_metadata_preservation is True
        assert config.enable_source_attribution is True
        assert config.compression_strategy == CompressionStrategy.TRUNCATE
        assert config.chunk_selection == ChunkSelectionStrategy.RELEVANCE
        assert config.prefer_latest_version is True
        assert config.excluded_doc_types == []
        assert config.included_doc_types == []
        assert config.language_filter == ""
        assert config.tenant_filter == ""


class TestTokenBudget:
    def test_defaults(self):
        b = TokenBudget()
        assert b.total_tokens == 8192
        assert b.conversation_tokens == 2048
        assert b.memory_tokens == 1024
        assert b.knowledge_tokens == 2048
        assert b.reserved_tokens == 1024
        assert b.used_tokens == 0
        assert b.remaining_tokens == 0

    def test_calculate_remaining(self):
        b = TokenBudget(total_tokens=1000, used_tokens=200, reserved_tokens=100)
        assert b.calculate_remaining() == 700

    def test_can_accommodate_true(self):
        b = TokenBudget(total_tokens=1000, used_tokens=200, reserved_tokens=100)
        assert b.can_accommodate(500) is True

    def test_can_accommodate_false(self):
        b = TokenBudget(total_tokens=1000, used_tokens=200, reserved_tokens=100)
        assert b.can_accommodate(800) is False

    def test_can_accommodate_at_boundary(self):
        b = TokenBudget(total_tokens=1000, used_tokens=200, reserved_tokens=100)
        assert b.can_accommodate(700) is True


class TestKnowledgeContextResult:
    def test_defaults(self):
        r = KnowledgeContextResult()
        assert r.chunks == []
        assert r.total_chunks == 0
        assert r.total_tokens == 0
        assert r.truncated is False
        assert r.compressed is False
        assert r.deduplicated_count == 0
        assert r.retrieval_latency_ms == 0.0
        assert r.compression_latency_ms == 0.0
        assert r.cache_hit is False
        assert r.query == ""
        assert r.correlation_id == ""


class TestAssembledContext:
    def test_defaults(self):
        ctx = AssembledContext()
        assert ctx.text == ""
        assert ctx.chunks == []
        assert ctx.tokens_used == 0
        assert ctx.total_available == 0
        assert ctx.truncated is False
        assert ctx.metadata == {}


class TestKnowledgeContextValidator:
    def setup_method(self) -> None:
        self.validator = KnowledgeContextValidator()

    def test_validate_query_valid(self):
        self.validator.validate_query("valid query")

    def test_validate_query_empty_raises(self):
        with pytest.raises(ContextValidationError, match="cannot be empty"):
            self.validator.validate_query("")

    def test_validate_query_whitespace_only_raises(self):
        with pytest.raises(ContextValidationError, match="cannot be empty"):
            self.validator.validate_query("   ")

    def test_validate_query_too_long_raises(self):
        with pytest.raises(ContextValidationError, match="exceeds maximum length"):
            self.validator.validate_query("x" * 10001)

    def test_validate_config_valid(self):
        config = KnowledgeContextConfig(max_knowledge_tokens=2048, max_retrieved_chunks=20, min_relevance_score=0.3)
        self.validator.validate_config(config)

    def test_validate_config_zero_tokens_raises(self):
        config = KnowledgeContextConfig(max_knowledge_tokens=0)
        with pytest.raises(ContextValidationError, match="max_knowledge_tokens must be positive"):
            self.validator.validate_config(config)

    def test_validate_config_zero_chunks_raises(self):
        config = KnowledgeContextConfig(max_retrieved_chunks=0)
        with pytest.raises(ContextValidationError, match="max_retrieved_chunks must be positive"):
            self.validator.validate_config(config)

    def test_validate_config_min_score_out_of_range_raises(self):
        config = KnowledgeContextConfig(min_relevance_score=1.5)
        with pytest.raises(ContextValidationError, match="min_relevance_score must be between 0 and 1"):
            self.validator.validate_config(config)

    def test_validate_budget_valid(self):
        budget = TokenBudget(total_tokens=1024, knowledge_tokens=512, reserved_tokens=128)
        self.validator.validate_budget(budget)

    def test_validate_budget_too_small_raises(self):
        budget = TokenBudget(total_tokens=64, knowledge_tokens=32, reserved_tokens=0)
        with pytest.raises(ContextValidationError, match="at least"):
            self.validator.validate_budget(budget)

    def test_validate_budget_negative_reserved_raises(self):
        budget = TokenBudget(total_tokens=8192, knowledge_tokens=2048, reserved_tokens=-1)
        with pytest.raises(ContextValidationError, match="Reserved tokens cannot be negative"):
            self.validator.validate_budget(budget)

    def test_validate_budget_zero_knowledge_raises(self):
        budget = TokenBudget(total_tokens=8192, knowledge_tokens=0, reserved_tokens=1024)
        with pytest.raises(ContextValidationError, match="Knowledge token budget must be positive"):
            self.validator.validate_budget(budget)

    def test_validate_result_valid(self):
        result = KnowledgeContextResult(total_chunks=10)
        self.validator.validate_result(result)

    def test_validate_result_exceeds_max_chunks_raises(self):
        result = KnowledgeContextResult(total_chunks=200)
        with pytest.raises(ContextValidationError, match="max is"):
            self.validator.validate_result(result)

    def test_validate_context_output_valid(self):
        self.validator.validate_context_output("short text", 100)

    def test_validate_context_output_too_large_raises(self):
        text = "word " * 500
        with pytest.raises(ContextValidationError, match="too large"):
            self.validator.validate_context_output(text, 100)


class TestKnowledgeRetrievalProvider:
    def setup_method(self) -> None:
        self.search_service = AsyncMock()
        self.provider = type("Provider", (), {})()
        self.provider._search_service = self.search_service
        self.provider._build_filter = lambda config: MagicMock()
        self.provider._diversity_ranking = lambda chunks: chunks
        self.provider._text_similarity = lambda t1, t2: 0.0

    @pytest.mark.asyncio
    async def test_retrieve_returns_result(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        mock_response = MagicMock()
        mock_response.results = []
        self.search_service.search = AsyncMock(return_value=mock_response)

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig()
        result = await provider.retrieve("test query", config, "corr-1")
        assert isinstance(result, KnowledgeContextResult)
        assert result.query == "test query"
        assert result.correlation_id == "corr-1"

    @pytest.mark.asyncio
    async def test_retrieve_with_results(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        chunk = KnowledgeChunk(text="content", checksum="c1")
        doc = MagicMock()
        doc.title = "Doc Title"
        doc.doc_type = type("DT", (), {"value": "pdf"})()

        result_item = MagicMock()
        result_item.chunk = chunk
        result_item.document = doc
        result_item.score = 0.9
        result_item.rank = 1

        mock_response = MagicMock()
        mock_response.results = [result_item]
        self.search_service.search = AsyncMock(return_value=mock_response)

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig(min_relevance_score=0.0)
        result = await provider.retrieve("test", config, "corr-1")
        assert result.total_chunks > 0
        assert result.chunks[0].document_title == "Doc Title"

    @pytest.mark.asyncio
    async def test_retrieve_error_raises_context_retrieval_error(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        self.search_service.search = AsyncMock(side_effect=Exception("search failed"))
        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig()
        with pytest.raises(ContextRetrievalError, match="Knowledge retrieval failed"):
            await provider.retrieve("test", config, "corr-1")

    @pytest.mark.asyncio
    async def test_retrieve_by_ids(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        chunk = KnowledgeChunk(text="found", checksum="c1")
        mock_response = MagicMock()
        mock_response.results = [type("R", (), {"chunk": chunk})()]
        self.search_service.search = AsyncMock(return_value=mock_response)

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        results = await provider.retrieve_by_ids(["id1", "id2"], "corr-1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_by_ids_continues_on_error(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        self.search_service.search = AsyncMock(side_effect=[Exception("fail"), type("R", (), {"results": [type("R2", (), {"chunk": KnowledgeChunk(text="ok")})]})()])
        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        results = await provider.retrieve_by_ids(["bad", "good"], "corr-1")
        assert len(results) == 1

    def test_build_filter_with_excluded_types(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig(excluded_doc_types=["pdf"])
        search_filter = provider._build_filter(config)
        assert search_filter is not None

    def test_build_filter_with_language(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig(language_filter="en")
        search_filter = provider._build_filter(config)
        assert search_filter.language == "en"

    def test_build_filter_with_tenant(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        config = KnowledgeContextConfig(tenant_filter="tenant-1")
        search_filter = provider._build_filter(config)
        assert search_filter.custom["tenant_id"] == "tenant-1"

    def test_diversity_ranking_empty(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        result = provider._diversity_ranking([])
        assert result == []

    def test_diversity_ranking_single(self, sample_context_chunk):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        result = provider._diversity_ranking([sample_context_chunk])
        assert len(result) == 1

    def test_text_similarity(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        sim = provider._text_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_text_similarity_no_overlap(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        sim = provider._text_similarity("abc def", "ghi jkl")
        assert sim == 0.0

    def test_text_similarity_empty(self):
        from application.knowledge_context.provider import KnowledgeRetrievalProvider

        provider = KnowledgeRetrievalProvider(search_service=self.search_service)
        sim = provider._text_similarity("", "")
        assert sim == 0.0


class TestKnowledgeContextAssemblerImpl:
    def setup_method(self) -> None:
        from application.knowledge_context.assembler import KnowledgeContextAssemblerImpl

        self.assembler = KnowledgeContextAssemblerImpl()

    def test_select_chunks_relevance(self, sample_context_chunk):
        chunks = [
            KnowledgeContextChunk(chunk=KnowledgeChunk(text="b"), score=0.5),
            KnowledgeContextChunk(chunk=KnowledgeChunk(text="a"), score=0.9),
        ]
        selected = self.assembler.select_chunks(chunks, ChunkSelectionStrategy.RELEVANCE, 5)
        assert selected[0].score == 0.9

    def test_select_chunks_recency(self):
        from datetime import datetime, timezone

        old = KnowledgeContextChunk(chunk=KnowledgeChunk(text="old", created_at=datetime(2020, 1, 1, tzinfo=timezone.utc)), score=0.5)
        new = KnowledgeContextChunk(chunk=KnowledgeChunk(text="new", created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)), score=0.5)
        chunks = [old, new]
        selected = self.assembler.select_chunks(chunks, ChunkSelectionStrategy.RECENCY, 5)
        assert selected[0] == new

    def test_select_chunks_hybrid_defaults_to_relevance(self, sample_context_chunk):
        chunks = [
            KnowledgeContextChunk(chunk=KnowledgeChunk(text="b"), score=0.5),
            KnowledgeContextChunk(chunk=KnowledgeChunk(text="a"), score=0.9),
        ]
        selected = self.assembler.select_chunks(chunks, ChunkSelectionStrategy.HYBRID, 5)
        assert len(selected) == 2

    def test_select_chunks_respects_max(self, sample_context_chunk):
        chunks = [sample_context_chunk, sample_context_chunk]
        selected = self.assembler.select_chunks(chunks, ChunkSelectionStrategy.RELEVANCE, 1)
        assert len(selected) == 1

    def test_deduplicate_removes_duplicates(self):
        c1 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="a", checksum="x"))
        c2 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="b", checksum="x"))
        result = self.assembler._deduplicate([c1, c2])
        assert len(result) == 1

    def test_deduplicate_preserves_unique(self):
        c1 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="a", checksum="x"))
        c2 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="b", checksum="y"))
        result = self.assembler._deduplicate([c1, c2])
        assert len(result) == 2

    def test_group_by_section(self):
        c1 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="a", section="intro"))
        c2 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="b", section="details"))
        c3 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="c", section="intro"))
        result = self.assembler._group_by_section([c1, c2, c3])
        assert result[0] == c1
        assert result[1] == c3
        assert result[2] == c2

    def test_group_by_section_falls_back_to_heading(self):
        c1 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="a", heading="h1"))
        result = self.assembler._group_by_section([c1])
        assert len(result) == 1

    def test_group_by_section_default_section(self):
        c1 = KnowledgeContextChunk(chunk=KnowledgeChunk(text="a"))
        result = self.assembler._group_by_section([c1])
        assert len(result) == 1

    def test_jaccard_similarity_identical(self):
        sim = self.assembler._jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_jaccard_similarity_different(self):
        sim = self.assembler._jaccard_similarity("abc def", "ghi jkl")
        assert sim == 0.0

    def test_jaccard_similarity_empty(self):
        sim = self.assembler._jaccard_similarity("", "")
        assert sim == 0.0

    def test_diversity_select_empty(self):
        result = self.assembler._diversity_select([])
        assert result == []

    def test_diversity_select_single(self, sample_context_chunk):
        result = self.assembler._diversity_select([sample_context_chunk])
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_assemble_with_dedup_and_section_grouping(self, sample_context_chunk):
        result = KnowledgeContextResult(
            chunks=[sample_context_chunk],
            total_chunks=1,
            total_tokens=10,
        )
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(
            enable_deduplication=True,
            enable_section_grouping=True,
            enable_semantic_ordering=False,
            enable_compression=False,
        )
        assembled = await self.assembler.assemble(result, budget, config)
        assert isinstance(assembled, AssembledContext)
        assert assembled.tokens_used > 0

    @pytest.mark.asyncio
    async def test_assemble_triggers_compression_when_over_budget(self):
        long_text = "word " * 500
        chunk = KnowledgeContextChunk(chunk=KnowledgeChunk(text=long_text, checksum="c1"))
        result = KnowledgeContextResult(chunks=[chunk], total_chunks=1)
        budget = TokenBudget(knowledge_tokens=10)
        config = KnowledgeContextConfig(
            enable_compression=True,
            compression_strategy=CompressionStrategy.TRUNCATE,
            enable_deduplication=False,
            enable_section_grouping=False,
        )
        assembled = await self.assembler.assemble(result, budget, config)
        assert assembled.truncated or assembled.tokens_used <= 10

    @pytest.mark.asyncio
    async def test_assemble_source_attribution(self):
        chunk = KnowledgeContextChunk(
            chunk=KnowledgeChunk(text="content"),
            document_title="My Doc",
        )
        result = KnowledgeContextResult(chunks=[chunk], total_chunks=1)
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(
            enable_source_attribution=True,
            enable_deduplication=False,
            enable_section_grouping=False,
            enable_metadata_preservation=False,
            enable_compression=False,
        )
        assembled = await self.assembler.assemble(result, budget, config)
        assert "[Source: My Doc]" in assembled.text

    @pytest.mark.asyncio
    async def test_assemble_metadata_preservation(self):
        chunk = KnowledgeContextChunk(
            chunk=KnowledgeChunk(text="content", heading="My Heading"),
        )
        result = KnowledgeContextResult(chunks=[chunk], total_chunks=1)
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(
            enable_metadata_preservation=True,
            enable_source_attribution=False,
            enable_deduplication=False,
            enable_section_grouping=False,
            enable_compression=False,
        )
        assembled = await self.assembler.assemble(result, budget, config)
        assert "My Heading" in assembled.text

    @pytest.mark.asyncio
    async def test_assemble_empty_result(self):
        result = KnowledgeContextResult()
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(enable_deduplication=False, enable_section_grouping=False)
        assembled = await self.assembler.assemble(result, budget, config)
        assert assembled.text == ""

    @pytest.mark.asyncio
    async def test_assemble_error_raises_assembly_error(self):
        from application.knowledge_context.exceptions import ContextAssemblyError

        bad_compressor = MagicMock()
        bad_compressor.estimate_tokens = MagicMock(side_effect=Exception("compressor failed"))
        from application.knowledge_context.assembler import KnowledgeContextAssemblerImpl
        assembler = KnowledgeContextAssemblerImpl(compressor=bad_compressor)
        chunk = KnowledgeContextChunk(chunk=KnowledgeChunk(text="test"))
        result = KnowledgeContextResult(chunks=[chunk], total_chunks=1)
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(enable_compression=False, enable_deduplication=False, enable_section_grouping=False)
        with pytest.raises(ContextAssemblyError, match="Context assembly failed"):
            await assembler.assemble(result, budget, config)

    @pytest.mark.asyncio
    async def test_assemble_skips_empty_chunks(self):
        result = KnowledgeContextResult(chunks=[], total_chunks=0)
        budget = TokenBudget(knowledge_tokens=2048)
        config = KnowledgeContextConfig(enable_deduplication=False, enable_section_grouping=False)
        assembled = await self.assembler.assemble(result, budget, config)
        assert assembled.text == ""


class TestKnowledgeContextBuilder:
    def setup_method(self) -> None:
        self.provider = AsyncMock()
        self.assembler = AsyncMock()
        self.cache = AsyncMock()
        self.validator = MagicMock()
        self.metrics = MagicMock()
        self.statistics = MagicMock()
        self.health = MagicMock()

        self.builder = KnowledgeContextBuilder(
            provider=self.provider,
            assembler=self.assembler,
            cache=self.cache,
            validator=self.validator,
            metrics_collector=self.metrics,
            statistics_collector=self.statistics,
            health_checker=self.health,
        )

    def test_name(self):
        assert self.builder.name == "knowledge"

    def test_priority(self):
        assert self.builder.priority == 5

    def test_is_enabled(self):
        assert self.builder.is_enabled() is True

    def test_get_config(self):
        config = self.builder.get_config()
        assert isinstance(config, KnowledgeContextConfig)

    def test_update_policy(self):
        policy = KnowledgeContextPolicy(max_knowledge_tokens=4096)
        self.builder.update_policy(policy)
        assert self.builder.get_config().max_knowledge_tokens == 4096

    @pytest.mark.asyncio
    async def test_build_successful(self):
        self.validator.validate_query = MagicMock()
        self.validator.validate_config = MagicMock()
        self.health.record_success = MagicMock()

        result = KnowledgeContextResult(
            chunks=[KnowledgeContextChunk(chunk=KnowledgeChunk(text="test"))],
            total_chunks=1,
            total_tokens=10,
            retrieval_latency_ms=5.0,
            cache_hit=False,
        )
        self.provider.retrieve = AsyncMock(return_value=result)

        assembled = AssembledContext(
            text="test context",
            chunks=result.chunks,
            tokens_used=10,
            total_available=2048,
            truncated=False,
            metadata={"compression_ratio": 1.0, "total_available": 2048},
        )
        self.assembler.assemble = AsyncMock(return_value=assembled)

        output = await self.builder.build(query="test", correlation_id="corr-1")
        assert output["context"] == "test context"
        assert output["tokens_used"] == 10
        assert output["truncated"] is False

    @pytest.mark.asyncio
    async def test_build_with_cached_result(self):
        self.validator.validate_query = MagicMock()
        self.validator.validate_config = MagicMock()
        self.health.record_success = MagicMock()

        cached_result = KnowledgeContextResult(
            chunks=[KnowledgeContextChunk(chunk=KnowledgeChunk(text="cached"))],
            total_chunks=1,
            total_tokens=5,
            cache_hit=True,
        )
        self.cache.get_retrieval_result = AsyncMock(return_value=cached_result)

        assembled = AssembledContext(
            text="cached context",
            chunks=cached_result.chunks,
            tokens_used=5,
            total_available=2048,
            truncated=False,
            metadata={"compression_ratio": 1.0},
        )
        self.assembler.assemble = AsyncMock(return_value=assembled)

        output = await self.builder.build(query="cached", correlation_id="corr-1")
        assert output["context"] == "cached context"
        assert output["metadata"]["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_build_empty_query_returns_error(self):
        self.validator.validate_query = MagicMock(side_effect=ContextValidationError("Query cannot be empty"))
        self.health.record_failure = MagicMock()

        output = await self.builder.build(query="", correlation_id="corr-1")
        assert "error" in output

    @pytest.mark.asyncio
    async def test_build_context_retrieval_error(self):
        self.validator.validate_query = MagicMock()
        self.validator.validate_config = MagicMock()
        self.cache.get_retrieval_result = AsyncMock(return_value=None)
        self.provider.retrieve = AsyncMock(side_effect=ContextRetrievalError("retrieval failed"))
        self.health.record_failure = MagicMock()

        output = await self.builder.build(query="test", correlation_id="corr-1")
        assert "error" in output
        assert "retrieval failed" in output["error"]

    @pytest.mark.asyncio
    async def test_build_unexpected_error(self):
        self.validator.validate_query = MagicMock()
        self.validator.validate_config = MagicMock()
        self.provider.retrieve = AsyncMock(side_effect=RuntimeError("unexpected"))
        self.health.record_failure = MagicMock()

        output = await self.builder.build(query="test", correlation_id="corr-1")
        assert "error" in output
        assert "Knowledge context build failed" in output["error"]

    @pytest.mark.asyncio
    async def test_build_records_metrics(self):
        self.validator.validate_query = MagicMock()
        self.validator.validate_config = MagicMock()
        self.metrics.record_retrieval = MagicMock()
        self.metrics.record_tokens = MagicMock()
        self.metrics.record_compression = MagicMock()
        self.health.record_success = MagicMock()

        result = KnowledgeContextResult(
            chunks=[KnowledgeContextChunk(chunk=KnowledgeChunk(text="test"))],
            total_chunks=1,
            total_tokens=10,
            retrieval_latency_ms=5.0,
            cache_hit=False,
        )
        self.provider.retrieve = AsyncMock(return_value=result)

        assembled = AssembledContext(
            text="test",
            chunks=result.chunks,
            tokens_used=10,
            total_available=2048,
            truncated=False,
            metadata={"compression_ratio": 0.5, "total_available": 2048},
        )
        self.assembler.assemble = AsyncMock(return_value=assembled)

        await self.builder.build(query="test", correlation_id="corr-1")
        self.metrics.record_retrieval.assert_called_once()
        self.metrics.record_tokens.assert_called_once_with(10)

    def test_health_check(self):
        self.health.check = MagicMock(return_value={"status": "healthy"})
        result = self.builder.health_check()
        assert result["status"] == "healthy"

    def test_get_metrics(self):
        self.metrics.get_metrics = MagicMock(return_value={"total_retrievals": 0})
        result = self.builder.get_metrics()
        assert result["total_retrievals"] == 0

    def test_get_statistics(self):
        self.statistics.get_statistics = MagicMock(return_value=ContextStatisticsData())
        result = self.builder.get_statistics()
        assert result.total_requests == 0

    def test_reset_metrics(self):
        self.metrics.reset = MagicMock()
        self.builder.reset_metrics()
        self.metrics.reset.assert_called_once()

    def test_reset_statistics(self):
        self.statistics.reset = MagicMock()
        self.builder.reset_statistics()
        self.statistics.reset.assert_called_once()


class TestKnowledgeContextBuilderNoMocks:
    @pytest.mark.asyncio
    async def test_build_with_default_dependencies(self):
        provider = AsyncMock()
        provider.retrieve = AsyncMock(return_value=KnowledgeContextResult())
        builder = KnowledgeContextBuilder(provider=provider)
        result = await builder.build(query="test")
        assert "context" in result


class TestKnowledgeContextHealthChecker:
    def setup_method(self) -> None:
        self.checker = KnowledgeContextHealthChecker()

    def test_initial_healthy(self):
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.HEALTHY.value
        assert health["success_rate"] == 1.0

    def test_record_success_keeps_healthy(self):
        self.checker.record_success()
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.HEALTHY.value

    def test_degraded_after_threshold(self):
        for i in range(5):
            self.checker.record_failure(f"error_{i}")
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.DEGRADED.value

    def test_unhealthy_after_high_threshold(self):
        for i in range(20):
            self.checker.record_failure(f"error_{i}")
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.UNHEALTHY.value

    def test_success_clears_failures(self):
        for i in range(6):
            self.checker.record_failure(f"error_{i}")
        self.checker.record_success()
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.HEALTHY.value

    def test_remains_unhealthy_after_success_when_not_fully_cleared(self):
        for i in range(25):
            self.checker.record_failure(f"error_{i}")
        self.checker.record_success()
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.HEALTHY.value

    def test_consecutive_failures_count(self):
        self.checker.record_failure("err")
        self.checker.record_failure("err")
        health = self.checker.check()
        assert health["consecutive_failures"] == 2

    def test_failure_records_last_error(self):
        self.checker.record_failure("something went wrong")
        health = self.checker.check()
        assert health["last_error"] == "something went wrong"

    def test_reset(self):
        self.checker.record_failure("err")
        self.checker.reset()
        health = self.checker.check()
        assert health["status"] == KnowledgeContextHealthStatus.HEALTHY.value
        assert health["total_requests"] == 0

    def test_success_rate_calculation(self):
        self.checker.record_success()
        self.checker.record_success()
        self.checker.record_failure("err")
        health = self.checker.check()
        assert health["success_rate"] == pytest.approx(2.0 / 3.0)

    def test_success_rate_no_requests(self):
        health = self.checker.check()
        assert health["success_rate"] == 1.0


class TestKnowledgeContextMetricsCollector:
    def setup_method(self) -> None:
        self.collector = KnowledgeContextMetricsCollector()

    def test_default_metrics(self):
        assert self.collector.metrics.total_retrievals == 0
        assert self.collector.metrics.cache_hits == 0
        assert self.collector.metrics.cache_misses == 0

    def test_record_retrieval(self):
        self.collector.record_retrieval(chunks_retrieved=10, latency_ms=100.0, cache_hit=False)
        assert self.collector.metrics.total_retrievals == 1
        assert self.collector.metrics.cache_misses == 1
        assert self.collector.metrics.total_chunks_retrieved == 10

    def test_record_retrieval_cache_hit(self):
        self.collector.record_retrieval(chunks_retrieved=5, latency_ms=50.0, cache_hit=True)
        assert self.collector.metrics.cache_hits == 1
        assert self.collector.metrics.cache_misses == 0

    def test_record_tokens(self):
        self.collector.record_tokens(500)
        assert self.collector.metrics.total_tokens_used == 500

    def test_record_compression(self):
        self.collector.record_compression(tokens_saved=200)
        assert self.collector.metrics.compressions_performed == 1
        assert self.collector.metrics.tokens_saved_by_compression == 200

    def test_record_multiple_compressions(self):
        self.collector.record_compression(100)
        self.collector.record_compression(50)
        assert self.collector.metrics.compressions_performed == 2
        assert self.collector.metrics.tokens_saved_by_compression == 150

    def test_get_metrics(self):
        self.collector.record_retrieval(chunks_retrieved=10, latency_ms=100.0, cache_hit=True)
        metrics = self.collector.get_metrics()
        assert metrics["total_retrievals"] == 1
        assert metrics["cache_hits"] == 1
        assert metrics["cache_hit_ratio"] == 1.0

    def test_get_metrics_cache_hit_ratio_default(self):
        metrics = self.collector.get_metrics()
        assert metrics["cache_hit_ratio"] == 0.0

    def test_get_metrics_average_latency(self):
        self.collector.record_retrieval(chunks_retrieved=1, latency_ms=200.0, cache_hit=False)
        metrics = self.collector.get_metrics()
        assert metrics["average_latency_ms"] == 200.0

    def test_get_metrics_average_latency_no_requests(self):
        metrics = self.collector.get_metrics()
        assert metrics["average_latency_ms"] == 0.0

    def test_reset(self):
        self.collector.record_retrieval(chunks_retrieved=10, latency_ms=100.0)
        self.collector.reset()
        assert self.collector.metrics.total_retrievals == 0
        assert self.collector.metrics.total_chunks_retrieved == 0


class TestKnowledgeContextStatisticsCollector:
    def setup_method(self) -> None:
        self.collector = KnowledgeContextStatisticsCollector()

    def test_default_statistics(self):
        stats = self.collector.get_statistics()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0

    def test_record_successful_request(self):
        self.collector.record_request(success=True, chunks_served=5, tokens_served=100, latency_ms=50.0)
        stats = self.collector.get_statistics()
        assert stats.total_requests == 1
        assert stats.successful_requests == 1
        assert stats.total_chunks_served == 5
        assert stats.total_tokens_served == 100

    def test_record_failed_request(self):
        self.collector.record_request(success=False)
        stats = self.collector.get_statistics()
        assert stats.total_requests == 1
        assert stats.failed_requests == 1

    def test_record_truncated_request(self):
        self.collector.record_request(success=True, truncated=True)
        stats = self.collector.get_statistics()
        assert stats.truncated_responses == 1

    def test_record_knowledge_coverage(self):
        self.collector.record_knowledge_coverage("pdf")
        self.collector.record_knowledge_coverage("pdf")
        self.collector.record_knowledge_coverage("txt")
        stats = self.collector.get_statistics()
        assert stats.knowledge_coverage["pdf"] == 2
        assert stats.knowledge_coverage["txt"] == 1

    def test_record_error(self):
        self.collector.record_error("ContextRetrievalError")
        self.collector.record_error("ContextRetrievalError")
        stats = self.collector.get_statistics()
        assert stats.errors_by_type["ContextRetrievalError"] == 2

    def test_average_latency(self):
        self.collector.record_request(success=True, latency_ms=100.0)
        self.collector.record_request(success=True, latency_ms=200.0)
        stats = self.collector.get_statistics()
        assert stats.average_latency_ms == 150.0

    def test_reset(self):
        self.collector.record_request(success=True, chunks_served=10, tokens_served=100, latency_ms=50.0)
        self.collector.reset()
        stats = self.collector.get_statistics()
        assert stats.total_requests == 0
        assert stats.total_chunks_served == 0


class TestKnowledgeContextPolicy:
    def setup_method(self) -> None:
        self.policy = KnowledgeContextPolicy()

    def test_defaults(self):
        assert self.policy.max_knowledge_tokens == 2048
        assert self.policy.max_retrieved_chunks == 20
        assert self.policy.min_relevance_score == 0.3

    def test_to_config(self):
        config = self.policy.to_config()
        assert isinstance(config, KnowledgeContextConfig)
        assert config.max_knowledge_tokens == self.policy.max_knowledge_tokens
        assert config.max_retrieved_chunks == self.policy.max_retrieved_chunks
        assert config.compression_strategy == self.policy.compression_strategy
        assert config.chunk_selection == self.policy.chunk_selection

    def test_to_config_overrides(self):
        policy = KnowledgeContextPolicy(
            max_knowledge_tokens=4096,
            max_retrieved_chunks=10,
            compression_strategy=CompressionStrategy.EXTRACT,
            chunk_selection=ChunkSelectionStrategy.DIVERSITY,
            default_language="en",
            default_tenant="tenant-1",
        )
        config = policy.to_config()
        assert config.max_knowledge_tokens == 4096
        assert config.max_retrieved_chunks == 10
        assert config.compression_strategy == CompressionStrategy.EXTRACT
        assert config.chunk_selection == ChunkSelectionStrategy.DIVERSITY
        assert config.language_filter == "en"
        assert config.tenant_filter == "tenant-1"

    def test_create_budget(self):
        budget = self.policy.create_budget()
        assert isinstance(budget, TokenBudget)
        assert budget.knowledge_tokens == self.policy.max_knowledge_tokens
        assert budget.total_tokens == 8192

    def test_create_budget_custom(self):
        budget = self.policy.create_budget(total_tokens=16384, conversation_tokens=4096, memory_tokens=2048, reserved_tokens=2048)
        assert budget.total_tokens == 16384
        assert budget.conversation_tokens == 4096
        assert budget.memory_tokens == 2048
        assert budget.reserved_tokens == 2048
        assert budget.knowledge_tokens == self.policy.max_knowledge_tokens


class TestKnowledgeContextCache:
    def setup_method(self) -> None:
        self.cache_service = AsyncMock()
        self.cache = KnowledgeContextCache(cache_service=self.cache_service)

    @pytest.mark.asyncio
    async def test_get_returns_none_when_miss(self):
        self.cache_service.get = AsyncMock(return_value=None)
        result = await self.cache.get("some_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self):
        import json
        self.cache_service.get = AsyncMock(return_value=json.dumps({"key": "value"}))
        result = await self.cache.get("some_key")
        assert result["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_returns_raw_data_when_not_string(self):
        self.cache_service.get = AsyncMock(return_value={"direct": "object"})
        result = await self.cache.get("some_key")
        assert result["direct"] == "object"

    @pytest.mark.asyncio
    async def test_get_error_raises_cache_error(self):
        from application.knowledge_context.exceptions import ContextCacheError
        self.cache_service.get = AsyncMock(side_effect=Exception("redis down"))
        with pytest.raises(ContextCacheError, match="Cache get failed"):
            await self.cache.get("key")

    @pytest.mark.asyncio
    async def test_set_string_value(self):
        self.cache_service.set = AsyncMock()
        await self.cache.set("key", "string_value", ttl=100)
        self.cache_service.set.assert_called_once_with("key", "string_value", ttl=100)

    @pytest.mark.asyncio
    async def test_set_non_string_value(self):
        self.cache_service.set = AsyncMock()
        await self.cache.set("key", {"nested": "data"}, ttl=200)
        args, kwargs = self.cache_service.set.call_args
        assert kwargs["ttl"] == 200

    @pytest.mark.asyncio
    async def test_set_error_raises_cache_error(self):
        self.cache_service.set = AsyncMock(side_effect=Exception("set failed"))
        from application.knowledge_context.exceptions import ContextCacheError
        with pytest.raises(ContextCacheError, match="Cache set failed"):
            await self.cache.set("key", "value")

    @pytest.mark.asyncio
    async def test_delete(self):
        self.cache_service.delete = AsyncMock()
        await self.cache.delete("some_key")
        self.cache_service.delete.assert_called_once_with("some_key")

    @pytest.mark.asyncio
    async def test_delete_error_raises_cache_error(self):
        self.cache_service.delete = AsyncMock(side_effect=Exception("delete failed"))
        from application.knowledge_context.exceptions import ContextCacheError
        with pytest.raises(ContextCacheError, match="Cache delete failed"):
            await self.cache.delete("key")

    @pytest.mark.asyncio
    async def test_invalidate_for_document(self):
        self.cache_service.set = AsyncMock()
        await self.cache.invalidate_for_document("doc-123")
        self.cache_service.set.assert_called_once()
        args, kwargs = self.cache_service.set.call_args
        assert "version" in args[0]

    @pytest.mark.asyncio
    async def test_invalidate_for_document_error(self):
        self.cache_service.set = AsyncMock(side_effect=Exception("invalidate failed"))
        from application.knowledge_context.exceptions import ContextCacheError
        with pytest.raises(ContextCacheError, match="Cache invalidation failed"):
            await self.cache.invalidate_for_document("doc-123")

    @pytest.mark.asyncio
    async def test_get_or_compute_returns_cached(self):
        self.cache_service.get = AsyncMock(return_value='"cached_value"')
        result = await self.cache.get_or_compute("key", "compute_value", ttl=300)
        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_get_or_compute_computes_when_miss(self):
        self.cache_service.get = AsyncMock(return_value=None)
        self.cache_service.set = AsyncMock()
        result = await self.cache.get_or_compute("key", "computed_value", ttl=300)
        assert result == "computed_value"

    @pytest.mark.asyncio
    async def test_get_or_compute_with_callable(self):
        self.cache_service.get = AsyncMock(return_value=None)
        self.cache_service.set = AsyncMock()
        async def async_compute():
            return "callable_result"
        result = await self.cache.get_or_compute("key", async_compute, ttl=300)
        assert result == "callable_result"

    @pytest.mark.asyncio
    async def test_cache_retrieval_result(self):
        self.cache_service.set = AsyncMock()
        result = KnowledgeContextResult()
        key = await self.cache.cache_retrieval_result("query", "hash", result)
        assert "knowledge:context:retrieval:" in key

    @pytest.mark.asyncio
    async def test_get_retrieval_result(self):
        self.cache_service.get = AsyncMock(return_value=None)
        result = await self.cache.get_retrieval_result("query", "hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_retrieval_result_hit(self):
        import json
        self.cache_service.get = AsyncMock(return_value=json.dumps({"total_chunks": 0}))
        result = await self.cache.get_retrieval_result("query", "hash")
        assert result is not None

    @pytest.mark.asyncio
    async def test_clear(self):
        await self.cache.clear()

    def test_make_version_key(self):
        key = self.cache._make_version_key("doc-1")
        assert "version" in key
        assert "doc-1" in key
