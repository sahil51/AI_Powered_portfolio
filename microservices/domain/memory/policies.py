from dataclasses import dataclass

from domain.memory.value_objects import MemoryConfidence, MemoryImportance, MemoryScope


@dataclass
class MemoryPolicies:
    default_retention_days: int = 365
    max_retention_days: int = 730
    min_confidence_for_persist: MemoryConfidence = MemoryConfidence.LOW
    max_conflict_merge_count: int = 10
    overwrite_requires_confidence_above: MemoryConfidence = MemoryConfidence.MEDIUM
    importance_threshold_for_notification: MemoryImportance = MemoryImportance.HIGH
    max_memories_per_scope_user: int = 1000
    max_memories_per_conversation: int = 500
    enable_tenant_isolation: bool = True
    enable_privacy_check: bool = True

    def retention_exceeded(self, elapsed_days: float) -> bool:
        return elapsed_days > self.default_retention_days

    def max_retention_exceeded(self, elapsed_days: float) -> bool:
        return elapsed_days > self.max_retention_days

    def is_confidence_sufficient(self, confidence: MemoryConfidence) -> bool:
        levels = list(MemoryConfidence)
        return levels.index(confidence) <= levels.index(self.min_confidence_for_persist)

    def can_overwrite(self, existing_confidence: MemoryConfidence, incoming_confidence: MemoryConfidence) -> bool:
        levels = list(MemoryConfidence)
        return levels.index(incoming_confidence) <= levels.index(self.overwrite_requires_confidence_above)

    def exceeds_scope_limit(self, current_count: int, scope: MemoryScope) -> bool:
        if scope == MemoryScope.CONVERSATION:
            return current_count >= self.max_memories_per_conversation
        return current_count >= self.max_memories_per_scope_user

    def should_notify_importance(self, importance: MemoryImportance) -> bool:
        levels = list(MemoryImportance)
        return levels.index(importance) <= levels.index(self.importance_threshold_for_notification)


default_policies = MemoryPolicies()
