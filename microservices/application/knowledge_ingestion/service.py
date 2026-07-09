from __future__ import annotations

from typing import Any

from application.knowledge_ingestion.health import KnowledgeImportHealthChecker
from application.knowledge_ingestion.importer import KnowledgeImporter
from application.knowledge_ingestion.metrics import KnowledgeImportMetricsCollector
from application.knowledge_ingestion.models import (
    ImportSource,
    ImportStatisticsData,
    KnowledgeImportResult,
)
from application.knowledge_ingestion.statistics import KnowledgeImportStatisticsCollector
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from domain.knowledge.value_objects import DocumentType


class KnowledgeIngestionService:
    def __init__(
        self,
        importer: KnowledgeImporter,
        validator: KnowledgeImportValidator | None = None,
        metrics_collector: KnowledgeImportMetricsCollector | None = None,
        statistics_collector: KnowledgeImportStatisticsCollector | None = None,
        health_checker: KnowledgeImportHealthChecker | None = None,
    ) -> None:
        self._importer = importer
        self._validator = validator or KnowledgeImportValidator()
        self._metrics = metrics_collector or KnowledgeImportMetricsCollector()
        self._statistics = statistics_collector or KnowledgeImportStatisticsCollector()
        self._health = health_checker or KnowledgeImportHealthChecker()

    async def import_document(
        self,
        source: ImportSource,
        doc_type: DocumentType | None = None,
        correlation_id: str = "",
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> KnowledgeImportResult:
        start = __import__("time").monotonic()
        try:
            self._validator.validate_source(source)
            result = await self._importer.import_document(
                source=source,
                doc_type=doc_type,
                correlation_id=correlation_id,
                tags=tags,
                **kwargs,
            )
            latency = (__import__("time").monotonic() - start) * 1000
            result.latency_ms = latency

            if result.success:
                self._metrics.record_import(
                    source_type=source.source_type.value,
                    doc_type=doc_type.value if doc_type else "unknown",
                    latency_ms=latency,
                    chunk_count=result.chunk_count,
                    bytes_processed=source.size_bytes,
                )
                self._statistics.record_import(
                    source_type=source.source_type.value,
                    doc_type=doc_type.value if doc_type else "unknown",
                    success=True,
                )
                self._health.record_success()
            else:
                self._metrics.record_failure(
                    source_type=source.source_type.value,
                    error=result.error,
                )
                self._statistics.record_import(
                    source_type=source.source_type.value,
                    doc_type=doc_type.value if doc_type else "unknown",
                    success=False,
                )
                self._health.record_failure(result.error)

            return result

        except Exception as e:
            latency = (__import__("time").monotonic() - start) * 1000
            self._metrics.record_failure(
                source_type=source.source_type.value,
                error=str(e),
            )
            self._statistics.record_import(
                source_type=source.source_type.value,
                doc_type=doc_type.value if doc_type else "unknown",
                success=False,
            )
            self._health.record_failure(str(e))
            return KnowledgeImportResult(
                success=False,
                error=str(e),
                latency_ms=latency,
                correlation_id=correlation_id,
            )

    async def import_batch(
        self,
        sources: list[ImportSource],
        correlation_id: str = "",
        tags: list[str] | None = None,
    ) -> list[KnowledgeImportResult]:
        results: list[KnowledgeImportResult] = []
        for source in sources:
            result = await self.import_document(
                source=source,
                correlation_id=correlation_id,
                tags=tags,
            )
            results.append(result)
        return results

    def health_check(self) -> dict[str, Any]:
        return self._health.check()

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics.get_metrics()

    def get_statistics(self) -> ImportStatisticsData:
        return self._statistics.get_statistics()

    def reset_metrics(self) -> None:
        self._metrics.reset()

    def reset_statistics(self) -> None:
        self._statistics.reset()
