from dataclasses import dataclass, field

from domain.conversation.policies import ConversationPolicies


@dataclass
class ConversationHealthStatus:
    healthy: bool = False
    active_conversations: int = 0
    total_conversations: int = 0
    policies: dict | None = None
    errors: list[str] = field(default_factory=list)


class ConversationHealthCheck:
    def __init__(self, policies: ConversationPolicies | None = None) -> None:
        self._policies = policies or ConversationPolicies()

    async def check(self, active_count: int, total_count: int) -> ConversationHealthStatus:
        errors: list[str] = []
        healthy = True

        if active_count < 0:
            errors.append("Active conversation count is negative")
            healthy = False

        if total_count < 0:
            errors.append("Total conversation count is negative")
            healthy = False

        return ConversationHealthStatus(
            healthy=healthy,
            active_conversations=active_count,
            total_conversations=total_count,
            policies={
                "timeout_minutes": self._policies.conversation_timeout_minutes,
                "archive_after_days": self._policies.archive_after_days,
                "retention_days": self._policies.retention_days,
                "max_active_per_user": self._policies.max_active_conversations_per_user,
            },
            errors=errors,
        )
