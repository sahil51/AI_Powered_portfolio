from __future__ import annotations

import time

from application.embedding.interfaces import EmbeddingProvider
from application.embedding.models import EmbeddingProviderType, EmbeddingRequest
from application.retrieval.fusion import ScoreFusion
from application.retrieval.interfaces import KeywordRetriever, MetadataRetriever, Reranker, SemanticRetriever
from application.retrieval.models import (
    RetrievalRequest,
    RetrievalResult,
    SearchMode,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from application.retrieval.validator import RetrievalValidator


class HybridRetrievalService:
    def __init__(
        self,
        semantic_retriever: SemanticRetriever | None = None,
        keyword_retriever: KeywordRetriever | None = None,
        metadata_retriever: MetadataRetriever | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: Reranker | None = None,
        fusion: ScoreFusion | None = None,
        validator: RetrievalValidator | None = None,
    ) -> None:
        self._semantic_retriever = semantic_retriever
        self._keyword_retriever = keyword_retriever
        self._metadata_retriever = metadata_retriever
        self._embedding_provider = embedding_provider
        self._reranker = reranker
        self._fusion = fusion or ScoreFusion()
        self._validator = validator or RetrievalValidator()

    async def search(self, query: SearchQuery) -> SearchResponse:
        self._validator.validate_query(query)
        start = time.time()

        query_embedding = query.query_embedding
        if query_embedding is None and query.query_text and query.mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            if self._embedding_provider:
                emb_request = EmbeddingRequest(text=query.query_text, provider=EmbeddingProviderType.CUSTOM)
                emb_response = self._embedding_provider.generate(emb_request)
                query_embedding = emb_response.embedding

        semantic_result: RetrievalResult | None = None
        keyword_result: RetrievalResult | None = None
        metadata_result: RetrievalResult | None = None

        if query.mode in (SearchMode.SEMANTIC, SearchMode.HYBRID) and self._semantic_retriever and query_embedding:
            sem_request = RetrievalRequest(
                embedding=query_embedding,
                query_text=query.query_text,
                top_k=query.config.semantic_candidate_k,
                filter=query.filter,
                min_score=query.config.min_semantic_score,
            )
            semantic_result = await self._semantic_retriever.search(sem_request)

        if query.mode in (SearchMode.KEYWORD, SearchMode.HYBRID) and self._keyword_retriever and query.query_text:
            keyword_result = await self._keyword_retriever.search(
                query=query.query_text,
                top_k=query.config.keyword_candidate_k,
                filter=query.filter,
            )

        if query.mode == SearchMode.METADATA and self._metadata_retriever:
            metadata_result = await self._metadata_retriever.search(
                filter=query.filter,
                top_k=query.config.metadata_candidate_k,
            )

        fused_results = self._fuse_results(
            semantic_result=semantic_result,
            keyword_result=keyword_result,
            metadata_result=metadata_result,
            query=query,
        )

        if query.config.rerank_enabled and self._reranker and fused_results:
            if query.config.enable_mmr and query_embedding:
                mmr = __import__("application.retrieval.reranker", fromlist=["MMRReranker"]).MMRReranker
                mmr_reranker = mmr(lambda_=query.config.mmr_lambda)
                embeddings_list = [r.chunk.embedding or [] for r in fused_results]
                fused_results = await mmr_reranker.rerank(fused_results, query.config.mmr_top_k, embeddings_list)

            reranked = await self._reranker.rerank(
                query=query.query_text,
                candidates=fused_results[:query.config.rerank_top_k],
                top_k=query.config.final_top_k,
            )
            fused_results = reranked

        for i, r in enumerate(fused_results[:query.config.final_top_k]):
            r.rank = i + 1

        final = fused_results[:query.config.final_top_k]
        latency_ms = (time.time() - start) * 1000

        return SearchResponse(
            results=final,
            total_hits=len(final),
            total_documents=len(set(r.chunk.document_id for r in final)),
            query=query,
            latency_ms=latency_ms,
            retrieval_breakdown=self._build_breakdown(semantic_result, keyword_result, metadata_result, len(final)),
        )

    def _fuse_results(
        self,
        semantic_result: RetrievalResult | None,
        keyword_result: RetrievalResult | None,
        metadata_result: RetrievalResult | None,
        query: SearchQuery,
    ) -> list[SearchResult]:
        sem_scores: list[tuple[str, float]] = []
        kw_scores: list[tuple[str, float]] = []
        meta_scores: list[tuple[str, float]] = []

        sem_map: dict[str, SearchResult] = {}
        kw_map: dict[str, SearchResult] = {}
        meta_map: dict[str, SearchResult] = {}

        if semantic_result and semantic_result.chunks:
            norm_sem = ScoreFusion.normalize_scores(semantic_result.scores, query.config.normalization_method)
            for chunk, score in zip(semantic_result.chunks, norm_sem, strict=False):
                cid = str(chunk.chunk_id)
                sem_scores.append((cid, score))
                sem_map[cid] = SearchResult(chunk=chunk, semantic_score=score, score=score)

        if keyword_result and keyword_result.chunks:
            norm_kw = ScoreFusion.normalize_scores(keyword_result.scores, query.config.normalization_method)
            for chunk, score in zip(keyword_result.chunks, norm_kw, strict=False):
                cid = str(chunk.chunk_id)
                kw_scores.append((cid, score))
                kw_map[cid] = SearchResult(chunk=chunk, keyword_score=score, score=score)

        if metadata_result and metadata_result.chunks:
            norm_meta = ScoreFusion.normalize_scores(metadata_result.scores, query.config.normalization_method)
            for chunk, score in zip(metadata_result.chunks, norm_meta, strict=False):
                cid = str(chunk.chunk_id)
                meta_scores.append((cid, score))
                meta_map[cid] = SearchResult(chunk=chunk, metadata_score=score, score=score)

        if query.mode == SearchMode.HYBRID:
            weights = (query.config.semantic_weight, query.config.keyword_weight, query.config.metadata_weight)
            fused = self._fusion.weighted_avg(
                sem_scores, kw_scores, meta_scores,
                weights=weights,
                strategy=query.config.fusion_strategy,
            )
        elif query.mode == SearchMode.SEMANTIC:
            fused = dict(sem_scores)
        elif query.mode == SearchMode.KEYWORD:
            fused = dict(kw_scores)
        else:
            fused = dict(meta_scores)

        all_results: dict[str, SearchResult] = {}
        for cid, score in fused.items():
            result = sem_map.get(cid) or kw_map.get(cid) or meta_map.get(cid)
            if result is None:
                continue
            result.score = score
            if cid in sem_map:
                result.semantic_score = sem_map[cid].semantic_score
            if cid in kw_map:
                result.keyword_score = kw_map[cid].keyword_score
            if cid in meta_map:
                result.metadata_score = meta_map[cid].metadata_score
            all_results[cid] = result

        sorted_results = sorted(all_results.values(), key=lambda r: r.score, reverse=True)

        if query.config.min_hybrid_score > 0:
            sorted_results = [r for r in sorted_results if r.score >= query.config.min_hybrid_score]

        return sorted_results

    @staticmethod
    def _build_breakdown(
        semantic_result: RetrievalResult | None,
        keyword_result: RetrievalResult | None,
        metadata_result: RetrievalResult | None,
        final_count: int,
    ) -> dict:
        return {
            "semantic_count": len(semantic_result.chunks) if semantic_result else 0,
            "keyword_count": len(keyword_result.chunks) if keyword_result else 0,
            "metadata_count": len(metadata_result.chunks) if metadata_result else 0,
            "fused_count": final_count,
        }
