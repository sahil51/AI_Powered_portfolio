from application.context_builder.models import BuiltContext, ContextLayerResult, ContextMetadata
from application.context_builder.serializer import ContextSerializer


class TestContextSerializer:
    def setup_method(self):
        self.serializer = ContextSerializer()
        self.context = BuiltContext(
            layers={
                "system": ContextLayerResult(name="system", data={"prompt": "hello"}, tokens=10),
                "memory": ContextLayerResult(name="memory", data={"items": []}, tokens=5),
            },
            layer_order=["system", "memory"],
            metadata=ContextMetadata(total_tokens=15, max_tokens=8192, layer_count=2),
        )

    def test_serialize_to_dict(self):
        result = self.serializer.serialize_to_dict(self.context)
        assert "metadata" in result
        assert result["metadata"]["total_tokens"] == 15
        assert result["system"] == {"prompt": "hello"}
        assert result["memory"] == {"items": []}

    def test_serialize_layer_data(self):
        result = self.serializer.serialize_layer_data(self.context, "system")
        assert result == {"prompt": "hello"}

    def test_serialize_layer_data_nonexistent(self):
        result = self.serializer.serialize_layer_data(self.context, "nonexistent")
        assert result == {}

    def test_estimate_tokens(self):
        tokens = self.serializer.estimate_tokens({"key": "value"})
        assert tokens > 0
