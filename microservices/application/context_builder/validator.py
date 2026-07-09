from __future__ import annotations

from application.context_builder.budget import ContextBudget
from application.context_builder.models import BuiltContext, ContextLayerResult


class ContextValidationError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class ContextValidator:
    def validate_budget(self, budget: ContextBudget) -> list[str]:
        errors: list[str] = []
        if budget.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        if budget.reserved_tokens < 0:
            errors.append("reserved_tokens must be non-negative")
        if budget.output_tokens < 0:
            errors.append("output_tokens must be non-negative")
        if budget.reserved_tokens + budget.output_tokens >= budget.max_tokens:
            errors.append("reserved + output tokens exceed max_tokens")
        if budget.max_layers <= 0:
            errors.append("max_layers must be positive")
        return errors

    def validate_layer_result(self, result: ContextLayerResult) -> list[str]:
        errors: list[str] = []
        if not result.name:
            errors.append("layer name must not be empty")
        if result.tokens < 0:
            errors.append("token count must be non-negative")
        return errors

    def validate_built_context(self, context: BuiltContext) -> list[str]:
        errors: list[str] = []
        if not context.layers:
            errors.append("context must have at least one layer")
        for name, layer in context.layers.items():
            layer_errors = self.validate_layer_result(layer)
            for err in layer_errors:
                errors.append(f"layer '{name}': {err}")
        if context.metadata.total_tokens < 0:
            errors.append("total_tokens must be non-negative")
        if context.metadata.max_tokens < 0:
            errors.append("max_tokens must be non-negative")
        return errors

    def raise_if_invalid(self, context: BuiltContext) -> None:
        errors = self.validate_built_context(context)
        if errors:
            raise ContextValidationError("Context validation failed", detail="; ".join(errors))
