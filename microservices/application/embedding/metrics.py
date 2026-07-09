from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.embedding.models import EmbeddingProviderType


@dataclass
class EmbeddingMetrics:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    total_chunks_processed: int = 0
    total_documents_processed: int = 0
    requests_by_provider: dict[str, int] = field(default_factory=dict)
    requests_by_model: dict[str, int] = field(default_factory=dict)
    retry_count: int = 0
    timeout_count: int = 0
    last_request_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingMetricsCollector:
    def __init__(self) -> None:
        self._metrics = EmbeddingMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> EmbeddingMetrics:
        return self._metrics

    def record_request(
        self,
        provider: EmbeddingProviderType,
        model: str,
        latency_ms: float,
        tokens_used: int = 0,
        success: bool = True,
        retry: bool = False,
    ) -> None:
        self._metrics.total_requests += 1

        prov_key = provider.value
        self._metrics.requests_by_provider[prov_key] = (
            self._metrics.requests_by_provider.get(prov_key, 0) + 1
        )

        self._metrics.requests_by_model[model] = (
            self._metrics.requests_by_model.get(model, 0) + 1
        )

        if success:
            self._metrics.successful += 1
        else:
            self._metrics.failed += 1

        if retry:
            self._metrics.retry_count += 1

        self._metrics.total_tokens += tokens_used
        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = (
            self._metrics.total_latency_ms / self._metrics.total_requests
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms
            if self._metrics.min_latency_ms == 0.0
            else min(self._metrics.min_latency_ms, latency_ms)
        )
        self._metrics.last_request_at = datetime.now(timezone.utc)

    def record_chunk_processed(self) -> None:
        self._metrics.total_chunks_processed += 1

    def record_document_processed(self) -> None:
        self._metrics.total_documents_processed += 1

    def reset(self) -> None:
        self._metrics = EmbeddingMetrics()
        self._start_time = time.time()
