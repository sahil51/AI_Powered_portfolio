import pytest

from application.confirmation.exceptions import (
    ConfirmationConfigurationError,
    ConfirmationEngineError,
    ConfirmationResolutionError,
    ConfirmationValidationError,
)
from application.confirmation.health import ConfirmationHealthChecker, ConfirmationHealthStatus
from application.confirmation.metrics import ConfirmationMetricsCollector
from application.confirmation.models import (
    ConfirmationContext,
    ConfirmationMetadata,
    ConfirmationResult,
)
from application.confirmation.policies import default_confirmation_policy
from application.confirmation.validator import ConfirmationValidator
from domain.enums.confirmation import ConfirmationType
from domain.enums.intent import IntentType


class TestConfirmationModels:
    def test_confirmation_context_defaults(self) -> None:
        ctx = ConfirmationContext(
            user_id="u1",
            session_id="s1",
            conversation_id="c1",
            user_reply="Yes please",
        )
        assert ctx.user_id == "u1"
        assert ctx.user_reply == "Yes please"
        assert ctx.pending_fields == []
        assert ctx.pending_questions == []
        assert ctx.current_entities == {}

    def test_confirmation_context_with_all_fields(self) -> None:
        ctx = ConfirmationContext(
            user_id="u1",
            session_id="s1",
            conversation_id="c1",
            user_reply="Change the time to 3pm",
            current_intent=IntentType.MEETING_SCHEDULE,
            conversation_history=[{"role": "user", "content": "Schedule a meeting"}],
            pending_questions=["What time?"],
            pending_fields=["time"],
            current_entities={"date": "2026-07-15"},
        )
        assert ctx.current_intent == IntentType.MEETING_SCHEDULE
        assert ctx.pending_fields == ["time"]
        assert ctx.current_entities == {"date": "2026-07-15"}

    def test_confirmation_metadata_defaults(self) -> None:
        m = ConfirmationMetadata()
        assert m.latency_ms == 0.0
        assert m.model == ""

    def test_confirmation_metadata_with_values(self) -> None:
        m = ConfirmationMetadata(
            latency_ms=200.0,
            model="gpt-4",
            provider="openai",
            correlation_id="corr1",
        )
        assert m.latency_ms == 200.0
        assert m.model == "gpt-4"
        assert m.correlation_id == "corr1"

    def test_confirmation_result_positive(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.POSITIVE,
            confirmed=True,
            reason="User confirmed",
            ready_for_agent=True,
        )
        assert result.confirmation_type == ConfirmationType.POSITIVE
        assert result.confirmed is True
        assert result.ready_for_agent is True

    def test_confirmation_result_modification(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.MODIFICATION,
            confirmed=False,
            updated_entities={"time": "15:00"},
            reason="User requested time change",
            suggested_follow_up="Any other changes?",
        )
        assert result.confirmation_type == ConfirmationType.MODIFICATION
        assert result.updated_entities == {"time": "15:00"}
        assert result.confirmed is False

    def test_confirmation_result_cancellation(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.CANCELLATION,
            confirmed=False,
            reason="User cancelled",
            ready_for_agent=False,
        )
        assert result.confirmation_type == ConfirmationType.CANCELLATION
        assert result.ready_for_agent is False

    def test_confirmation_result_negative(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.NEGATIVE,
            confirmed=False,
            reason="User declined",
        )
        assert result.confirmed is False
        assert result.remaining_missing_fields == []

    def test_confirmation_result_partial(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.PARTIAL,
            confirmed=True,
            updated_entities={"date": "2026-07-16"},
            remaining_missing_fields=["time"],
            reason="User confirmed date but not time",
        )
        assert result.confirmed is True
        assert result.remaining_missing_fields == ["time"]

    def test_confirmation_result_correction(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.CORRECTION,
            confirmed=True,
            corrected_field="date",
            corrected_value="2026-07-17",
            reason="User corrected the date",
        )
        assert result.corrected_field == "date"
        assert result.corrected_value == "2026-07-17"

    def test_confirmation_result_ambiguous(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.AMBIGUOUS,
            confirmed=False,
            reason="Could not determine intent",
            suggested_follow_up="Please clarify",
        )
        assert result.confirmation_type == ConfirmationType.AMBIGUOUS

    def test_confirmation_result_unknown(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.UNKNOWN,
            confirmed=False,
            reason="Unparseable response",
        )
        assert result.confirmation_type == ConfirmationType.UNKNOWN


