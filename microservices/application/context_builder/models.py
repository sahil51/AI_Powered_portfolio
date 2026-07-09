from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ContextLayerResult:
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    tokens: int = 0
    priority: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.data


@dataclass
class ContextMetadata:
    total_tokens: int = 0
    layer_count: int = 0
    enabled_layer_count: int = 0
    max_tokens: int = 0
    reserved_tokens: int = 0
    compression_ratio: float = 1.0
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    elapsed_ms: float = 0.0
    version: str = "1.0.0"

    @property
    def usage_percent(self) -> float:
        if self.max_tokens == 0:
            return 0.0
        return (self.total_tokens / self.max_tokens) * 100.0

    @property
    def has_remaining(self) -> bool:
        if self.max_tokens <= 0:
            return True
        return self.total_tokens < self.max_tokens


@dataclass
class BuiltContext:
    layers: dict[str, ContextLayerResult] = field(default_factory=dict)
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    layer_order: list[str] = field(default_factory=list)

    def get_layer(self, name: str) -> ContextLayerResult | None:
        return self.layers.get(name)

    def get_layer_data(self, name: str) -> dict[str, Any]:
        layer = self.layers.get(name)
        if layer is None:
            return {}
        return layer.data

    @property
    def enabled_layers(self) -> list[ContextLayerResult]:
        return [layer for layer in self.layers.values() if layer.enabled]

    @property
    def token_breakdown(self) -> dict[str, int]:
        return {name: layer.tokens for name, layer in self.layers.items()}

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers": {
                name: {
                    "data": layer.data,
                    "tokens": layer.tokens,
                    "enabled": layer.enabled,
                }
                for name, layer in self.layers.items()
            },
            "layer_order": list(self.layer_order),
            "metadata": {
                "total_tokens": self.metadata.total_tokens,
                "layer_count": self.metadata.layer_count,
                "max_tokens": self.metadata.max_tokens,
                "usage_percent": self.metadata.usage_percent,
            },
        }
