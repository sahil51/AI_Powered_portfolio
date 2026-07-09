from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestionMetrics:
    total_imports: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    total_chunks_created: int = 0
    total_bytes_processed: int = 0
    total_latency_ms: float = 0.0
    imports_by_source: dict[str, int] = field(default_factory=dict)
    failures_by_error: dict[str, int] = field(default_factory=dict)
    last_import_time: float = 0.0
    peak_latency_ms: float = 0.0


class KnowledgeImportMetricsCollector:
    def __init__(self) -> None:
        self._metrics = IngestionMetrics()

    def record_import(
        self,
        source_type: str,
        doc_type: str,
        latency_ms: float,
        chunk_count: int,
        bytes_processed: int,
    ) -> None:
        self._metrics.total_imports += 1
        self._metrics.successful_imports += 1
        self._metrics.total_chunks_created += chunk_count
        self._metrics.total_bytes_processed += bytes_processed
        self._metrics.total_latency_ms += latency_ms
        self._metrics.last_import_time = time.time()
        self._metrics.peak_latency_ms = max(self._metrics.peak_latency_ms, latency_ms)

        src_key = f"{source_type}:{doc_type}"
        self._metrics.imports_by_source[src_key] = self._metrics.imports_by_source.get(src_key, 0) + 1

    def record_failure(self, source_type: str, error: str) -> None:
        self._metrics.total_imports += 1
        self._metrics.failed_imports += 1
        self._metrics.last_import_time = time.time()
        error_key = error[:100] if error else "unknown"
        self._metrics.failures_by_error[error_key] = self._metrics.failures_by_error.get(error_key, 0) + 1

    def reset(self) -> None:
        self._metrics = IngestionMetrics()

    def get_metrics(self) -> dict[str, Any]:
        m = self._metrics
        return {
            "total_imports": m.total_imports,
            "successful_imports": m.successful_imports,
            "failed_imports": m.failed_imports,
            "total_chunks_created": m.total_chunks_created,
            "total_bytes_processed": m.total_bytes_processed,
            "average_latency_ms": m.total_latency_ms / max(m.total_imports, 1),
            "peak_latency_ms": m.peak_latency_ms,
            "imports_by_source": dict(m.imports_by_source),
            "failures_by_error": dict(m.failures_by_error),
            "last_import_time": m.last_import_time,
        }

    @property
    def metrics(self) -> IngestionMetrics:
        return self._metrics
