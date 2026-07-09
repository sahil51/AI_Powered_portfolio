import pytest

from security.retry_policy_registry import BackoffStrategy, RetryPolicy, RetryPolicyRegistry


class TestRetryPolicyRegistry:
    @pytest.fixture
    def registry(self):
        r = RetryPolicyRegistry()
        r.register_defaults()
        return r

    def test_register(self, registry):
        policy = RetryPolicy(name="custom", max_retries=5)
        registry.register(policy)
        assert registry.get("custom") is policy

    def test_get_default(self, registry):
        policy = registry.get("default")
        assert policy is not None
        assert policy.max_retries == 3

    def test_get_or_default(self, registry):
        existing = registry.get_or_default("default")
        assert existing.max_retries == 3
        created = registry.get_or_default("new_policy")
        assert created.name == "new_policy"

    def test_calculate_fixed_delay(self, registry):
        policy = RetryPolicy(name="fixed", backoff_strategy=BackoffStrategy.FIXED, base_delay_seconds=2.0)
        assert registry.calculate_delay(policy, 0) == 2.0
        assert registry.calculate_delay(policy, 5) == 2.0

    def test_calculate_exponential_delay(self, registry):
        policy = RetryPolicy(name="exp", backoff_strategy=BackoffStrategy.EXPONENTIAL, base_delay_seconds=1.0)
        assert registry.calculate_delay(policy, 0) == 1.0
        assert registry.calculate_delay(policy, 1) == 2.0
        assert registry.calculate_delay(policy, 2) == 4.0

    def test_calculate_linear_delay(self, registry):
        policy = RetryPolicy(name="lin", backoff_strategy=BackoffStrategy.LINEAR, base_delay_seconds=1.0)
        assert registry.calculate_delay(policy, 0) == 1.0
        assert registry.calculate_delay(policy, 1) == 2.0

    def test_calculate_jitter_delay(self, registry):
        policy = RetryPolicy(name="jit", backoff_strategy=BackoffStrategy.JITTER, base_delay_seconds=1.0, jitter_factor=0.5)
        delay = registry.calculate_delay(policy, 1)
        assert delay >= 1.0
        assert delay <= 3.0

    def test_max_delay_cap(self, registry):
        policy = RetryPolicy(
            name="capped",
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            base_delay_seconds=10.0,
            max_delay_seconds=15.0,
        )
        delay = registry.calculate_delay(policy, 5)
        assert delay <= 15.0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, registry):
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await registry.execute_with_retry("default", "test", succeed)
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self, registry):
        call_count = 0

        async def fails_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary")
            return "ok"

        result = await registry.execute_with_retry("default", "test", fails_then_succeeds)
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self, registry):
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("persistent")

        with pytest.raises(ValueError):
            await registry.execute_with_retry("fast", "test", always_fails)
        assert call_count == 3

    def test_register_defaults(self):
        registry = RetryPolicyRegistry()
        registry.register_defaults()
        assert registry.get("default") is not None
        assert registry.get("fast") is not None
        assert registry.get("persistent") is not None
        assert registry.get("circuit_breaker_safe") is not None
