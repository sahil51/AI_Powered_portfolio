from __future__ import annotations

import time

from application.knowledge_context.compressor import KnowledgeContextCompressor as DefaultCompressor
from application.knowledge_context.exceptions import ContextAssemblyError
from application.knowledge_context.interfaces import KnowledgeContextAssembler, KnowledgeContextCompressor
from application.knowledge_context.models import (
    AssembledContext,
    ChunkSelectionStrategy,
    KnowledgeContextChunk,
    KnowledgeContextConfig,
    KnowledgeContextResult,
    TokenBudget,
)


class KnowledgeContextAssemblerImpl(KnowledgeContextAssembler):
    def __init__(
        self,
        compressor: KnowledgeContextCompressor | None = None,
    ) -> None:
        self._compressor = compressor or DefaultCompressor()

    async def assemble(
        self,
        result: KnowledgeContextResult,
        budget: TokenBudget,
        config: KnowledgeContextConfig,
    ) -> AssembledContext:
        start = time.monotonic()
        try:
            chunks = self.select_chunks(
                chunks=result.chunks,
                strategy=config.chunk_selection,
                max_chunks=config.max_retrieved_chunks,
            )

            if config.enable_deduplication:
                chunks = self._deduplicate(chunks)

            if config.enable_section_grouping:
                chunks = self._group_by_section(chunks)

            if config.enable_semantic_ordering:
                chunks = self._semantic_order(chunks)

            context_parts: list[str] = []
            total_tokens = 0
            max_tokens = budget.knowledge_tokens

            for chunk in chunks:
                attribution = ""
                if config.enable_source_attribution:
                    attribution = f"[Source: {chunk.document_title}] "
                entry = f"{attribution}{chunk.chunk.text}"

                if config.enable_metadata_preservation and chunk.chunk.heading:
                    entry = f"## {chunk.chunk.heading}\n{entry}"

                entry_tokens = self._compressor.estimate_tokens(entry)

                if total_tokens + entry_tokens > max_tokens:
                    if config.enable_compression:
                        compressed_text, saved = self._compressor.compress(
                            text=entry,
                            strategy=config.compression_strategy,
                            max_tokens=max_tokens - total_tokens,
                        )
                        if compressed_text:
                            context_parts.append(compressed_text)
                            total_tokens += self._compressor.estimate_tokens(compressed_text)
                    break

                context_parts.append(entry)
                total_tokens += entry_tokens

            text = "\n\n".join(context_parts)

            latency = (time.monotonic() - start) * 1000
            result.compression_latency_ms = latency

            return AssembledContext(
                text=text,
                chunks=chunks,
                tokens_used=total_tokens,
                total_available=max_tokens,
                truncated=total_tokens >= max_tokens,
                metadata={
                    "total_chunks": len(chunks),
                    "chunks_used": len(context_parts),
                    "total_tokens": total_tokens,
                    "max_tokens": max_tokens,
                    "compression_ratio": total_tokens / max(max_tokens, 1),
                    "assembly_latency_ms": latency,
                },
            )

        except Exception as e:
            raise ContextAssemblyError(f"Context assembly failed: {e}") from e

    def select_chunks(
        self,
        chunks: list[KnowledgeContextChunk],
        strategy: ChunkSelectionStrategy,
        max_chunks: int,
    ) -> list[KnowledgeContextChunk]:
        if strategy == ChunkSelectionStrategy.RELEVANCE:
            chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
        elif strategy == ChunkSelectionStrategy.RECENCY:
            chunks = sorted(
                chunks,
                key=lambda c: c.chunk.created_at.timestamp() if c.chunk.created_at else 0,
                reverse=True,
            )
        elif strategy == ChunkSelectionStrategy.DIVERSITY:
            chunks = self._diversity_select(chunks)

        return chunks[:max_chunks]

    def _deduplicate(self, chunks: list[KnowledgeContextChunk]) -> list[KnowledgeContextChunk]:
        seen: set[str] = set()
        unique: list[KnowledgeContextChunk] = []
        for chunk in chunks:
            checksum = chunk.chunk.checksum
            if checksum and checksum not in seen:
                seen.add(checksum)
                unique.append(chunk)
        return unique

    def _group_by_section(self, chunks: list[KnowledgeContextChunk]) -> list[KnowledgeContextChunk]:
        section_order: list[str] = []
        sections: dict[str, list[KnowledgeContextChunk]] = {}
        for chunk in chunks:
            section = chunk.chunk.section or chunk.chunk.heading or "_default"
            if section not in sections:
                sections[section] = []
                section_order.append(section)
            sections[section].append(chunk)

        result: list[KnowledgeContextChunk] = []
        for section in section_order:
            result.extend(sections[section])
        return result

    def _semantic_order(self, chunks: list[KnowledgeContextChunk]) -> list[KnowledgeContextChunk]:
        return chunks

    def _diversity_select(self, chunks: list[KnowledgeContextChunk]) -> list[KnowledgeContextChunk]:
        if not chunks:
            return chunks
        ranked: list[KnowledgeContextChunk] = [chunks[0]]
        remaining = list(chunks[1:])
        while remaining and len(ranked) < len(chunks):
            best_idx = 0
            best_min_sim = float("inf")
            for i, candidate in enumerate(remaining):
                min_sim = min(
                    self._jaccard_similarity(candidate.chunk.text, r.chunk.text)
                    for r in ranked
                )
                if min_sim < best_min_sim:
                    best_min_sim = min_sim
                    best_idx = i
            ranked.append(remaining.pop(best_idx))
        return ranked

    def _jaccard_similarity(self, t1: str, t2: str) -> float:
        set1 = set(t1.lower().split())
        set2 = set(t2.lower().split())
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set1 | set2)
