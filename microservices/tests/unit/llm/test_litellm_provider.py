import pytest

from application.ai.capability import ProviderCapability
from application.ai.exceptions import ProviderConfigurationError
from application.ai.models import CompletionRequest, Usage
from infrastructure.llm.lite_llm_config import LiteLLMConfiguration
from infrastructure.llm.lite_llm_provider import LiteLLMProvider


class TestLiteLLMProvider:
    def setup_method(self):
        config = LiteLLMConfiguration(
            primary_model="gemini/gemini-2.0-flash",
            fallback_models=["cerebras/gpt-oss-120b"],
            api_keys={"gemini": "test-key"},
        )
        self.provider = LiteLLMProvider(config=config)

    def test_name(self):
        assert self.provider.name == "litellm"

    async def test_not_initialized_raises(self):
        with pytest.raises(ProviderConfigurationError, match="not initialized"):
            await self.provider.generate(CompletionRequest(system_prompt="test"))

    async def test_initialize(self):
        await self.provider.initialize()
        assert self.provider._initialized

    async def test_get_default_model(self):
        await self.provider.initialize()
        assert self.provider.get_default_model() == "gemini/gemini-2.0-flash"

    async def test_list_models(self):
        await self.provider.initialize()
        models = self.provider.list_models()
        assert len(models) >= 1
        assert models[0].id == "gemini/gemini-2.0-flash"

    async def test_get_model_found(self):
        await self.provider.initialize()
        model = self.provider.get_model("gemini/gemini-2.0-flash")
        assert model is not None

    async def test_get_model_not_found(self):
        await self.provider.initialize()
        model = self.provider.get_model("nonexistent")
        assert model is None

    async def test_supports(self):
        await self.provider.initialize()
        assert self.provider.supports(ProviderCapability.COMPLETION)
        assert self.provider.supports(ProviderCapability.STREAMING)

    async def test_estimate_cost(self):
        usage = Usage(prompt_tokens=100, completion_tokens=50)
        cost = await self.provider.estimate_cost("gemini/gemini-2.0-flash", usage)
        assert cost >= 0

    async def test_get_provider_info(self):
        await self.provider.initialize()
        info = await self.provider.get_provider_info()
        assert info.name == "litellm"
        assert info.healthy
        assert len(info.models) > 0

    async def test_health_check(self):
        await self.provider.initialize()
        healthy = await self.provider.health_check()
        assert healthy

    async def test_count_tokens(self):
        count = await self.provider.count_tokens("hello world")
        assert count > 0

    async def test_estimate_tokens(self):
        count = await self.provider.estimate_tokens("hello world")
        assert count > 0

    async def test_generate_json_invalid(self):
        await self.provider.initialize()
        request = CompletionRequest(system_prompt="say hello", max_tokens=10)
        with pytest.raises(Exception):
            await self.provider.generate_json(request)

    async def test_shutdown(self):
        await self.provider.initialize()
        await self.provider.shutdown()
        assert not self.provider._initialized
