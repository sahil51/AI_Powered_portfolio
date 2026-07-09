from __future__ import annotations

from dataclasses import dataclass

from application.knowledge_context.models import (
    ChunkSelectionStrategy,
    CompressionStrategy,
    KnowledgeContextConfig,
    TokenBudget,
)


@dataclass
class KnowledgeContextPolicy:
    max_knowledge_tokens: int = 2048
    max_retrieved_chunks: int = 20
    min_relevance_score: float = 0.3
    enable_compression: bool = True
    enable_deduplication: bool = True
    enable_section_grouping: bool = True
    enable_semantic_ordering: bool = False
    enable_metadata_preservation: bool = True
    enable_source_attribution: bool = True
    compression_strategy: CompressionStrategy = CompressionStrategy.TRUNCATE
    chunk_selection: ChunkSelectionStrategy = ChunkSelectionStrategy.RELEVANCE
    prefer_latest_version: bool = True
    default_language: str = ""
    default_tenant: str = ""

    def to_config(self) -> KnowledgeContextConfig:
        return KnowledgeContextConfig(
            max_knowledge_tokens=self.max_knowledge_tokens,
            max_retrieved_chunks=self.max_retrieved_chunks,
            min_relevance_score=self.min_relevance_score,
            enable_compression=self.enable_compression,
            enable_deduplication=self.enable_deduplication,
            enable_section_grouping=self.enable_section_grouping,
            enable_semantic_ordering=self.enable_semantic_ordering,
            enable_metadata_preservation=self.enable_metadata_preservation,
            enable_source_attribution=self.enable_source_attribution,
            compression_strategy=self.compression_strategy,
            chunk_selection=self.chunk_selection,
            prefer_latest_version=self.prefer_latest_version,
            language_filter=self.default_language,
            tenant_filter=self.default_tenant,
        )

    def create_budget(
        self,
        total_tokens: int = 8192,
        conversation_tokens: int = 2048,
        memory_tokens: int = 1024,
        reserved_tokens: int = 1024,
    ) -> TokenBudget:
        return TokenBudget(
            total_tokens=total_tokens,
            conversation_tokens=conversation_tokens,
            memory_tokens=memory_tokens,
            knowledge_tokens=self.max_knowledge_tokens,
            reserved_tokens=reserved_tokens,
        )


DEFAULT_KNOWLEDGE_CONTEXT_POLICY = KnowledgeContextPolicy()
