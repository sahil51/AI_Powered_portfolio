from __future__ import annotations

from dataclasses import dataclass

from application.ai.capability import ProviderCapability
from application.ai.models import ModelCapabilities, ModelInfo


@dataclass
class ModelDefinition:
    id: str
    provider: str
    display_name: str = ""
    max_context_length: int = 8192
    max_output_tokens: int = 2048
    supports_streaming: bool = True
    supports_json_mode: bool = True
    supports_function_calling: bool = True
    supports_tool_calling: bool = True
    supports_parallel_tool_calling: bool = True
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_structured_output: bool = True
    priority: int = 0
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    def to_model_info(self, healthy: bool = True) -> ModelInfo:
        return ModelInfo(
            id=self.id,
            provider=self.provider,
            display_name=self.display_name or self.id,
            capabilities=ModelCapabilities(
                max_context_length=self.max_context_length,
                max_output_tokens=self.max_output_tokens,
                supports_streaming=self.supports_streaming,
                supports_json_mode=self.supports_json_mode,
                supports_function_calling=self.supports_function_calling,
                supports_tool_calling=self.supports_tool_calling,
                supports_parallel_tool_calling=self.supports_parallel_tool_calling,
                supports_vision=self.supports_vision,
                supports_embeddings=self.supports_embeddings,
                supports_structured_output=self.supports_structured_output,
            ),
            priority=self.priority,
            healthy=healthy,
        )


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelDefinition] = {}

    def register(self, definition: ModelDefinition) -> None:
        self._models[definition.id] = definition

    def register_many(self, definitions: list[ModelDefinition]) -> None:
        for definition in definitions:
            self._models[definition.id] = definition

    def get(self, model_id: str) -> ModelDefinition | None:
        return self._models.get(model_id)

    def list_models(self, healthy_only: bool = True) -> list[ModelInfo]:
        return [d.to_model_info(healthy=True) for d in self._models.values()]

    def list_ids(self) -> list[str]:
        return list(self._models.keys())

    def supports(self, model_id: str, capability: ProviderCapability | str) -> bool:
        model = self._models.get(model_id)
        if model is None:
            return False
        cap_str = capability.value if isinstance(capability, ProviderCapability) else capability
        return model.to_model_info().capabilities.has(cap_str)

    @property
    def count(self) -> int:
        return len(self._models)

    def clear(self) -> None:
        self._models.clear()
