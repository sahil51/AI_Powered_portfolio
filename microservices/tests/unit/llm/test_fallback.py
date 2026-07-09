import time

import pytest

from application.ai.exceptions import ProviderUnavailableError
from application.ai.models import CompletionResponse
from infrastructure.llm.fallback import FallbackStrategy


class TestFallbackStrategy:
    def setup_method(self):
        self.circuit_state: dict[str, dict] = {}
        self.strategy = FallbackStrategy(
            fallback_models=["cerebras/model", "nvidia/model"],
            circuit_breaker_state=self.circuit_state,
            circuit_breaker_threshold=3,
            circuit_breaker_reset=60,
        )

    async def _success_fn(self, **kwargs):
        return CompletionResponse(content="success", model=kwargs.get("model", ""))

    async def test_execute_with_fallback_primary_success(self):
        result = await self.strategy.execute_with_fallback("primary", self._success_fn)
        assert result.content == "success"

    async def test_execute_with_fallback_fallback_success(self):
        call_order = []

        async def alternate(model=None, **kwargs):
            call_order.append(model)
            if model == "primary":
                raise TimeoutError("primary failed")
            return CompletionResponse(content=f"from {model}", model=model)

        result = await self.strategy.execute_with_fallback("primary", alternate)
        assert "from cerebras" in result.content
        assert call_order == ["primary", "cerebras/model"]

    async def test_execute_all_exhausted(self):
        async def always_fail(model=None, **kwargs):
            raise TimeoutError("always fails")

        with pytest.raises(ProviderUnavailableError, match="All models"):
            await self.strategy.execute_with_fallback("primary", always_fail)

    async def test_circuit_breaker_skips_open_model(self):
        self.circuit_state["primary"] = {"failures": 5, "last_failure": time.time()}

        result = await self.strategy.execute_with_fallback("primary", self._success_fn)
        assert "cerebras" in result.model.lower()

    async def test_circuit_breaker_recovers_after_reset(self):
        self.circuit_state["primary"] = {"failures": 5, "last_failure": time.time() - 120}

        result = await self.strategy.execute_with_fallback("primary", self._success_fn)
        assert result.content == "success"

    async def test_non_retryable_error_propagates(self):
        async def fail_hard(model=None, **kwargs):
            raise ValueError("non-retryable")

        with pytest.raises(ValueError):
            await self.strategy.execute_with_fallback("primary", fail_hard)

    def test_record_success_resets_failures(self):
        self.circuit_state["primary"] = {"failures": 4, "last_failure": 0.0}
        self.strategy._record_success("primary")
        assert self.circuit_state["primary"]["failures"] == 0
