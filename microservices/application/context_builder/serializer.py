from __future__ import annotations

from typing import Any

from application.context_builder.models import BuiltContext


class ContextSerializer:
    def __init__(self, token_counter: Any | None = None) -> None:
        self._token_counter = token_counter

    def serialize_to_dict(self, context: BuiltContext) -> dict[str, Any]:
        result: dict[str, Any] = {
            "metadata": {
                "total_tokens": context.metadata.total_tokens,
                "layer_count": context.metadata.layer_count,
                "enabled_layer_count": context.metadata.enabled_layer_count,
                "max_tokens": context.metadata.max_tokens,
                "usage_percent": context.metadata.usage_percent,
            }
        }
        for layer_name in context.layer_order:
            layer = context.layers.get(layer_name)
            if layer is None or not layer.enabled:
                continue
            result[layer_name] = layer.data
        return result

    def serialize_layer_data(self, context: BuiltContext, layer_name: str) -> dict[str, Any]:
        layer = context.layers.get(layer_name)
        if layer is None or not layer.enabled:
            return {}
        return layer.data

    def estimate_tokens(self, data: dict[str, Any]) -> int:
        if self._token_counter is None:
            return len(str(data)) // 4
        import json
        try:
            text = json.dumps(data, default=str)
        except (TypeError, ValueError):
            text = str(data)
        return self._token_counter(text)