class TestConfirmationValidator:
    def setup_method(self) -> None:
        self.validator = ConfirmationValidator()

    def test_validate_valid_context(self) -> None:
        ctx = ConfirmationContext(
            user_id="u1", session_id="s1", conversation_id="c1", user_reply="Yes"
        )
        self.validator.validate_context(ctx)

    def test_validate_empty_reply_raises_error(self) -> None:
        ctx = ConfirmationContext(
            user_id="u1", session_id="s1", conversation_id="c1", user_reply=""
        )
        with pytest.raises(ConfirmationValidationError, match="cannot be empty"):
            self.validator.validate_context(ctx)

    def test_validate_missing_user_id_raises_error(self) -> None:
        ctx = ConfirmationContext(
            user_id="", session_id="s1", conversation_id="c1", user_reply="Yes"
        )
        with pytest.raises(ConfirmationValidationError, match="User ID is required"):
            self.validator.validate_context(ctx)

    def test_validate_missing_conversation_id_raises_error(self) -> None:
        ctx = ConfirmationContext(
            user_id="u1", session_id="s1", conversation_id="", user_reply="Yes"
        )
        with pytest.raises(ConfirmationValidationError, match="Conversation ID is required"):
            self.validator.validate_context(ctx)

    def test_validate_result_valid(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.POSITIVE,
            confirmed=True,
        )
        assert self.validator.validate_result(result) is True

    def test_validate_unknown_confirmed_raises_error(self) -> None:
        result = ConfirmationResult(
            confirmation_type=ConfirmationType.UNKNOWN,
            confirmed=True,
        )
        with pytest.raises(ConfirmationValidationError, match="cannot be marked as confirmed"):
            self.validator.validate_result(result)

    def test_is_valid_type(self) -> None:
        assert self.validator.is_valid_type("positive") is True
        assert self.validator.is_valid_type("negative") is True
        assert self.validator.is_valid_type("invalid") is False


class TestConfirmationPolicy:
    def setup_method(self) -> None:
        self.policy = default_confirmation_policy()

    def test_is_ready_for_agent_positive(self) -> None:
        assert self.policy.is_ready_for_agent(ConfirmationType.POSITIVE, None) is True

    def test_is_ready_for_agent_negative(self) -> None:
        assert self.policy.is_ready_for_agent(ConfirmationType.NEGATIVE, None) is False

    def test_is_ready_for_agent_correction(self) -> None:
        assert self.policy.is_ready_for_agent(ConfirmationType.CORRECTION, None) is True

    def test_is_ready_for_agent_partial_with_meeting(self) -> None:
        assert self.policy.is_ready_for_agent(
            ConfirmationType.PARTIAL, IntentType.MEETING_SCHEDULE
        ) is True

    def test_is_ready_for_agent_partial_no_intent(self) -> None:
        assert self.policy.is_ready_for_agent(ConfirmationType.PARTIAL, None) is False

    def test_is_ready_for_agent_cancellation(self) -> None:
        assert self.policy.is_ready_for_agent(ConfirmationType.CANCELLATION, None) is False

    def test_default_settings(self) -> None:
        assert self.policy.max_clarification_rounds == 3
        assert self.policy.ambiguous_retry_count == 1
        assert self.policy.enable_context_resolution is True


class TestConfirmationMetrics:
    def setup_method(self) -> None:
        self.collector = ConfirmationMetricsCollector()

    def test_initial_metrics(self) -> None:
        metrics = self.collector.metrics
        assert metrics.total_resolutions == 0
        assert metrics.successful_resolutions == 0

    def test_record_resolution(self) -> None:
        self.collector.record_resolution(ConfirmationType.POSITIVE, 100.0)
        metrics = self.collector.metrics
        assert metrics.total_resolutions == 1
        assert metrics.successful_resolutions == 1
        assert metrics.resolutions_by_type.get("positive") == 1

    def test_record_failed_resolution(self) -> None:
        self.collector.record_resolution(ConfirmationType.UNKNOWN, 50.0, success=False)
        metrics = self.collector.metrics
        assert metrics.total_resolutions == 1
        assert metrics.failed_resolutions == 1

    def test_ambiguity_tracking(self) -> None:
        self.collector.record_resolution(ConfirmationType.AMBIGUOUS, 100.0)
        self.collector.record_resolution(ConfirmationType.AMBIGUOUS, 150.0)
        assert self.collector.metrics.ambiguity_count == 2

    def test_correction_tracking(self) -> None:
        self.collector.record_resolution(ConfirmationType.CORRECTION, 80.0)
        assert self.collector.metrics.correction_count == 1

    def test_modification_tracking(self) -> None:
        self.collector.record_resolution(ConfirmationType.MODIFICATION, 90.0)
        assert self.collector.metrics.modification_count == 1

    def test_cancellation_tracking(self) -> None:
        self.collector.record_resolution(ConfirmationType.CANCELLATION, 60.0)
        assert self.collector.metrics.cancellation_count == 1

    def test_agent_readiness(self) -> None:
        self.collector.record_agent_readiness()
        assert self.collector.metrics.agent_readiness_count == 1

    def test_avg_latency(self) -> None:
        self.collector.record_resolution(ConfirmationType.POSITIVE, 100.0)
        self.collector.record_resolution(ConfirmationType.POSITIVE, 200.0)
        assert self.collector.metrics.avg_latency_ms == 150.0

    def test_reset(self) -> None:
        self.collector.record_resolution(ConfirmationType.POSITIVE, 100.0)
        self.collector.reset()
        assert self.collector.metrics.total_resolutions == 0


