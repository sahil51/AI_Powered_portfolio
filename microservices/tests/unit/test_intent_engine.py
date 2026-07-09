import pytest

from application.intent.exceptions import (
    IntentClassificationError,
    IntentConfigurationError,
    IntentEngineError,
    IntentResolutionError,
    IntentValidationError,
)
from application.intent.models import (
    ConfidenceLevel,
    ExtractedEntity,
    IntentContext,
    IntentMetadata,
    IntentRequest,
    IntentResult,
)
from application.intent.policies import IntentPolicy, default_intent_policy
from application.intent.resolver import IntentResolver
from application.intent.statistics import IntentStatistics
from application.intent.validator import IntentValidator
from domain.enums.intent import IntentType


class TestIntentModels:
    def test_extracted_entity_defaults(self) -> None:
        entity = ExtractedEntity()
        assert entity.person_name is None
        assert entity.tags == []
        assert entity.workflow_parameters == {}

    def test_extracted_entity_with_values(self) -> None:
        entity = ExtractedEntity(
            person_name="John Doe",
            company="Acme Inc",
            email="john@acme.com",
            date="2026-07-15",
            duration=60,
            tags=["meeting"],
        )
        assert entity.person_name == "John Doe"
        assert entity.email == "john@acme.com"
        assert entity.duration == 60

    def test_intent_context_creation(self) -> None:
        ctx = IntentContext(
            user_id="user1",
            session_id="session1",
            conversation_id="conv1",
            message="Schedule a meeting",
        )
        assert ctx.user_id == "user1"
        assert ctx.message == "Schedule a meeting"

    def test_intent_result_defaults(self) -> None:
        result = IntentResult(
            intent=IntentType.GREETING,
            confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        assert result.needs_confirmation is False
        assert result.missing_fields == []

    def test_intent_result_with_all_fields(self) -> None:
        metadata = IntentMetadata(latency_ms=150.0, model="gpt-4")
        result = IntentResult(
            intent=IntentType.MEETING_SCHEDULE,
            confidence=0.88,
            confidence_level=ConfidenceLevel.HIGH,
            entities=ExtractedEntity(person_name="Alice"),
            needs_confirmation=True,
            missing_fields=["date", "time"],
            suggested_agent="meeting_agent",
            workflow_hint="schedule_meeting",
            metadata=metadata,
        )
        assert result.intent == IntentType.MEETING_SCHEDULE
        assert result.needs_confirmation is True
        assert result.missing_fields == ["date", "time"]
        assert result.suggested_agent == "meeting_agent"

    def test_confidence_level_values(self) -> None:
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.UNCERTAIN.value == "uncertain"

    def test_intent_request_creation(self) -> None:
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message="test"
        )
        request = IntentRequest(context=ctx, prompt_version="2.0.0", temperature=0.3)
        assert request.context.user_id == "u1"
        assert request.prompt_version == "2.0.0"
        assert request.temperature == 0.3


class TestIntentValidator:
    def setup_method(self) -> None:
        self.validator = IntentValidator()

    def test_validate_valid_request(self) -> None:
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message="Hello"
        )
        self.validator.validate_request(IntentRequest(context=ctx))

    def test_validate_empty_message_raises_error(self) -> None:
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message=""
        )
        with pytest.raises(IntentValidationError, match="cannot be empty"):
            self.validator.validate_request(IntentRequest(context=ctx))

    def test_validate_missing_user_id_raises_error(self) -> None:
        ctx = IntentContext(
            user_id="", session_id="s1", conversation_id="c1", message="Hello"
        )
        with pytest.raises(IntentValidationError, match="User ID is required"):
            self.validator.validate_request(IntentRequest(context=ctx))

    def test_validate_missing_conversation_id_raises_error(self) -> None:
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="", message="Hello"
        )
        with pytest.raises(IntentValidationError, match="Conversation ID is required"):
            self.validator.validate_request(IntentRequest(context=ctx))

    def test_validate_result_valid(self) -> None:
        result = IntentResult(
            intent=IntentType.GREETING, confidence=0.95, confidence_level=ConfidenceLevel.HIGH
        )
        assert self.validator.validate_result(result) is True

    def test_validate_result_negative_confidence(self) -> None:
        result = IntentResult(
            intent=IntentType.GREETING, confidence=-0.1, confidence_level=ConfidenceLevel.UNCERTAIN
        )
        with pytest.raises(IntentValidationError, match="between 0.0 and 1.0"):
            self.validator.validate_result(result)

    def test_validate_confident_unknown_raises(self) -> None:
        result = IntentResult(
            intent=IntentType.UNKNOWN, confidence=0.95, confidence_level=ConfidenceLevel.HIGH
        )
        with pytest.raises(IntentValidationError, match="contradictory"):
            self.validator.validate_result(result)

    def test_is_valid_intent(self) -> None:
        assert self.validator.is_valid_intent("greeting") is True
        assert self.validator.is_valid_intent("meeting_schedule") is True
        assert self.validator.is_valid_intent("invalid") is False


