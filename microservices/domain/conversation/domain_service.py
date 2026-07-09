from domain.conversation.aggregate import Conversation
from domain.conversation.policies import ConversationPolicies, default_policies
from domain.conversation.state import ConversationState
from domain.conversation.validator import ConversationValidator
from domain.conversation.value_objects import (
    Message,
)


class ConversationDomainService:
    def __init__(
        self,
        validator: ConversationValidator | None = None,
        policies: ConversationPolicies | None = None,
    ) -> None:
        self._validator = validator or ConversationValidator()
        self._policies = policies or default_policies

    def check_timeout(self, conversation: Conversation) -> bool:
        elapsed = conversation.elapsed_since_last_activity()
        return self._policies.should_timeout(elapsed)

    def check_pause_timeout(self, conversation: Conversation) -> bool:
        elapsed = conversation.elapsed_since_paused()
        if elapsed is None:
            return False
        return not self._policies.can_resume(elapsed)

    def check_archive_ready(self, conversation: Conversation) -> bool:
        if not conversation.is_terminal:
            return False
        from datetime import datetime, timezone
        ref = conversation.completed_at or conversation.updated_at
        elapsed = (datetime.now(timezone.utc) - ref).total_seconds() / 86400.0
        return self._policies.should_archive(elapsed)

    def check_retention_expired(self, conversation: Conversation) -> bool:
        from datetime import datetime, timezone
        ref = conversation.completed_at or conversation.created_at
        elapsed = (datetime.now(timezone.utc) - ref).total_seconds() / 86400.0
        return self._policies.should_expire_retention(elapsed)

    def can_add_message(self, conversation: Conversation, message: Message) -> bool:
        if not conversation.state_machine.can_accept_messages():
            return False
        if self._policies.exceeds_max_messages(conversation.message_count):
            return False
        if self._policies.exceeds_max_message_length(len(message.content)):
            return False
        if not self._validator.validate_duplicate_message(conversation, message.content):
            return False
        return True

    def can_transition_to(self, conversation: Conversation, target: ConversationState) -> bool:
        return conversation.state_machine.can_transition_to(target)

    def evaluate_needed_state(self, conversation: Conversation) -> ConversationState:
        if conversation.is_terminal or conversation.is_paused:
            return conversation.state
        return conversation.state
