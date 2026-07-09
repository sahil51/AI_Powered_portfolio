from __future__ import annotations

import time
from typing import Any

from application.context_builder.interfaces import ContextLayer
from application.knowledge_context.assembler import KnowledgeContextAssemblerImpl
from application.knowledge_context.cache import KnowledgeContextCache
from application.knowledge_context.exceptions import KnowledgeContextError
from application.knowledge_context.health import KnowledgeContextHealthChecker
from application.knowledge_context.interfaces import KnowledgeContextAssembler, KnowledgeContextProvider
from application.knowledge_context.metrics import KnowledgeContextMetricsCollector
from application.knowledge_context.models import (
    KnowledgeContextConfig,
    KnowledgeContextResult,
)
from application.knowledge_context.policy import DEFAULT_KNOWLEDGE_CONTEXT_POLICY, KnowledgeContextPolicy
from application.knowledge_context.statistics import KnowledgeContextStatisticsCollector
from application.knowledge_context.validator import KnowledgeContextValidator


class KnowledgeContextBuilder(ContextLayer):
    def __init__(
        self,
        provider: KnowledgeContextProvider,
        assembler: KnowledgeContextAssembler | None = None,
        cache: KnowledgeContextCache | None = None,
        policy: KnowledgeContextPolicy | None = None,
        validator: KnowledgeContextValidator | None = None,
        metrics_collector: KnowledgeContextMetricsCollector | None = None,
        statistics_collector: KnowledgeContextStatisticsCollector | None = None,
        health_checker: KnowledgeContextHealthChecker | None = None,
    ) -> None:
        self._provider = provider
        self._assembler = assembler or KnowledgeContextAssemblerImpl()
        self._cache = cache
        self._policy = policy or DEFAULT_KNOWLEDGE_CONTEXT_POLICY
        self._validator = validator or KnowledgeContextValidator()
        self._metrics = metrics_collector or KnowledgeContextMetricsCollector()
        self._statistics = statistics_collector or KnowledgeContextStatisticsCollector()
        self._health = health_checker or KnowledgeContextHealthChecker()
        self._config: KnowledgeContextConfig = self._policy.to_config()

    @property
    def name(self) -> str:
        return "knowledge"

    @property
    def priority(self) -> int:
        return 5

    def is_enabled(self) -> bool:
        return True

    def get_config(self) -> Any:
        return self._config

    def update_policy(self, policy: KnowledgeContextPolicy) -> None:
        self._policy = policy
        self._config = policy.to_config()

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        start = time.monotonic()
        query = kwargs.get("query", "")
        correlation_id = kwargs.get("correlation_id", "")

        try:
            self._validator.validate_query(query)
            self._validator.validate_config(self._config)

            budget = self._policy.create_budget(
                total_tokens=kwargs.get("total_tokens", 8192),
                conversation_tokens=kwargs.get("conversation_tokens", 2048),
                memory_tokens=kwargs.get("memory_tokens", 1024),
                reserved_tokens=kwargs.get("reserved_tokens", 1024),
            )

            result = await self._retrieve_knowledge(query, correlation_id)
            if result is None:
                return self._empty_result()

            assembled = await self._assembler.assemble(result, budget, self._config)

            self._metrics.record_retrieval(
                chunks_retrieved=result.total_chunks,
                latency_ms=result.retrieval_latency_ms,
                cache_hit=result.cache_hit,
            )
            self._metrics.record_tokens(assembled.tokens_used)
            if assembled.metadata.get("compression_ratio", 1.0) < 1.0:
                saved = assembled.metadata.get("total_available", 0) - assembled.tokens_used
                self._metrics.record_compression(max(0, saved))

            self._statistics.record_request(
                success=True,
                chunks_served=len(assembled.chunks),
                tokens_served=assembled.tokens_used,
                latency_ms=(time.monotonic() - start) * 1000,
                truncated=assembled.truncated,
            )

            for chunk in assembled.chunks:
                self._statistics.record_knowledge_coverage(chunk.document_type)

            self._health.record_success()

            return {
                "context": assembled.text,
                "chunks": assembled.chunks,
                "tokens_used": assembled.tokens_used,
                "total_available": assembled.total_available,
                "truncated": assembled.truncated,
                "metadata": {
                    **assembled.metadata,
                    "elapsed_ms": (time.monotonic() - start) * 1000,
                    "cache_hit": result.cache_hit,
                    "correlation_id": correlation_id,
                },
            }

        except KnowledgeContextError as e:
            self._health.record_failure(str(e))
            self._statistics.record_request(success=False)
            self._statistics.record_error(type(e).__name__)
            return self._error_result(str(e))

        except Exception as e:
            self._health.record_failure(str(e))
            self._statistics.record_request(success=False)
            self._statistics.record_error("UnexpectedError")
            return self._error_result(f"Knowledge context build failed: {e}")

    async def _retrieve_knowledge(
        self,
        query: str,
        correlation_id: str,
    ) -> KnowledgeContextResult | None:
        config_hash = str(hash((
            self._config.max_knowledge_tokens,
            self._config.max_retrieved_chunks,
            self._config.chunk_selection.value,
        )))

        if self._cache:
            cached = await self._cache.get_retrieval_result(query, config_hash)
            if cached is not None:
                cached.cache_hit = True
                return cached

        result = await self._provider.retrieve(query, self._config, correlation_id)

        if self._cache and result.chunks:
            await self._cache.cache_retrieval_result(query, config_hash, result)

        return result

    def _empty_result(self) -> dict[str, Any]:
        return {
            "context": "",
            "chunks": [],
            "tokens_used": 0,
            "total_available": self._config.max_knowledge_tokens,
            "truncated": False,
            "metadata": {
                "total_chunks": 0,
                "total_tokens": 0,
                "elapsed_ms": 0,
            },
        }

    def _error_result(self, error: str) -> dict[str, Any]:
        return {
            "context": "",
            "chunks": [],
            "tokens_used": 0,
            "total_available": 0,
            "truncated": False,
            "error": error,
            "metadata": {"error": error},
        }

    def health_check(self) -> dict[str, Any]:
        return self._health.check()

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics.get_metrics()

    def get_statistics(self) -> Any:
        return self._statistics.get_statistics()

    def reset_metrics(self) -> None:
        self._metrics.reset()

    def reset_statistics(self) -> None:
        self._statistics.reset()
