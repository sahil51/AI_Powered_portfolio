from __future__ import annotations

from typing import TYPE_CHECKING

from application.ai.exceptions import ProviderValidationError
from application.ai.validation import validate_completion_request

if TYPE_CHECKING:
    from application.ai.models import CompletionRequest


class LiteLLMValidator:
    def validate_request(self, request: "CompletionRequest") -> None:
        validate_completion_request(request)

    def validate_model(self, model: str) -> str:
        if not model or not isinstance(model, str):
            raise ProviderValidationError("Invalid model", detail=f"Model must be a non-empty string, got: {model!r}")
        return model.strip()

    def validate_response(self, response: dict) -> None:
        if "choices" not in response:
            raise ProviderValidationError("Invalid response", detail="Response missing 'choices' field")
        if not response["choices"]:
            raise ProviderValidationError("Invalid response", detail="Response has empty choices")
        choice = response["choices"][0]
        if "message" not in choice and "delta" not in choice:
            pass
