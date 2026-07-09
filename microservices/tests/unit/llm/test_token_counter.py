
from application.ai.models import Usage
from infrastructure.llm.token_counter import LiteLLMTokenCounter


class TestLiteLLMTokenCounter:
    def setup_method(self):
        self.counter = LiteLLMTokenCounter()

    async def test_estimate_tokens_empty(self):
        count = await self.counter.estimate_tokens("")
        assert count == 0

    async def test_estimate_tokens_short(self):
        count = await self.counter.estimate_tokens("hello world")
        assert count > 0

    def test_estimate_cost_gemini(self):
        usage = Usage(prompt_tokens=1000, completion_tokens=500)
        cost = self.counter.estimate_cost("gemini/gemini-2.0-flash", usage)
        assert cost > 0

    def test_estimate_cost_zero_usage(self):
        usage = Usage()
        cost = self.counter.estimate_cost("gemini/gemini-2.0-flash", usage)
        assert cost == 0

    async def test_count_tokens_fallback_to_estimate(self):
        count = await self.counter.count_tokens("Hello, world! How are you today?")
        assert count > 0
