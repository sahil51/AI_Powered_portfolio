from __future__ import annotations

from dataclasses import dataclass, field

from application.embedding.models import EmbeddingProviderType


@dataclass
class EmbeddingStatistics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_chunks: int = 0
    total_tokens: int = 0
    requests_by_provider: dict[str, int] = field(default_factory=dict)
    requests_by_model: dict[str, int] = field(default_factory=dict)
    chunks_by_doc_type: dict[str, int] = field(default_factory=dict)
    avg_tokens_per_request: float = 0.0
    success_rate: float = 1.0


class EmbeddingStatisticsCollector:
    def __init__(self) -> None:
        self._stats = EmbeddingStatistics()

    @property
    def statistics(self) -> EmbeddingStatistics:
        return self._stats

    def record_request(
        self,
        provider: EmbeddingProviderType,
        model: str,
        success: bool,
    ) -> None:
        self._stats.total_requests += 1
        prov_key = provider.value
        self._stats.requests_by_provider[prov_key] = (
            self._stats.requests_by_provider.get(prov_key, 0) + 1
        )
        self._stats.requests_by_model[model] = (
            self._stats.requests_by_model.get(model, 0) + 1
        )
        if success:
            self._stats.successful_requests += 1
        else:
            self._stats.failed_requests += 1
        self._update_rates()

    def record_chunk(self, doc_type: str) -> None:
        self._stats.total_chunks += 1
        self._stats.chunks_by_doc_type[doc_type] = (
            self._stats.chunks_by_doc_type.get(doc_type, 0) + 1
        )

    def record_tokens(self, token_count: int) -> None:
        self._stats.total_tokens += token_count
        if self._stats.total_requests > 0:
            self._stats.avg_tokens_per_request = (
                self._stats.total_tokens / self._stats.total_requests
            )

    def _update_rates(self) -> None:
        if self._stats.total_requests > 0:
            self._stats.avg_tokens_per_request = (
                self._stats.total_tokens / self._stats.total_requests
            )
            self._stats.success_rate = (
                self._stats.successful_requests / self._stats.total_requests
            )

    def reset(self) -> None:
        self._stats = EmbeddingStatistics()
