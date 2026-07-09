from __future__ import annotations

from application.knowledge_ingestion.models import ImportStatisticsData


class KnowledgeImportStatisticsCollector:
    def __init__(self) -> None:
        self._stats = ImportStatisticsData()

    def record_import(
        self,
        source_type: str,
        doc_type: str,
        success: bool,
        chunk_count: int = 0,
        bytes_processed: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        self._stats.total_imports += 1
        if success:
            self._stats.successful_imports += 1
        else:
            self._stats.failed_imports += 1
        self._stats.total_chunks += chunk_count
        self._stats.total_bytes += bytes_processed
        self._stats.total_latency_ms += latency_ms
        self._stats.imports_by_source[source_type] = self._stats.imports_by_source.get(source_type, 0) + 1
        self._stats.imports_by_type[doc_type] = self._stats.imports_by_type.get(doc_type, 0) + 1

    def record_failure(self, error_type: str) -> None:
        self._stats.errors_by_type[error_type] = self._stats.errors_by_type.get(error_type, 0) + 1

    def get_statistics(self) -> ImportStatisticsData:
        return self._stats

    def reset(self) -> None:
        self._stats = ImportStatisticsData()
