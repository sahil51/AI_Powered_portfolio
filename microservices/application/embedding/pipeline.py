from __future__ import annotations

import time

from application.embedding.batching import EmbeddingBatchProcessor
from application.embedding.chunking import ChunkerFactory
from application.embedding.health import EmbeddingHealth, EmbeddingHealthChecker
from application.embedding.interfaces import EmbeddingProvider
from application.embedding.metrics import EmbeddingMetrics, EmbeddingMetricsCollector
from application.embedding.models import (
    EmbeddingBatchResult,
    EmbeddingConfiguration,
    EmbeddingRequest,
)
from application.embedding.statistics import EmbeddingStatistics, EmbeddingStatisticsCollector
from application.embedding.validator import EmbeddingValidator
from domain.knowledge.aggregate import KnowledgeDocument


class EmbeddingPipeline:
    def __init__(
        self,
        provider: EmbeddingProvider,
        config: EmbeddingConfiguration,
        validator: EmbeddingValidator | None = None,
        metrics_collector: EmbeddingMetricsCollector | None = None,
        statistics_collector: EmbeddingStatisticsCollector | None = None,
        health_checker: EmbeddingHealthChecker | None = None,
    ) -> None:
        self._provider = provider
        self._config = config
        self._validator = validator or EmbeddingValidator()
        self._metrics = metrics_collector or EmbeddingMetricsCollector()
        self._statistics = statistics_collector or EmbeddingStatisticsCollector()
        self._health_checker = health_checker or EmbeddingHealthChecker()
        self._batch_processor = EmbeddingBatchProcessor()

    @property
    def configuration(self) -> EmbeddingConfiguration:
        return self._config

    @property
    def provider(self) -> EmbeddingProvider:
        return self._provider

    @property
    def metrics(self) -> EmbeddingMetrics:
        return self._metrics.metrics

    @property
    def statistics(self) -> EmbeddingStatistics:
        return self._statistics.statistics

    def health(self) -> EmbeddingHealth:
        return self._health_checker.check(self._metrics.metrics)

    def process_document(
        self,
        document: KnowledgeDocument,
    ) -> EmbeddingBatchResult:
        start = time.monotonic()
        try:
            chunker = ChunkerFactory.create(
                self._config.chunking_strategy,
                max_size=self._config.max_tokens_per_chunk,
                overlap=self._config.overlap_tokens,
            )

            text = " ".join(chunk.text for chunk in document.chunks) if document.chunks else ""
            if not text.strip():
                return EmbeddingBatchResult(
                    document_id=str(document.document_id),
                    success=False,
                    error="Empty document content",
                )

            chunk_result = chunker.chunk(text)
            raw_chunks = chunk_result.chunks

            validated_chunks = self._validator.validate_chunks(raw_chunks)
            if not validated_chunks:
                return EmbeddingBatchResult(
                    document_id=str(document.document_id),
                    success=False,
                    error="No valid chunks after validation",
                )

            if self._config.enable_deduplication:
                validated_chunks = list(dict.fromkeys(validated_chunks))

            requests = [
                EmbeddingRequest(
                    chunk_id=f"{document.document_id}_{i}",
                    text=chunk_text,
                    model=self._config.model,
                    provider=self._config.provider,
                )
                for i, chunk_text in enumerate(validated_chunks)
            ]

            batches = self._batch_processor.split_into_batches(requests, self._config.batch_size)
            total_requests = len(requests)

            all_embeddings: list[list[float]] = []
            all_chunks: list[str] = []
            total_tokens = 0
            total_success = True

            for batch in batches:
                batch_embeddings: list[list[float]] = []
                for req in batch:
                    self._validator.validate_request(req)
                    resp = self._provider.generate(req)
                    self._validator.validate_response(resp)
                    if resp.embedding:
                        self._validator.validate_embedding_dimension(
                            resp.dimension, self._config.dimensions
                        )
                        batch_embeddings.append(resp.embedding)
                        all_chunks.append(req.text)
                        total_tokens += resp.tokens_used
                        self._metrics.record_request(
                            req.provider, req.model, resp.latency_ms,
                            tokens_used=resp.tokens_used, success=True,
                        )
                        self._statistics.record_request(req.provider, req.model, success=True)
                    else:
                        total_success = False
                        self._metrics.record_request(
                            req.provider, req.model, resp.latency_ms,
                            tokens_used=0, success=False,
                        )
                        self._statistics.record_request(req.provider, req.model, success=False)
                    self._metrics.record_chunk_processed()
                    self._statistics.record_chunk(document.doc_type.value)
                    self._statistics.record_tokens(resp.tokens_used)

                all_embeddings.extend(batch_embeddings)

            self._metrics.record_document_processed()
            latency = (time.monotonic() - start) * 1000

            result = EmbeddingBatchResult(
                document_id=str(document.document_id),
                chunks=all_chunks,
                embeddings=all_embeddings,
                success=total_success and len(all_embeddings) == total_requests,
                latency_ms=latency,
            )
            return result

        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            self._health_checker.record_failure(str(e))
            return EmbeddingBatchResult(
                document_id=str(document.document_id),
                success=False,
                error=str(e),
                latency_ms=latency,
            )

    def process_documents(
        self,
        documents: list[KnowledgeDocument],
    ) -> list[EmbeddingBatchResult]:
        results: list[EmbeddingBatchResult] = []
        for doc in documents:
            result = self.process_document(doc)
            results.append(result)
        return results

    def reset_metrics(self) -> None:
        self._metrics.reset()

    def reset_statistics(self) -> None:
        self._statistics.reset()
