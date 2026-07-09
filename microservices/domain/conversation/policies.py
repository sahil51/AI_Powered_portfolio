from dataclasses import dataclass


@dataclass
class ConversationPolicies:
    conversation_timeout_minutes: int = 30
    archive_after_days: int = 90
    resume_after_pause_max_minutes: int = 60
    retention_days: int = 365
    max_active_conversations_per_user: int = 10
    max_messages_per_conversation: int = 1000
    max_message_length: int = 10000
    max_participants: int = 10
    enforce_ownership: bool = True
    enforce_concurrency: bool = True

    def should_timeout(self, elapsed_minutes: float) -> bool:
        return elapsed_minutes > self.conversation_timeout_minutes

    def should_archive(self, elapsed_days: float) -> bool:
        return elapsed_days > self.archive_after_days

    def can_resume(self, elapsed_minutes: float) -> bool:
        return elapsed_minutes <= self.resume_after_pause_max_minutes

    def should_expire_retention(self, elapsed_days: float) -> bool:
        return elapsed_days > self.retention_days

    def exceeds_max_messages(self, message_count: int) -> bool:
        return message_count >= self.max_messages_per_conversation

    def exceeds_max_message_length(self, content_length: int) -> bool:
        return content_length > self.max_message_length

    def exceeds_max_participants(self, participant_count: int) -> bool:
        return participant_count > self.max_participants

    @property
    def timeout_seconds(self) -> int:
        return self.conversation_timeout_minutes * 60

    @property
    def resume_timeout_seconds(self) -> int:
        return self.resume_after_pause_max_minutes * 60


default_policies = ConversationPolicies()