class TestConfirmationHealth:
    def setup_method(self) -> None:
        self.checker = ConfirmationHealthChecker()

    @pytest.mark.asyncio
    async def test_healthy_with_no_metrics(self) -> None:
        health = await self.checker.check()
        assert health.status == ConfirmationHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthy_with_good_metrics(self) -> None:
        metrics = ConfirmationMetricsCollector()
        metrics.record_resolution(ConfirmationType.POSITIVE, 100.0)
        metrics.record_resolution(ConfirmationType.POSITIVE, 200.0)
        health = await self.checker.check(metrics.metrics)
        assert health.status == ConfirmationHealthStatus.HEALTHY
        assert health.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_degraded_high_latency(self) -> None:
        checker = ConfirmationHealthChecker(max_avg_latency_ms=100.0)
        metrics = ConfirmationMetricsCollector()
        metrics.record_resolution(ConfirmationType.POSITIVE, 500.0)
        health = await checker.check(metrics.metrics)
        assert health.status == ConfirmationHealthStatus.DEGRADED
        assert len(health.errors) > 0

    @pytest.mark.asyncio
    async def test_degraded_low_success_rate(self) -> None:
        checker = ConfirmationHealthChecker(min_success_rate=0.9)
        metrics = ConfirmationMetricsCollector()
        metrics.record_resolution(ConfirmationType.POSITIVE, 100.0, success=True)
        metrics.record_resolution(ConfirmationType.UNKNOWN, 100.0, success=False)
        health = await checker.check(metrics.metrics)
        assert health.status == ConfirmationHealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_consecutive_errors_unhealthy(self) -> None:
        checker = ConfirmationHealthChecker(max_consecutive_errors=2)
        checker.record_error("err1")
        checker.record_error("err2")
        checker.record_error("err3")
        metrics = ConfirmationMetricsCollector()
        metrics.record_resolution(ConfirmationType.POSITIVE, 100.0)
        health = await checker.check(metrics.metrics)
        assert health.status == ConfirmationHealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_record_success_clears_errors(self) -> None:
        checker = ConfirmationHealthChecker(max_consecutive_errors=2)
        checker.record_error("err1")
        checker.record_success()
        metrics = ConfirmationMetricsCollector()
        metrics.record_resolution(ConfirmationType.POSITIVE, 100.0)
        health = await checker.check(metrics.metrics)
        assert health.status == ConfirmationHealthStatus.HEALTHY


class TestConfirmationTypes:
    def test_all_confirmation_types_exist(self) -> None:
        assert ConfirmationType.POSITIVE.value == "positive"
        assert ConfirmationType.NEGATIVE.value == "negative"
        assert ConfirmationType.PARTIAL.value == "partial"
        assert ConfirmationType.MODIFICATION.value == "modification"
        assert ConfirmationType.CORRECTION.value == "correction"
        assert ConfirmationType.CANCELLATION.value == "cancellation"
        assert ConfirmationType.AMBIGUOUS.value == "ambiguous"
        assert ConfirmationType.UNKNOWN.value == "unknown"

    def test_all_types_unique(self) -> None:
        values = [t.value for t in ConfirmationType]
        assert len(values) == len(set(values))


class TestConfirmationExceptions:
    def test_error_hierarchy(self) -> None:
        assert issubclass(ConfirmationResolutionError, ConfirmationEngineError)
        assert issubclass(ConfirmationValidationError, ConfirmationEngineError)
        assert issubclass(ConfirmationConfigurationError, ConfirmationEngineError)

    def test_error_with_detail(self) -> None:
        err = ConfirmationEngineError("Failed", detail="Something broke")
        assert err.detail == "Something broke"

    def test_resolution_error(self) -> None:
        err = ConfirmationResolutionError("Could not resolve")
        assert err.message == "Could not resolve"
