import pytest

from application.ai.exceptions import ProviderConfigurationError
from application.ai.models import CompletionRequest, CompletionResponse, ModelInfo, ProviderInfo, Usage
from application.ai.registry import ProviderFactory, ProviderRegistry


class StubProvider:
    def __init__(self, name: str = "stub") -> None:
        self._name = name
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(content="stub response", model="stub")

    async def generate_json(self, request: CompletionRequest) -> dict:
        return {"result": "stub"}

    async def stream(self, request: CompletionRequest):
        yield None

    async def count_tokens(self, text: str, model: str | None = None) -> int:
        return len(text)

    async def estimate_tokens(self, text: str) -> int:
        return len(text) // 4 + 1

    async def health_check(self) -> bool:
        return True

    def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="stub-model", provider=self._name)]

    def get_default_model(self) -> str:
        return "stub-model"

    def get_model(self, model_id: str) -> ModelInfo | None:
        if model_id == "stub-model":
            return ModelInfo(id="stub-model", provider=self._name)
        return None

    def supports(self, capability) -> bool:
        return True

    async def estimate_cost(self, model: str, usage: Usage) -> float:
        return 0.0

    async def get_provider_info(self) -> ProviderInfo:
        return ProviderInfo(name=self._name, healthy=True)


class TestProviderRegistry:
    def test_register_and_get(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        assert registry.get("test") is provider
        assert registry.default == "test"

    def test_register_makes_default(self):
        registry = ProviderRegistry()
        p1 = StubProvider("p1")
        p2 = StubProvider("p2")
        registry.register(p1, make_default=True)
        registry.register(p2)
        assert registry.default == "p1"

    def test_get_default(self):
        registry = ProviderRegistry()
        provider = StubProvider("default")
        registry.register(provider)
        assert registry.get() is provider

    def test_get_nonexistent_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(ProviderConfigurationError):
            registry.get("nonexistent")

    def test_get_empty_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(ProviderConfigurationError):
            registry.get()

    def test_list_providers(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        infos = registry.list_providers()
        assert len(infos) == 1
        assert infos[0].name == "test"

    def test_list_models(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        models = registry.list_models()
        assert len(models) == 1
        assert models[0].id == "stub-model"

    def test_available(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        assert registry.available == ["test"]

    def test_unregister(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        registry.unregister("test")
        assert "test" not in registry.available

    def test_clear(self):
        registry = ProviderRegistry()
        registry.register(StubProvider("test"))
        registry.clear()
        assert registry.available == []
        assert registry.default is None

    def test_resolve_with_capability(self):
        registry = ProviderRegistry()
        provider = StubProvider("test")
        registry.register(provider)
        resolved = registry.resolve(capability="completion")
        assert resolved is provider


class TestProviderFactory:
    def test_create_and_register(self):
        registry = ProviderRegistry()

        def factory(config):
            return StubProvider("factory-provider")

        registry.register_factory("factory", factory)
        pf = ProviderFactory(registry)
        provider = pf.create("factory")
        assert provider.name == "factory-provider"
        assert registry.get("factory") is provider
