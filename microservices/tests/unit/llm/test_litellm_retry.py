import pytest
from litellm.exceptions import RateLimitError

from infrastructure.llm.lite_llm_retry import LiteLLMRetryPolicy


class TestLiteLLMRetryPolicy:
    def setup_method(self):
        self.policy = LiteLLMRetryPolicy(max_retries=3, base_delay=0.01, max_delay=1.0)

    def test_max_retries(self):
        assert self.policy.max_retries == 3

    def test_is_retryable_rate_limit(self):
        assert self.policy.is_retryable(RateLimitError("rate limited", "test", 429))

    def test_is_retryable_timeout(self):
        assert self.policy.is_retryable(TimeoutError())

    def test_is_not_retryable_arbitrary(self):
        assert not self.policy.is_retryable(ValueError("not retryable"))

    def test_get_delay_increases(self):
        delay_0 = self.policy.get_delay(0)
        delay_1 = self.policy.get_delay(1)
        delay_2 = self.policy.get_delay(2)
        assert delay_0 < delay_1
        assert delay_1 < delay_2

    def test_get_delay_capped(self):
        policy = LiteLLMRetryPolicy(max_retries=5, base_delay=10.0, max_delay=5.0)
        delay = policy.get_delay(10)
        assert delay <= 5.0

    async def test_execute_with_retry_success(self):
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await self.policy.execute_with_retry(succeed)
        assert call_count == 1
        assert result == "success"

    async def test_execute_with_retry_eventually_succeeds(self):
        call_count = 0

        async def eventually_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timeout")
            return "success"

        result = await self.policy.execute_with_retry(eventually_succeed)
        assert call_count == 3
        assert result == "success"

    async def test_execute_with_retry_exhausted(self):
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("always fails")

        with pytest.raises(TimeoutError):
            await self.policy.execute_with_retry(always_fail)
        assert call_count == 3

    async def test_execute_with_retry_non_retryable(self):
        async def fail():
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            await self.policy.execute_with_retry(fail)

    def test_from_settings(self):
        policy = LiteLLMRetryPolicy.from_settings()
        assert policy.max_retries > 0
