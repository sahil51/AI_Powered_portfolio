from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from application.ai.models import CompletionResponse, Usage

logger = logging.getLogger("ai_assistant")


@dataclass
class ProviderMetrics:
    provider: str = ""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    retry_count: int = 0
    fallback_count: int = 0
    circuit_breaker_trips: int = 0
    last_request_time: float = 0.0
    model_usage: dict[str, "ModelMetrics"] = field(default_factory=dict)

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    def merge(self, other: "ProviderMetrics") -> None:
        self.total_requests += other.total_requests
        self.successful_requests += other.successful_requests
        self.failed_requests += other.failed_requests
        self.total_tokens += other.total_tokens
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_cost += other.total_cost
        self.total_latency_ms += other.total_latency_ms
        self.retry_count += other.retry_count
        self.fallback_count += other.fallback_count
        self.circuit_breaker_trips += other.circuit_breaker_trips
        if other.last_request_time > self.last_request_time:
            self.last_request_time = other.last_request_time
        for model, metrics in other.model_usage.items():
            if model in self.model_usage:
                self.model_usage[model].merge(metrics)
            else:
                self.model_usage[model] = metrics


@dataclass
class ModelMetrics:
    model: str = ""
    requests: int = 0
    tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    errors: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.latency_ms / self.requests

    def merge(self, other: "ModelMetrics") -> None:
        self.requests += other.requests
        self.tokens += other.tokens
        self.cost += other.cost
        self.latency_ms += other.latency_ms
        self.errors += other.errors


class ProviderMetricsCollector:
    def __init__(self) -> None:
        self._metrics: dict[str, ProviderMetrics] = {}

    def record_request(
        self,
        provider: str,
        model: str,
        success: bool,
        latency_ms: float,
        usage: Usage | None = None,
    ) -> None:
        if provider not in self._metrics:
            self._metrics[provider] = ProviderMetrics(provider=provider)
        metrics = self._metrics[provider]
        metrics.total_requests += 1
        metrics.last_request_time = time.time()
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        metrics.total_latency_ms += latency_ms
        if usage:
            metrics.total_tokens += usage.total_tokens
            metrics.prompt_tokens += usage.prompt_tokens
            metrics.completion_tokens += usage.completion_tokens
            metrics.total_cost += usage.cost
        if model not in metrics.model_usage:
            metrics.model_usage[model] = ModelMetrics(model=model)
        model_metrics = metrics.model_usage[model]
        model_metrics.requests += 1
        model_metrics.latency_ms += latency_ms
        if not success:
            model_metrics.errors += 1
        if usage:
            model_metrics.tokens += usage.total_tokens
            model_metrics.cost += usage.cost

    def record_retry(self, provider: str) -> None:
        if provider not in self._metrics:
            self._metrics[provider] = ProviderMetrics(provider=provider)
        self._metrics[provider].retry_count += 1

    def record_fallback(self, provider: str) -> None:
        if provider not in self._metrics:
            self._metrics[provider] = ProviderMetrics(provider=provider)
        self._metrics[provider].fallback_count += 1

    def record_circuit_breaker_trip(self, provider: str) -> None:
        if provider not in self._metrics:
            self._metrics[provider] = ProviderMetrics(provider=provider)
        self._metrics[provider].circuit_breaker_trips += 1

    def get_metrics(self, provider: str | None = None) -> ProviderMetrics | dict[str, ProviderMetrics]:
        if provider:
            return self._metrics.get(provider, ProviderMetrics(provider=provider))
        return dict(self._metrics)

    def reset(self, provider: str | None = None) -> None:
        if provider:
            self._metrics.pop(provider, None)
        else:
            self._metrics.clear()

    def wrap(self, provider: str, model: str, fn: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await fn(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                usage = None
                if isinstance(result, CompletionResponse):
                    usage = result.usage
                self.record_request(provider, model, True, elapsed, usage)
                return result
            except Exception:
                elapsed = (time.time() - start) * 1000
                self.record_request(provider, model, False, elapsed)
                raise

        return wrapper
