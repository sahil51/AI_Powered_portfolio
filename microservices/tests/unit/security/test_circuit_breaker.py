import time

import pytest

from security.circuit_breaker_registry import CircuitBreakerRegistry, CircuitState


class TestCircuitBreakerRegistry:
    @pytest.fixture
    def registry(self):
        return CircuitBreakerRegistry()

    def test_register(self, registry):
        breaker = registry.register("test", failure_threshold=3, reset_timeout_seconds=1.0)
        assert breaker.name == "test"
        assert breaker.state == CircuitState.CLOSED

    def test_get(self, registry):
        registry.register("test")
        breaker = registry.get("test")
        assert breaker is not None

    def test_get_nonexistent(self, registry):
        breaker = registry.get("nonexistent")
        assert breaker is None

    def test_is_available_closed(self, registry):
        registry.register("test")
        assert registry.is_available("test")

    def test_open_after_threshold(self, registry):
        registry.register("test", failure_threshold=3, reset_timeout_seconds=60.0)
        for _ in range(3):
            registry.record_failure("test")
        assert not registry.is_available("test")
        assert registry.get_state("test") == CircuitState.OPEN

    def test_half_open_after_timeout(self, registry):
        registry.register("test", failure_threshold=2, reset_timeout_seconds=0.1)
        for _ in range(2):
            registry.record_failure("test")
        assert not registry.is_available("test")
        time.sleep(0.15)
        assert registry.is_available("test")
        assert registry.get_state("test") == CircuitState.HALF_OPEN

    def test_half_open_success_closes(self, registry):
        registry.register("test", failure_threshold=2, reset_timeout_seconds=0.1)
        for _ in range(2):
            registry.record_failure("test")
        time.sleep(0.15)
        registry.is_available("test")
        for _ in range(3):
            registry.record_success("test")
        assert registry.get_state("test") == CircuitState.CLOSED

    def test_half_open_failure_reopens(self, registry):
        registry.register("test", failure_threshold=2, reset_timeout_seconds=0.1)
        for _ in range(2):
            registry.record_failure("test")
        time.sleep(0.15)
        registry.is_available("test")
        registry.record_failure("test")
        assert registry.get_state("test") == CircuitState.OPEN

    def test_record_success_closed(self, registry):
        registry.register("test")
        registry.record_failure("test")
        registry.record_success("test")
        assert registry.get("test").failure_count == 0

    def test_get_all_states(self, registry):
        registry.register("cb1")
        registry.register("cb2")
        states = registry.get_all_states()
        assert "cb1" in states
        assert "cb2" in states

    def test_reset(self, registry):
        registry.register("test", failure_threshold=1)
        registry.record_failure("test")
        assert not registry.is_available("test")
        registry.reset("test")
        assert registry.is_available("test")

    def test_reset_all(self, registry):
        registry.register("cb1", failure_threshold=1)
        registry.register("cb2", failure_threshold=1)
        registry.record_failure("cb1")
        registry.record_failure("cb2")
        registry.reset_all()
        assert registry.is_available("cb1")
        assert registry.is_available("cb2")

    def test_unregister(self, registry):
        registry.register("test")
        registry.unregister("test")
        assert registry.get("test") is None

    def test_get_or_create(self, registry):
        breaker = registry.get_or_create("auto")
        assert breaker is not None
        same = registry.get_or_create("auto")
        assert same is breaker
