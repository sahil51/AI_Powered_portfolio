from __future__ import annotations

import time

from application.knowledge_context.exceptions import ContextRetrievalError
from application.knowledge_context.interfaces import KnowledgeContextProvider
from application.knowledge_context.models import (
    ChunkSelectionStrategy,
    KnowledgeContextChunk,
    KnowledgeContextConfig,
    KnowledgeContextResult,
)
from application.retrieval.models import SearchFilter, SearchMode, SearchQuery
from application.retrieval.search_service import KnowledgeSearchService
from domain.knowledge.chunk import KnowledgeChunk


class KnowledgeRetrievalProvider(KnowledgeContextProvider):
    def __init__(self, search_service: KnowledgeSearchService) -> None:
        self._search_service = search_service

    async def retrieve(
        self,
        query: str,
        config: KnowledgeContextConfig,
        correlation_id: str = "",
    ) -> KnowledgeContextResult:
        start = time.monotonic()
        try:
            search_filter = self._build_filter(config)
            search_query = SearchQuery(
                query_text=query,
                mode=SearchMode.HYBRID,
                filter=search_filter,
                correlation_id=correlation_id,
            )

            response = await self._search_service.search(search_query)

            chunks: list[KnowledgeContextChunk] = []
            for result in response.results:
                chunk = KnowledgeContextChunk(
                    chunk=result.chunk,
                    document_title=result.document.title if result.document else "",
                    document_type=result.document.doc_type.value if result.document else "",
                    score=result.score,
                    rank=result.rank,
                )
                chunks.append(chunk)

            strategy = config.chunk_selection
            if strategy == ChunkSelectionStrategy.RELEVANCE:
                chunks.sort(key=lambda c: c.score, reverse=True)
            elif strategy == ChunkSelectionStrategy.RECENCY:
                chunks.sort(key=lambda c: c.chunk.created_at.timestamp() if c.chunk.created_at else 0, reverse=True)
            elif strategy == ChunkSelectionStrategy.DIVERSITY:
                chunks = self._diversity_ranking(chunks)

            selected = chunks[: config.max_retrieved_chunks]
            selected = [c for c in selected if c.score >= config.min_relevance_score]

            total_tokens = sum(
                len(c.chunk.text.split()) for c in selected
            )

            latency = (time.monotonic() - start) * 1000

            return KnowledgeContextResult(
                chunks=selected,
                total_chunks=len(selected),
                total_tokens=total_tokens,
                retrieval_latency_ms=latency,
                query=query,
                correlation_id=correlation_id,
            )

        except Exception as e:
            raise ContextRetrievalError(f"Knowledge retrieval failed: {e}") from e

    async def retrieve_by_ids(
        self,
        chunk_ids: list[str],
        correlation_id: str = "",
    ) -> list[KnowledgeChunk]:
        results: list[KnowledgeChunk] = []
        for cid in chunk_ids:
            filter = SearchFilter()
            filter.custom = {"chunk_id": cid}
            query = SearchQuery(
                query_text="",
                mode=SearchMode.METADATA,
                filter=filter,
                correlation_id=correlation_id,
            )
            try:
                response = await self._search_service.search(query)
                for r in response.results:
                    results.append(r.chunk)
            except Exception:
                continue
        return results

    def _build_filter(self, config: KnowledgeContextConfig) -> SearchFilter:
        from domain.knowledge.value_objects import DocumentType as DocType
        search_filter = SearchFilter()
        if config.excluded_doc_types:
            valid_dt = [d for d in config.excluded_doc_types if d in DocType._value2member_map_]
            search_filter.doc_types = [DocType(dt) for dt in valid_dt]
        if config.included_doc_types:
            dt_val = config.included_doc_types[0]
            search_filter.doc_type = DocType(dt_val) if dt_val in DocType._value2member_map_ else None
        if config.language_filter:
            search_filter.language = config.language_filter
        if config.tenant_filter:
            search_filter.custom = search_filter.custom or {}
            search_filter.custom["tenant_id"] = config.tenant_filter
        return search_filter

    def _diversity_ranking(
        self, chunks: list[KnowledgeContextChunk]
    ) -> list[KnowledgeContextChunk]:
        if not chunks:
            return chunks

        ranked: list[KnowledgeContextChunk] = [chunks[0]]
        remaining = list(chunks[1:])

        while remaining and len(ranked) < len(chunks):
            best_idx = 0
            best_min_sim = float("inf")
            for i, candidate in enumerate(remaining):
                min_sim = min(
                    self._text_similarity(candidate.chunk.text, r.chunk.text)
                    for r in ranked
                )
                if min_sim < best_min_sim:
                    best_min_sim = min_sim
                    best_idx = i
            ranked.append(remaining.pop(best_idx))

        return ranked

    def _text_similarity(self, t1: str, t2: str) -> float:
        set1 = set(t1.lower().split())
        set2 = set(t2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union)
