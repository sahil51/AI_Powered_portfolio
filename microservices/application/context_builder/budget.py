from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextBudget:
    max_tokens: int = 8192
    reserved_tokens: int = 1024
    output_tokens: int = 2048
    layer_allocations: dict[str, int] = field(default_factory=dict)
    used_tokens: int = 0
    compression_enabled: bool = True
    max_layers: int = 10

    @property
    def available_tokens(self) -> int:
        return self.max_tokens - self.reserved_tokens - self.output_tokens - self.used_tokens

    @property
    def total_budget(self) -> int:
        return self.max_tokens - self.reserved_tokens


class ContextBudgetPolicy:
    def __init__(self, max_tokens: int = 8192, reserved_tokens: int = 1024, output_tokens: int = 2048) -> None:
        self._max_tokens = max_tokens
        self._reserved_tokens = reserved_tokens
        self._output_tokens = output_tokens

    def create_budget(self, layer_weights: dict[str, float]) -> ContextBudget:
        available = self._max_tokens - self._reserved_tokens - self._output_tokens
        total_weight = sum(layer_weights.values()) or 1.0
        allocations: dict[str, int] = {}
        for name, weight in layer_weights.items():
            allocations[name] = int((weight / total_weight) * available)
        return ContextBudget(
            max_tokens=self._max_tokens,
            reserved_tokens=self._reserved_tokens,
            output_tokens=self._output_tokens,
            layer_allocations=allocations,
            compression_enabled=True,
        )

    def is_within_budget(self, budget: ContextBudget, layer_name: str, tokens: int) -> bool:
        allocation = budget.layer_allocations.get(layer_name, 0)
        if allocation <= 0:
            return True
        current_used = sum(
            v for k, v in budget.layer_allocations.items() if k != layer_name
        )
        used_for_layer = budget.used_tokens - current_used
        return (used_for_layer + tokens) <= allocation

    def enforce(self, budget: ContextBudget) -> ContextBudget:
        if budget.used_tokens > budget.total_budget:
            budget.compression_enabled = True
        return budget