class TestIntentPolicy:
    def setup_method(self) -> None:
        self.policy = default_intent_policy()

    def test_default_thresholds(self) -> None:
        assert self.policy.auto_accept_threshold == 0.85
        assert self.policy.clarification_threshold == 0.60
        assert self.policy.fallback_threshold == 0.30

    def test_get_confidence_label(self) -> None:
        assert self.policy.get_confidence_label(0.90) == "high"
        assert self.policy.get_confidence_label(0.70) == "medium"
        assert self.policy.get_confidence_label(0.40) == "low"
        assert self.policy.get_confidence_label(0.20) == "uncertain"

    def test_needs_confirmation(self) -> None:
        assert self.policy.needs_confirmation(IntentType.MEETING_SCHEDULE) is True
        assert self.policy.needs_confirmation(IntentType.GREETING) is False

    def test_needs_clarification(self) -> None:
        assert self.policy.needs_clarification(IntentType.UNKNOWN) is True
        assert self.policy.needs_clarification(IntentType.GREETING) is False

    def test_auto_accept(self) -> None:
        assert self.policy.auto_accept(IntentType.GREETING) is True
        assert self.policy.auto_accept(IntentType.MEETING_SCHEDULE) is False

    def test_custom_thresholds(self) -> None:
        policy = IntentPolicy(
            auto_accept_threshold=0.90,
            clarification_threshold=0.70,
            fallback_threshold=0.40,
        )
        assert policy.get_confidence_label(0.85) == "medium"
        assert policy.get_confidence_label(0.50) == "low"


class TestIntentStatistics:
    def setup_method(self) -> None:
        self.stats = IntentStatistics()

    def test_record_classification(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 100.0, "user1", "session1")
        assert self.stats.data.total_classified == 1
        assert self.stats.data.by_intent.get("greeting") == 1

    def test_multiple_classifications(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 100.0, "u1", "s1")
        self.stats.record(IntentType.MEETING_SCHEDULE, 0.80, 200.0, "u1", "s1")
        assert self.stats.data.total_classified == 2
        assert self.stats.data.by_intent.get("meeting_schedule") == 1

    def test_avg_confidence_and_latency(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 100.0, "u1", "s1")
        self.stats.record(IntentType.MEETING_SCHEDULE, 0.75, 200.0, "u2", "s2")
        assert self.stats.data.avg_confidence == 0.85
        assert self.stats.data.avg_latency_ms == 150.0
        assert self.stats.data.user_count == 2

    def test_top_intents(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 50.0, "u1", "s1")
        self.stats.record(IntentType.GREETING, 0.90, 60.0, "u1", "s2")
        self.stats.record(IntentType.MEETING_SCHEDULE, 0.85, 70.0, "u1", "s3")
        assert self.stats.data.top_intents[0][0] == "greeting"
        assert self.stats.data.top_intents[0][1] == 2

    def test_reset(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 50.0, "u1", "s1")
        self.stats.reset()
        assert self.stats.data.total_classified == 0

    def test_by_confidence_level(self) -> None:
        self.stats.record(IntentType.GREETING, 0.95, 50.0, "u1", "s1")
        assert self.stats.data.by_confidence_level.get("high") == 1


