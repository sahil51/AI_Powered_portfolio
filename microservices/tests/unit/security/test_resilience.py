import asyncio

import pytest

from security.circuit_breaker_registry import CircuitBreakerRegistry
from security.resilience_manager import ResilienceManager
from security.retry_policy_registry import RetryPolicyRegistry


class TestResilienceManager:
    @pytest.fixture
    def manager(self):
        cb_registry = CircuitBreakerRegistry()
        retry_registry = RetryPolicyRegistry()
        retry_registry.register_defaults()
        return ResilienceManager(cb_registry, retry_registry)

    def test_register_bulkhead(self, manager):
        manager.register_bulkhead("test", max_concurrent=5)
        report = manager.get_resilience_report()
        assert "test" in report["bulkheads"]

    def test_register_timeout(self, manager):
        manager.register_timeout("test", timeout_seconds=10.0)
        report = manager.get_resilience_report()
        assert "test" in report["timeouts"]

    @pytest.mark.asyncio
    async def test_execute_success(self, manager):
        async def success():
            return "ok"

        result = await manager.execute_with_resilience("test", success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_with_fallback(self, manager):
        async def fail():
            raise ValueError("fail")

        async def fallback():
            return "fallback"

        manager.register_fallback("test", fallback_func=fallback)

        manager.circuit_breaker_registry.register("test", failure_threshold=1)
        with pytest.raises(ValueError):
            await manager.execute_with_resilience("test", fail)

        result = await manager.execute_with_resilience("test", fail)
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_execute_circuit_breaker_open(self, manager):
        async def fail():
            raise ValueError("fail")

        manager.circuit_breaker_registry.register("test", failure_threshold=1, reset_timeout_seconds=60.0)
        with pytest.raises(ValueError):
            await manager.execute_with_resilience("test", fail)

        with pytest.raises(RuntimeError):
            await manager.execute_with_resilience("test", fail)

    @pytest.mark.asyncio
    async def test_execute_with_retry_policy(self, manager):
        call_count = 0

        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retry")
            return "ok"

        result = await manager.execute_with_resilience("test", eventually_succeeds)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, manager):
        async def slow():
            await asyncio.sleep(10)
            return "ok"

        manager.register_timeout("test", timeout_seconds=0.05)
        cb = manager.circuit_breaker_registry
        cb.register("test", failure_threshold=3)

        with pytest.raises(asyncio.TimeoutError):
            await manager.execute_with_resilience("test", slow)

    def test_resilience_report(self, manager):
        report = manager.get_resilience_report()
        assert "circuit_breakers" in report
        assert "bulkheads" in report
        assert "timeouts" in report

    def test_reset(self, manager):
        manager.register_bulkhead("bh")
        manager.register_timeout("to")
        manager.reset()
        report = manager.get_resilience_report()
        assert len(report["bulkheads"]) == 0
        assert len(report["timeouts"]) == 0
