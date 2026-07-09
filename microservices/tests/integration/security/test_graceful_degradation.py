import asyncio

import pytest

from security.circuit_breaker_registry import CircuitBreakerRegistry
from security.resilience_manager import ResilienceManager
from security.retry_policy_registry import RetryPolicyRegistry


class TestGracefulDegradationIntegration:
    @pytest.fixture
    def manager(self):
        cb = CircuitBreakerRegistry()
        retry = RetryPolicyRegistry()
        retry.register_defaults()
        mgr = ResilienceManager(cb, retry)
        return mgr

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, manager):
        async def primary():
            raise ConnectionError("Service unavailable")

        async def fallback():
            return "degraded response"

        manager.register_fallback("service-a", fallback_func=fallback)
        manager.circuit_breaker_registry.register("service-a", failure_threshold=1, reset_timeout_seconds=60)

        with pytest.raises(ConnectionError):
            await manager.execute_with_resilience("service-a", primary)

        result = await manager.execute_with_resilience("service-a", primary)
        assert result == "degraded response"

    @pytest.mark.asyncio
    async def test_degradation_on_circuit_open(self, manager):
        async def primary():
            return "full response"

        async def degraded():
            return "limited response"

        manager.register_degradation("service-b", degraded)
        manager.circuit_breaker_registry.register("service-b", failure_threshold=1, reset_timeout_seconds=60)

        await manager.execute_with_resilience("service-b", primary)

        async def fail():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await manager.execute_with_resilience("service-b", fail)

    @pytest.mark.asyncio
    async def test_bulkhead_isolation(self, manager):
        manager.register_bulkhead("limited-resource", max_concurrent=2)

        async def slow_task():
            await asyncio.sleep(0.5)
            return "done"

        tasks = [manager.execute_with_resilience("limited-resource", slow_task) for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successes = [r for r in results if r == "done"]
        assert len(successes) == 5

    @pytest.mark.asyncio
    async def test_timeout_graceful_degradation(self, manager):
        async def slow():
            await asyncio.sleep(10)
            return "slow"

        async def quick_fallback():
            return "quick fallback"

        manager.register_timeout("slow-service", timeout_seconds=0.05)
        manager.register_fallback("slow-service", fallback_func=quick_fallback)
        manager.circuit_breaker_registry.register("slow-service", failure_threshold=3)

        with pytest.raises(asyncio.TimeoutError):
            await manager.execute_with_resilience("slow-service", slow)

    @pytest.mark.asyncio
    async def test_retry_then_circuit_breaker(self, manager):
        call_count = [0]

        async def always_fails():
            call_count[0] += 1
            raise ValueError("failure")

        manager.circuit_breaker_registry.register("flaky-service", failure_threshold=3, reset_timeout_seconds=60)

        for _ in range(3):
            with pytest.raises(ValueError):
                await manager.execute_with_resilience("flaky-service", always_fails)

        state = manager.circuit_breaker_registry.get_state("flaky-service")
        assert state.value == "open"