class TestIntentResolver:
    @pytest.mark.asyncio
    async def test_unknown_requires_clarification(self) -> None:
        resolver = IntentResolver()
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message="xyzzy"
        )
        result = IntentResult(
            intent=IntentType.UNKNOWN, confidence=0.30, confidence_level=ConfidenceLevel.LOW
        )
        resolved = await resolver.resolve(result, ctx)
        assert resolved.needs_clarification is True

    @pytest.mark.asyncio
    async def test_fallback_resolved_from_context(self) -> None:
        resolver = IntentResolver()
        ctx = IntentContext(
            user_id="u1",
            session_id="s1",
            conversation_id="c1",
            message="do it",
            conversation_history=[{"role": "assistant", "content": "intent: meeting_schedule confirmed"}],
        )
        result = IntentResult(
            intent=IntentType.FALLBACK, confidence=0.40, confidence_level=ConfidenceLevel.LOW
        )
        resolved = await resolver.resolve(result, ctx)
        assert resolved.intent != IntentType.FALLBACK

    @pytest.mark.asyncio
    async def test_low_confidence_resolved_from_context(self) -> None:
        resolver = IntentResolver()
        ctx = IntentContext(
            user_id="u1",
            session_id="s1",
            conversation_id="c1",
            message="yes",
            conversation_history=[{"role": "assistant", "content": "intent: meeting_schedule"}],
        )
        result = IntentResult(
            intent=IntentType.GREETING, confidence=0.20, confidence_level=ConfidenceLevel.UNCERTAIN
        )
        resolved = await resolver.resolve(result, ctx)
        assert resolved.intent == IntentType.MEETING_SCHEDULE

    @pytest.mark.asyncio
    async def test_high_confidence_passes_through(self) -> None:
        resolver = IntentResolver()
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message="hello"
        )
        result = IntentResult(
            intent=IntentType.GREETING, confidence=0.95, confidence_level=ConfidenceLevel.HIGH
        )
        resolved = await resolver.resolve(result, ctx)
        assert resolved.intent == IntentType.GREETING

    @pytest.mark.asyncio
    async def test_missing_fields_for_meeting(self) -> None:
        resolver = IntentResolver()
        ctx = IntentContext(
            user_id="u1", session_id="s1", conversation_id="c1", message="schedule"
        )
        result = IntentResult(
            intent=IntentType.MEETING_SCHEDULE,
            confidence=0.88,
            confidence_level=ConfidenceLevel.HIGH,
            entities=ExtractedEntity(),
        )
        resolved = await resolver.resolve(result, ctx)
        assert len(resolved.missing_fields) > 0
        assert "date" in resolved.missing_fields


class TestIntentExceptions:
    def test_error_hierarchy(self) -> None:
        assert issubclass(IntentClassificationError, IntentEngineError)
        assert issubclass(IntentValidationError, IntentEngineError)
        assert issubclass(IntentResolutionError, IntentEngineError)
        assert issubclass(IntentConfigurationError, IntentEngineError)

    def test_classification_error_with_detail(self) -> None:
        err = IntentClassificationError("Failed", detail="Model error")
        assert err.detail == "Model error"

    def test_validation_error_message(self) -> None:
        err = IntentValidationError("Invalid input")
        assert err.message == "Invalid input"


class TestIntentExtendedTypes:
    def test_new_intent_types_exist(self) -> None:
        assert IntentType.MEETING_SCHEDULE.value == "meeting_schedule"
        assert IntentType.MEETING_RESCHEDULE.value == "meeting_reschedule"
        assert IntentType.MEETING_CANCEL.value == "meeting_cancel"
        assert IntentType.GENERAL_CONVERSATION.value == "general_conversation"
        assert IntentType.QUESTION_ANSWERING.value == "question_answering"
        assert IntentType.LEAD_QUALIFICATION.value == "lead_qualification"
        assert IntentType.REMINDER.value == "reminder"
        assert IntentType.TASK_CREATION.value == "task_creation"
        assert IntentType.INFORMATION_COLLECTION.value == "information_collection"
        assert IntentType.WORKFLOW_TRIGGER.value == "workflow_trigger"
        assert IntentType.FALLBACK.value == "fallback"

    def test_all_intents_unique(self) -> None:
        values = [i.value for i in IntentType]
        assert len(values) == len(set(values))
