
from application.context_builder.factory import ContextFactory
from application.context_builder.models import BuiltContext


class TestContextBuilder:
    def test_create_default(self):
        builder = ContextFactory.create_default_builder()
        assert builder is not None
        assert builder.budget.max_tokens == 8192

    def test_register_default_layers(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        assert len(builder._layers) == 7

    async def test_build_with_default_layers(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        context = await builder.build()
        assert isinstance(context, BuiltContext)
        assert "system" in context.layers
        assert "identity" in context.layers
        assert "conversation" in context.layers
        assert "memory" in context.layers

    async def test_build_returns_structure(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        context = await builder.build(user_id="test-user")
        assert context.metadata.total_tokens >= 0
        assert context.metadata.layer_count > 0

    def test_add_layer(self):
        builder = ContextFactory.create_default_builder()
        from application.context_builder.layers.system import SystemContextLayer
        layer = SystemContextLayer(system_prompt="custom")
        builder.add_layer(layer)
        assert layer.name in [x.name for x in builder._layers]

    def test_remove_layer(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        builder.remove_layer("system")
        assert "system" not in [x.name for x in builder._layers]

    def test_enable_disable_layer(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        builder.disable_layer("memory")
        builder.enable_layer("memory")

    def test_get_layer(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        layer = builder.get_layer("system")
        assert layer is not None
        assert layer.name == "system"

    async def test_build_with_kwargs(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        context = await builder.build(user_id="user-1", session_id="sess-1")
        identity = context.get_layer_data("identity")
        assert identity.get("user_id") == "user-1"

    async def test_metrics_recorded(self):
        builder = ContextFactory.create_default_builder()
        builder.register_default_layers()
        await builder.build()
        assert builder.metrics.total_builds == 1

    def test_custom_budget(self):
        builder = ContextFactory.create_builder(max_tokens=4096)
        assert builder.budget.max_tokens == 4096
