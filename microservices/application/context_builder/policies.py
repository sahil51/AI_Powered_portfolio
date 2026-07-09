from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderingDirection(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass
class LayerOrderingPolicy:
    order: list[str] = field(default_factory=list)
    direction: OrderingDirection = OrderingDirection.ASCENDING

    def sort_layers(self, layer_names: list[str]) -> list[str]:
        if self.order:
            ordered = [n for n in self.order if n in layer_names]
            remaining = [n for n in layer_names if n not in self.order]
            ordered.extend(sorted(remaining))
            return ordered if self.direction == OrderingDirection.ASCENDING else list(reversed(ordered))
        return sorted(layer_names)


class VisibilityPolicy:
    def __init__(self, allowed_layers: list[str] | None = None) -> None:
        self._allowed = allowed_layers

    def filter(self, layers: dict[str, Any]) -> dict[str, Any]:
        if self._allowed is None:
            return layers
        return {k: v for k, v in layers.items() if k in self._allowed}


class PrivacyPolicy:
    def __init__(self, sensitive_fields: list[str] | None = None) -> None:
        self._sensitive_fields = sensitive_fields or ["email", "phone", "password", "api_key", "token"]

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in self._sensitive_fields:
                result[key] = self._redact_value(value)
            elif isinstance(value, dict):
                result[key] = self.redact(value)
            elif isinstance(value, list):
                result[key] = [
                    self.redact(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def _redact_value(self, value: Any) -> str:
        s = str(value)
        if len(s) <= 4:
            return "****"
        return s[:2] + "****" + s[-2:]


@dataclass
class ContextPolicy:
    ordering: LayerOrderingPolicy = field(default_factory=LayerOrderingPolicy)
    visibility: VisibilityPolicy = field(default_factory=VisibilityPolicy)
    privacy: PrivacyPolicy = field(default_factory=PrivacyPolicy)
    max_layers: int = 10
    fail_on_missing_source: bool = False
