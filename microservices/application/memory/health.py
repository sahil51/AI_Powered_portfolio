from dataclasses import dataclass, field

from domain.memory.policies import MemoryPolicies


@dataclass
class MemoryHealthStatus:
    healthy: bool = False
    total_memories: int = 0
    active_memories: int = 0
    expired_memories: int = 0
    policies: dict | None = None
    errors: list[str] = field(default_factory=list)


class MemoryHealthCheck:
    def __init__(self, policies: MemoryPolicies | None = None) -> None:
        self._policies = policies or MemoryPolicies()

    async def check(
        self,
        total_count: int,
        active_count: int,
        expired_count: int,
    ) -> MemoryHealthStatus:
        errors: list[str] = []
        healthy = True

        if total_count < 0:
            errors.append("Total memory count is negative")
            healthy = False
        if active_count < 0:
            errors.append("Active memory count is negative")
            healthy = False

        return MemoryHealthStatus(
            healthy=healthy,
            total_memories=total_count,
            active_memories=active_count,
            expired_memories=expired_count,
            policies={
                "default_retention_days": self._policies.default_retention_days,
                "max_retention_days": self._policies.max_retention_days,
                "max_memories_per_user": self._policies.max_memories_per_scope_user,
                "max_memories_per_conversation": self._policies.max_memories_per_conversation,
            },
            errors=errors,
        )
