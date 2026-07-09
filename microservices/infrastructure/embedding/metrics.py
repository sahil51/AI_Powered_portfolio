from __future__ import annotations

from application.embedding.metrics import EmbeddingMetrics, EmbeddingMetricsCollector
from application.embedding.models import EmbeddingProviderType


class EmbeddingInfraMetrics:
    def __init__(self) -> None:
        self._collector = EmbeddingMetricsCollector()

    def record_request(
        self,
        provider: EmbeddingProviderType,
        model: str,
        latency_ms: float,
        tokens_used: int = 0,
        success: bool = True,
        retry: bool = False,
    ) -> None:
        self._collector.record_request(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            success=success,
            retry=retry,
        )

    def record_chunk(self) -> None:
        self._collector.record_chunk_processed()

    def record_document(self) -> None:
        self._collector.record_document_processed()

    @property
    def metrics(self) -> EmbeddingMetrics:
        return self._collector.metrics

    def reset(self) -> None:
        self._collector.reset()
