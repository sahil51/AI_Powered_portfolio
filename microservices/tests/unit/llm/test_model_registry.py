from infrastructure.llm.model_registry import ModelDefinition, ModelRegistry


class TestModelDefinition:
    def test_to_model_info(self):
        definition = ModelDefinition(
            id="test-model",
            provider="test",
            display_name="Test Model",
            max_context_length=16384,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_vision=False,
            priority=0,
        )
        info = definition.to_model_info()
        assert info.id == "test-model"
        assert info.provider == "test"
        assert info.display_name == "Test Model"
        assert info.capabilities.max_context_length == 16384
        assert info.capabilities.max_output_tokens == 4096
        assert info.capabilities.supports_streaming
        assert not info.capabilities.supports_vision
        assert info.priority == 0
        assert info.healthy


class TestModelRegistry:
    def setup_method(self):
        self.registry = ModelRegistry()

    def test_register_and_get(self):
        definition = ModelDefinition(id="model-1", provider="test")
        self.registry.register(definition)
        assert self.registry.get("model-1") is definition

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_register_many(self):
        definitions = [
            ModelDefinition(id="m1", provider="test"),
            ModelDefinition(id="m2", provider="test"),
        ]
        self.registry.register_many(definitions)
        assert self.registry.count == 2

    def test_list_models(self):
        self.registry.register(ModelDefinition(id="m1", provider="test"))
        self.registry.register(ModelDefinition(id="m2", provider="test"))
        models = self.registry.list_models()
        assert len(models) == 2
        assert {m.id for m in models} == {"m1", "m2"}

    def test_list_ids(self):
        self.registry.register(ModelDefinition(id="m1", provider="test"))
        self.registry.register(ModelDefinition(id="m2", provider="test"))
        ids = self.registry.list_ids()
        assert set(ids) == {"m1", "m2"}

    def test_supports(self):
        definition = ModelDefinition(
            id="m1",
            provider="test",
            supports_streaming=True,
            supports_vision=False,
        )
        self.registry.register(definition)
        assert self.registry.supports("m1", "streaming")
        assert not self.registry.supports("m1", "vision")
        assert not self.registry.supports("nonexistent", "streaming")

    def test_clear(self):
        self.registry.register(ModelDefinition(id="m1", provider="test"))
        self.registry.clear()
        assert self.registry.count == 0
