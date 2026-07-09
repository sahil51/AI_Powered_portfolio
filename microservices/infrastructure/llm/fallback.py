from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError

logger = logging.getLogger("ai_assistant")

RETRYABLE_FOR_FALLBACK = (APIConnectionError, RateLimitError, InternalServerError, TimeoutError)


class FallbackStrategy:
    def __init__(
        self,
        fallback_models: list[str],
        circuit_breaker_state: dict[str, dict],
        metrics_collector: Any = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_reset: int = 60,
    ) -> None:
        self._fallback_models = fallback_models
        self._circuit_breaker_state = circuit_breaker_state
        self._metrics = metrics_collector
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_breaker_reset = circuit_breaker_reset

    async def execute_with_fallback(
        self,
        primary_model: str,
        request_fn: Callable[..., Any],
        on_fallback: Callable[[str], None] | None = None,
    ) -> CompletionResponse:
        models_to_try = [primary_model] + self._fallback_models

        for idx, model in enumerate(models_to_try):
            if self._is_circuit_open(model):
                logger.warning("Circuit breaker open for %s, skipping", model)
                if self._metrics:
                    self._metrics.record_circuit_breaker_trip("litellm")
                continue

            try:
                response = await self._try_model(model, request_fn)
                self._record_success(model)
                if idx > 0 and on_fallback:
                    on_fallback(model)
                return response
            except RETRYABLE_FOR_FALLBACK as e:
                self._record_failure(model)
                logger.warning("Model %s failed: %s, %s models remaining", model, e, len(models_to_try) - idx - 1)
                if self._metrics:
                    self._metrics.record_fallback("litellm")
            except Exception as e:
                logger.error("Non-retryable error with model %s: %s", model, e)
                raise

        from application.ai.exceptions import ProviderUnavailableError
        raise ProviderUnavailableError("All models in fallback chain exhausted")

    async def _try_model(self, model: str, request_fn: Callable[..., Any]) -> CompletionResponse:
        return await request_fn(model=model)

    def _is_circuit_open(self, model: str) -> bool:
        state = self._circuit_breaker_state.get(model)
        if not state:
            return False
        if state["failures"] >= self._circuit_breaker_threshold:
            if time.time() - state["last_failure"] > self._circuit_breaker_reset:
                state["failures"] = 0
                return False
            return True
        return False

    def _record_failure(self, model: str) -> None:
        state = self._circuit_breaker_state.setdefault(model, {"failures": 0, "last_failure": 0.0})
        state["failures"] += 1
        state["last_failure"] = time.time()

    def _record_success(self, model: str) -> None:
        state = self._circuit_breaker_state.get(model)
        if state:
            state["failures"] = 0
