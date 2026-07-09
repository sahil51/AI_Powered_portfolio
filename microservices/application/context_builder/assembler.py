from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextAssembler, ContextLayer


class ContextAssemblerImpl(ContextAssembler):
    def __init__(self) -> None:
        self._layers: dict[str, ContextLayer] = {}

    async def assemble(self, layers: list[ContextLayer], **kwargs: Any) -> dict[str, Any]:
        assembled: dict[str, Any] = {}
        for layer in layers:
            if not layer.is_enabled():
                continue
            try:
                data = await layer.build(**kwargs)
                assembled[layer.name] = data
            except Exception:
                assembled[layer.name] = {"error": f"Failed to build layer: {layer.name}"}
        return assembled

    def add_layer(self, layer: ContextLayer) -> None:
        self._layers[layer.name] = layer

    def remove_layer(self, name: str) -> None:
        self._layers.pop(name, None)

    def get_layer(self, name: str) -> ContextLayer | None:
        return self._layers.get(name)

    def list_layers(self) -> list[ContextLayer]:
        return list(self._layers.values())
