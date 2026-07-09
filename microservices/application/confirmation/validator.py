from __future__ import annotations

from application.confirmation.exceptions import ConfirmationValidationError
from application.confirmation.models import ConfirmationContext, ConfirmationResult
from domain.enums.confirmation import ConfirmationType


class ConfirmationValidator:
    def validate_context(self, context: ConfirmationContext) -> None:
        if not context:
            raise ConfirmationValidationError("Confirmation context is required")
        if not context.user_reply or not context.user_reply.strip():
            raise ConfirmationValidationError("User reply cannot be empty")
        if not context.user_id:
            raise ConfirmationValidationError("User ID is required")
        if not context.conversation_id:
            raise ConfirmationValidationError("Conversation ID is required")

    def validate_result(self, result: ConfirmationResult) -> bool:
        if not result.confirmation_type:
            raise ConfirmationValidationError("Confirmation type is required")
        if result.confirmation_type == ConfirmationType.UNKNOWN and result.confirmed:
            raise ConfirmationValidationError(
                "Unknown confirmation type cannot be marked as confirmed"
            )
        return True

    def is_valid_type(self, raw: str) -> bool:
        try:
            ConfirmationType(raw)
            return True
        except ValueError:
            return False
