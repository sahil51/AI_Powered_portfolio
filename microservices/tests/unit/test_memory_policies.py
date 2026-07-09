
from domain.memory.policies import MemoryPolicies
from domain.memory.value_objects import MemoryConfidence, MemoryImportance, MemoryScope


class TestMemoryPolicies:
    def test_default_policies(self):
        policies = MemoryPolicies()
        assert policies.default_retention_days == 365
        assert policies.max_retention_days == 730
        assert policies.max_memories_per_scope_user == 1000

    def test_retention_exceeded(self):
        policies = MemoryPolicies(default_retention_days=365)
        assert policies.retention_exceeded(366)
        assert not policies.retention_exceeded(364)

    def test_max_retention_exceeded(self):
        policies = MemoryPolicies(max_retention_days=730)
        assert policies.max_retention_exceeded(731)
        assert not policies.max_retention_exceeded(729)

    def test_is_confidence_sufficient(self):
        policies = MemoryPolicies(min_confidence_for_persist=MemoryConfidence.LOW)
        assert policies.is_confidence_sufficient(MemoryConfidence.CERTAIN)
        assert policies.is_confidence_sufficient(MemoryConfidence.LOW)
        assert not policies.is_confidence_sufficient(MemoryConfidence.UNCERTAIN)

    def test_can_overwrite(self):
        policies = MemoryPolicies(overwrite_requires_confidence_above=MemoryConfidence.MEDIUM)
        assert policies.can_overwrite(MemoryConfidence.LOW, MemoryConfidence.HIGH)
        assert not policies.can_overwrite(MemoryConfidence.LOW, MemoryConfidence.LOW)

    def test_exceeds_scope_limit_user(self):
        policies = MemoryPolicies(max_memories_per_scope_user=100)
        assert policies.exceeds_scope_limit(100, MemoryScope.USER)
        assert not policies.exceeds_scope_limit(99, MemoryScope.USER)

    def test_exceeds_scope_limit_conversation(self):
        policies = MemoryPolicies(max_memories_per_conversation=50)
        assert policies.exceeds_scope_limit(50, MemoryScope.CONVERSATION)
        assert not policies.exceeds_scope_limit(49, MemoryScope.CONVERSATION)

    def test_should_notify_importance(self):
        policies = MemoryPolicies(importance_threshold_for_notification=MemoryImportance.HIGH)
        assert policies.should_notify_importance(MemoryImportance.CRITICAL)
        assert policies.should_notify_importance(MemoryImportance.HIGH)
        assert not policies.should_notify_importance(MemoryImportance.MEDIUM)
        assert not policies.should_notify_importance(MemoryImportance.LOW)
