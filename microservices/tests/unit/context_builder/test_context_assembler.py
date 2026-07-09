
from application.context_builder.assembler import ContextAssemblerImpl
from application.context_builder.layers.system import SystemContextLayer


class TestContextAssemblerImpl:
    def test_add_and_get_layer(self):
        assembler = ContextAssemblerImpl()
        layer = SystemContextLayer(system_prompt="test")
        assembler.add_layer(layer)
        assert assembler.get_layer("system") is layer

    def test_remove_layer(self):
        assembler = ContextAssemblerImpl()
        layer = SystemContextLayer()
        assembler.add_layer(layer)
        assembler.remove_layer("system")
        assert assembler.get_layer("system") is None

    def test_list_layers(self):
        assembler = ContextAssemblerImpl()
        assembler.add_layer(SystemContextLayer())
        assert len(assembler.list_layers()) == 1

    async def test_assemble_empty(self):
        assembler = ContextAssemblerImpl()
        result = await assembler.assemble([])
        assert result == {}

    async def test_assemble_skips_disabled(self):
        assembler = ContextAssemblerImpl()
        layer = SystemContextLayer(enabled=False)
        assembler.add_layer(layer)
        result = await assembler.assemble([layer])
        assert "system" not in result

    async def test_assemble_handles_error(self):
        class BrokenLayer(SystemContextLayer):
            async def build(self, **kwargs):
                raise RuntimeError("broken")

        assembler = ContextAssemblerImpl()
        layer = BrokenLayer()
        result = await assembler.assemble([layer])
        assert "error" in result["system"]
