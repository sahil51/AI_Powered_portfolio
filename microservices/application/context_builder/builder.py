from __future__ import annotations

import time
from typing import Any

from application.context_builder.assembler import ContextAssemblerImpl
from application.context_builder.budget import ContextBudget
from application.context_builder.compression import ContextCompressionPolicy
from application.context_builder.interfaces import ContextAssembler, ContextLayer
from application.context_builder.layers.conversation import ConversationContextLayer
from application.context_builder.layers.identity import IdentityContextLayer
from application.context_builder.layers.knowledge import KnowledgeContextLayer
from application.context_builder.layers.memory import MemoryContextLayer
from application.context_builder.layers.system import SystemContextLayer
from application.context_builder.layers.tool import ToolContextLayer
from application.context_builder.layers.workflow import WorkflowContextLayer
from application.context_builder.metrics import ContextMetrics
from application.context_builder.models import BuiltContext, ContextLayerResult, ContextMetadata
from application.context_builder.policies import ContextPolicy
from application.context_builder.validator import ContextValidator


class ContextBuilder:
    def __init__(
        self,
        budget: ContextBudget | None = None,
        compression: ContextCompressionPolicy | None = None,
        policy: ContextPolicy | None = None,
        assembler: ContextAssembler | None = None,
    ) -> None:
        self._budget = budget or ContextBudget()
        self._compression = compression or ContextCompressionPolicy()
        self._policy = policy or ContextPolicy()
        self._assembler = assembler or ContextAssemblerImpl()
        self._metrics = ContextMetrics()
        self._validator = ContextValidator()
        self._layers: list[ContextLayer] = []

    def register_default_layers(self) -> None:
        self._layers = [
            SystemContextLayer(),
            IdentityContextLayer(),
            ConversationContextLayer(),
            MemoryContextLayer(),
            WorkflowContextLayer(),
            KnowledgeContextLayer(enabled=False),
            ToolContextLayer(enabled=False),
        ]
        for layer in self._layers:
            self._assembler.add_layer(layer)

    def add_layer(self, layer: ContextLayer) -> None:
        self._layers.append(layer)
        self._assembler.add_layer(layer)

    def remove_layer(self, name: str) -> None:
        self._layers = [layer for layer in self._layers if layer.name != name]
        self._assembler.remove_layer(name)

    def enable_layer(self, name: str) -> None:
        for layer in self._layers:
            if layer.name == name and hasattr(layer, "set_enabled"):
                layer.set_enabled(True)

    def disable_layer(self, name: str) -> None:
        for layer in self._layers:
            if layer.name == name and hasattr(layer, "set_enabled"):
                layer.set_enabled(False)

    def get_layer(self, name: str) -> ContextLayer | None:
        return self._assembler.get_layer(name)

    async def build(self, **kwargs: Any) -> BuiltContext:
        start = time.time()
        enabled_layers = [layer for layer in self._layers if layer.is_enabled()]

        if not enabled_layers:
            enabled_layers = [layer for layer in self._layers]
            for layer in enabled_layers:
                if hasattr(layer, "set_enabled"):
                    layer.set_enabled(True)

        policy_order = self._policy.ordering.sort_layers([layer.name for layer in enabled_layers])
        ordered_layers = sorted(
            enabled_layers,
            key=lambda layer: policy_order.index(layer.name) if layer.name in policy_order else 999,
        )

        raw_data = await self._assembler.assemble(ordered_layers, **kwargs)

        layer_results: dict[str, ContextLayerResult] = {}
        for layer in ordered_layers:
            data = raw_data.get(layer.name, {})
            compressed = self._compression.compress(data, self._estimate_tokens)
            tokens = self._estimate_tokens_in_data(compressed)
            layer_results[layer.name] = ContextLayerResult(
                name=layer.name,
                data=self._policy.privacy.redact(compressed),
                tokens=tokens,
                priority=layer.priority,
                enabled=layer.is_enabled(),
            )

        total_tokens = sum(layer.tokens for layer in layer_results.values())
        elapsed = (time.time() - start) * 1000
        filtered = self._policy.visibility.filter(layer_results)

        metadata = ContextMetadata(
            total_tokens=total_tokens,
            layer_count=len(layer_results),
            enabled_layer_count=len([layer for layer in layer_results.values() if layer.enabled]),
            max_tokens=self._budget.max_tokens,
            reserved_tokens=self._budget.reserved_tokens,
            elapsed_ms=elapsed,
        )

        context = BuiltContext(
            layers=dict(filtered),
            metadata=metadata,
            layer_order=[layer.name for layer in ordered_layers if layer.name in filtered],
        )

        self._metrics.record_build(len(layer_results), total_tokens, elapsed)
        self._validator.raise_if_invalid(context)

        return context

    @property
    def budget(self) -> ContextBudget:
        return self._budget

    @property
    def metrics(self) -> ContextMetrics:
        return self._metrics

    @property
    def policy(self) -> ContextPolicy:
        return self._policy

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _estimate_tokens_in_data(self, data: dict[str, Any]) -> int:
        import json
        try:
            text = json.dumps(data, default=str)
        except (TypeError, ValueError):
            text = str(data)
        return self._estimate_tokens(text)
