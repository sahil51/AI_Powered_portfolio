import pytest

from application.ai.manager import ProviderManager
from application.ai.models import CompletionRequest
from application.ai.registry import ProviderRegistry
from tests.unit.llm.test_provider_registry import StubProvider


class TestProviderManager:
    def setup_method(self):
        self.registry = ProviderRegistry()
        self.provider = StubProvider("test")
        self.registry.register(self.provider)
        self.manager = ProviderManager(self.registry)

    async def test_generate(self):
        response = await self.manager.generate(CompletionRequest(messages=[{"role": "user", "content": "hi"}]))
        assert response.content == "stub response"

    async def test_generate_json(self):
        result = await self.manager.generate_json(CompletionRequest(system_prompt="test"))
        assert result == {"result": "stub"}

    async def test_count_tokens(self):
        count = await self.manager.count_tokens("hello world")
        assert count == 11

    async def test_health_check(self):
        healthy = await self.manager.health_check()
        assert healthy

    async def test_check_all_health(self):
        results = await self.manager.check_all_health()
        assert results == {"test": True}

    def test_list_models(self):
        models = self.manager.list_models()
        assert len(models) == 1

    def test_get_default_model(self):
        model = self.manager.get_default_model()
        assert model == "stub-model"

    async def test_initialize_all(self):
        await self.manager.initialize_all()
        assert self.provider._initialized

    async def test_shutdown_all(self):
        await self.manager.initialize_all()
        await self.manager.shutdown_all()
        assert not self.provider._initialized

    async def test_resolve_raises_on_empty(self):
        empty_registry = ProviderRegistry()
        empty_manager = ProviderManager(empty_registry)
        with pytest.raises(Exception):
            await empty_manager.generate(CompletionRequest())
