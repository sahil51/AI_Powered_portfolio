from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol


class ContextSource(Protocol):
    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        ...


@dataclass
class LayerConfig:
    name: str
    enabled: bool = True
    priority: int = 0
    max_tokens: int = 0
    weight: float = 1.0


class ContextLayer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def priority(self) -> int:
        ...

    @abstractmethod
    async def build(self, **kwargs: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def is_enabled(self) -> bool:
        ...

    def get_config(self) -> LayerConfig:
        return LayerConfig(name=self.name, enabled=self.is_enabled(), priority=self.priority)


class ContextAssembler(ABC):
    @abstractmethod
    async def assemble(self, layers: list[ContextLayer], **kwargs: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def add_layer(self, layer: ContextLayer) -> None:
        ...

    @abstractmethod
    def remove_layer(self, name: str) -> None:
        ...

    @abstractmethod
    def get_layer(self, name: str) -> ContextLayer | None:
        ...

    @abstractmethod
    def list_layers(self) -> list[ContextLayer]:
        ...
