from __future__ import annotations

from application.intent.exceptions import IntentValidationError
from application.intent.models import IntentRequest, IntentResult
from application.intent.policies import IntentPolicy
from domain.enums.intent import IntentType


class IntentValidator:
    def __init__(self, policy: IntentPolicy | None = None) -> None:
        self._policy = policy or IntentPolicy()

    def validate_request(self, request: IntentRequest) -> None:
        if not request.context:
            raise IntentValidationError("Request context is required")
        if not request.context.message or not request.context.message.strip():
            raise IntentValidationError("User message cannot be empty")
        if not request.context.user_id:
            raise IntentValidationError("User ID is required")
        if not request.context.conversation_id:
            raise IntentValidationError("Conversation ID is required")

    def validate_result(self, result: IntentResult) -> bool:
        if not result.intent:
            raise IntentValidationError("Intent type is required")
        if result.confidence < 0.0 or result.confidence > 1.0:
            raise IntentValidationError(
                f"Confidence must be between 0.0 and 1.0, got {result.confidence}"
            )
        if result.intent == IntentType.UNKNOWN and result.confidence > 0.9:
            raise IntentValidationError(
                "Unknown intent with high confidence is contradictory"
            )
        return True

    def is_valid_intent(self, intent: str) -> bool:
        try:
            IntentType(intent)
            return True
        except ValueError:
            return False
