from __future__ import annotations

from application.knowledge_context.models import (
    AssembledContext,
    ChunkSelectionStrategy,
    CompressionStrategy,
    ContextMetricsData,
    ContextSourcePriority,
    ContextStatisticsData,
    KnowledgeContextChunk,
    KnowledgeContextConfig,
    KnowledgeContextResult,
    TokenBudget,
)
from domain.knowledge.chunk import KnowledgeChunk


class TestKnowledgeContextChunk:
    def test_defaults(self):
        c = KnowledgeContextChunk(chunk=KnowledgeChunk())
        assert isinstance(c.chunk, KnowledgeChunk)
        assert c.document_title == ""
        assert c.document_type == ""
        assert c.score == 0.0
        assert c.rank == 0
        assert c.source_priority == ContextSourcePriority.KNOWLEDGE

    def test_with_values(self):
        chunk = KnowledgeChunk(text="test")
        c = KnowledgeContextChunk(
            chunk=chunk,
            document_title="Doc",
            document_type="pdf",
            score=0.8,
            rank=2,
            source_priority=ContextSourcePriority.MEMORY,
        )
        assert c.chunk == chunk
        assert c.document_title == "Doc"
        assert c.document_type == "pdf"
        assert c.score == 0.8
        assert c.rank == 2
        assert c.source_priority == ContextSourcePriority.MEMORY


class TestChunkSelectionStrategy:
    def test_relevance(self):
        assert ChunkSelectionStrategy.RELEVANCE.value == "relevance"

    def test_recency(self):
        assert ChunkSelectionStrategy.RECENCY.value == "recency"

    def test_diversity(self):
        assert ChunkSelectionStrategy.DIVERSITY.value == "diversity"

    def test_hybrid(self):
        assert ChunkSelectionStrategy.HYBRID.value == "hybrid"


class TestCompressionStrategy:
    def test_truncate(self):
        assert CompressionStrategy.TRUNCATE.value == "truncate"

    def test_summarize(self):
        assert CompressionStrategy.SUMMARIZE.value == "summarize"

    def test_extract(self):
        assert CompressionStrategy.EXTRACT.value == "extract"

    def test_prioritize(self):
        assert CompressionStrategy.PRIORITIZE.value == "prioritize"


class TestContextSourcePriority:
    def test_conversation(self):
        assert ContextSourcePriority.CONVERSATION.value == 0

    def test_memory(self):
        assert ContextSourcePriority.MEMORY.value == 1

    def test_knowledge(self):
        assert ContextSourcePriority.KNOWLEDGE.value == 2


class TestContextMetricsData:
    def test_defaults(self):
        m = ContextMetricsData()
        assert m.total_retrievals == 0
        assert m.cache_hits == 0
        assert m.cache_misses == 0
        assert m.total_chunks_retrieved == 0
        assert m.total_tokens_used == 0
        assert m.total_latency_ms == 0.0
        assert m.compressions_performed == 0
        assert m.tokens_saved_by_compression == 0

    def test_with_values(self):
        m = ContextMetricsData(
            total_retrievals=10,
            cache_hits=5,
            cache_misses=5,
            total_chunks_retrieved=100,
            total_tokens_used=5000,
            total_latency_ms=250.0,
            compressions_performed=3,
            tokens_saved_by_compression=1500,
        )
        assert m.total_retrievals == 10
        assert m.cache_hits == 5
        assert m.cache_misses == 5
        assert m.total_chunks_retrieved == 100
        assert m.total_tokens_used == 5000
        assert m.total_latency_ms == 250.0
        assert m.compressions_performed == 3
        assert m.tokens_saved_by_compression == 1500


class TestContextStatisticsData:
    def test_defaults(self):
        s = ContextStatisticsData()
        assert s.total_requests == 0
        assert s.successful_requests == 0
        assert s.failed_requests == 0
        assert s.truncated_responses == 0
        assert s.total_chunks_served == 0
        assert s.total_tokens_served == 0
        assert s.average_latency_ms == 0.0
        assert s.knowledge_coverage == {}
        assert s.errors_by_type == {}

    def test_with_values(self):
        s = ContextStatisticsData(
            total_requests=20,
            successful_requests=18,
            failed_requests=2,
            truncated_responses=1,
            total_chunks_served=50,
            total_tokens_served=2000,
            average_latency_ms=150.0,
            knowledge_coverage={"pdf": 10, "txt": 5},
            errors_by_type={"ContextRetrievalError": 2},
        )
        assert s.total_requests == 20
        assert s.successful_requests == 18
        assert s.failed_requests == 2
        assert s.truncated_responses == 1
        assert s.total_chunks_served == 50
        assert s.total_tokens_served == 2000
        assert s.average_latency_ms == 150.0
        assert s.knowledge_coverage["pdf"] == 10
        assert s.errors_by_type["ContextRetrievalError"] == 2


class TestKnowledgeContextConfig:
    def test_defaults(self):
        c = KnowledgeContextConfig()
        assert c.max_knowledge_tokens == 2048
        assert c.max_retrieved_chunks == 20
        assert c.min_relevance_score == 0.3
        assert c.enable_compression is True
        assert c.enable_deduplication is True
        assert c.enable_section_grouping is True
        assert c.enable_semantic_ordering is False
        assert c.enable_metadata_preservation is True
        assert c.enable_source_attribution is True
        assert c.compression_strategy == CompressionStrategy.TRUNCATE
        assert c.chunk_selection == ChunkSelectionStrategy.RELEVANCE
        assert c.prefer_latest_version is True
        assert c.excluded_doc_types == []
        assert c.included_doc_types == []
        assert c.language_filter == ""
        assert c.tenant_filter == ""


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
