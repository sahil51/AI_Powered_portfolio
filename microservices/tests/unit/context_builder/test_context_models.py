
from application.context_builder.models import BuiltContext, ContextLayerResult, ContextMetadata


class TestContextLayerResult:
    def test_defaults(self):
        result = ContextLayerResult(name="test")
        assert result.name == "test"
        assert result.data == {}
        assert result.tokens == 0
        assert result.enabled
        assert result.is_empty

    def test_not_empty(self):
        result = ContextLayerResult(name="test", data={"key": "value"})
        assert not result.is_empty


class TestContextMetadata:
    def test_defaults(self):
        meta = ContextMetadata()
        assert meta.total_tokens == 0
        assert meta.layer_count == 0
        assert meta.usage_percent == 0.0
        assert meta.has_remaining

    def test_usage_percent(self):
        meta = ContextMetadata(total_tokens=4096, max_tokens=8192)
        assert meta.usage_percent == 50.0

    def test_has_remaining_false(self):
        meta = ContextMetadata(total_tokens=8192, max_tokens=8192)
        assert not meta.has_remaining


class TestBuiltContext:
    def test_defaults(self):
        ctx = BuiltContext()
        assert ctx.layers == {}
        assert ctx.layer_order == []

    def test_get_layer(self):
        layer = ContextLayerResult(name="system", data={"prompt": "hello"})
        ctx = BuiltContext(layers={"system": layer})
        assert ctx.get_layer("system") is layer
        assert ctx.get_layer("nonexistent") is None

    def test_get_layer_data(self):
        layer = ContextLayerResult(name="system", data={"prompt": "hello"})
        ctx = BuiltContext(layers={"system": layer})
        assert ctx.get_layer_data("system") == {"prompt": "hello"}
        assert ctx.get_layer_data("nonexistent") == {}

    def test_enabled_layers(self):
        l1 = ContextLayerResult(name="l1", enabled=True)
        l2 = ContextLayerResult(name="l2", enabled=False)
        ctx = BuiltContext(layers={"l1": l1, "l2": l2})
        enabled = ctx.enabled_layers
        assert len(enabled) == 1
        assert enabled[0].name == "l1"

    def test_token_breakdown(self):
        l1 = ContextLayerResult(name="system", tokens=100)
        l2 = ContextLayerResult(name="memory", tokens=200)
        ctx = BuiltContext(layers={"system": l1, "memory": l2})
        breakdown = ctx.token_breakdown
        assert breakdown == {"system": 100, "memory": 200}

    def test_to_dict(self):
        layer = ContextLayerResult(name="system", data={"prompt": "hello"}, tokens=50)
        ctx = BuiltContext(
            layers={"system": layer},
            layer_order=["system"],
            metadata=ContextMetadata(total_tokens=50, max_tokens=8192),
        )
        d = ctx.to_dict()
        assert "layers" in d
        assert "layer_order" in d
        assert d["metadata"]["total_tokens"] == 50
