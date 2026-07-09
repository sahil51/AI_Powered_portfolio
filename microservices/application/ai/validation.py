from __future__ import annotations

from application.ai.exceptions import ProviderValidationError
from application.ai.models import CompletionRequest


def validate_completion_request(request: CompletionRequest) -> None:
    errors: list[str] = []
    if request.model and not isinstance(request.model, str):
        errors.append("model must be a string")
    if request.temperature is not None and not (0.0 <= request.temperature <= 2.0):
        errors.append("temperature must be between 0.0 and 2.0")
    if request.max_tokens is not None and request.max_tokens < 1:
        errors.append("max_tokens must be positive")
    if request.timeout is not None and request.timeout <= 0:
        errors.append("timeout must be positive")
    if request.top_p is not None and not (0.0 <= request.top_p <= 1.0):
        errors.append("top_p must be between 0.0 and 1.0")
    if request.presence_penalty is not None and not (-2.0 <= request.presence_penalty <= 2.0):
        errors.append("presence_penalty must be between -2.0 and 2.0")
    if request.frequency_penalty is not None and not (-2.0 <= request.frequency_penalty <= 2.0):
        errors.append("frequency_penalty must be between -2.0 and 2.0")
    if not request.system_prompt and not request.messages:
        errors.append("at least one of system_prompt or messages must be provided")
    for msg in request.messages:
        if "role" not in msg:
            errors.append("each message must have a 'role' field")
            break
        if "content" not in msg:
            errors.append("each message must have a 'content' field")
            break
    if errors:
        raise ProviderValidationError("Validation failed", detail="; ".join(errors))


def validate_model_name(model: str) -> str:
    if not model or not isinstance(model, str):
        raise ProviderValidationError("Invalid model name", detail=f"Model must be a non-empty string, got: {model!r}")
    return model.strip()
