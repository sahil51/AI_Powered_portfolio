import pytest

from application.meeting.agent import MeetingAgent
from application.meeting.exceptions import MeetingAgentError
from application.meeting.health import MeetingHealthChecker, MeetingHealthStatus
from application.meeting.metrics import MeetingMetricsCollector
from application.meeting.models import MeetingContext
from application.meeting.statistics import MeetingApplicationStatistics
from domain.meeting.aggregate import Meeting
from domain.meeting.factory import MeetingFactory
from domain.meeting.policies import MeetingPolicies
from domain.meeting.state import (
    IllegalMeetingTransitionError,
    MeetingStateMachine,
    MeetingStatus,
)
from domain.meeting.validator import MeetingValidationError
from domain.meeting.value_objects import (
    MeetingField,
    MeetingFieldStatus,
    MeetingId,
)


class TestMeetingDomain:
    def test_meeting_id_generation(self) -> None:
        mid1 = MeetingId()
        mid2 = MeetingId()
        assert mid1 != mid2
        assert str(mid1) == mid1.value

    def test_meeting_id_equality(self) -> None:
        mid1 = MeetingId()
        mid2 = MeetingId()
        mid1b = MeetingId()
        object.__setattr__(mid1b, "value", mid1.value)
        assert mid1 == mid1b
        assert mid1 != mid2

    def test_meeting_field_defaults(self) -> None:
        field = MeetingField(name="title")
        assert field.name == "title"
        assert field.value is None
        assert field.status == MeetingFieldStatus.PENDING
        assert field.required is True
        assert field.is_collected is False

    def test_meeting_field_collected_status(self) -> None:
        field = MeetingField(name="date", value="2026-07-15", status=MeetingFieldStatus.COLLECTED)
        assert field.is_collected is True

    def test_state_machine_initial_state(self) -> None:
        sm = MeetingStateMachine()
        assert sm.current_state == MeetingStatus.CREATED

    def test_state_machine_valid_transition(self) -> None:
        sm = MeetingStateMachine()
        sm.transition_to(MeetingStatus.COLLECTING_INFORMATION)
        assert sm.current_state == MeetingStatus.COLLECTING_INFORMATION

    def test_state_machine_invalid_transition(self) -> None:
        sm = MeetingStateMachine()
        with pytest.raises(IllegalMeetingTransitionError):
            sm.transition_to(MeetingStatus.SUBMITTED)

    def test_state_machine_is_terminal(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.ARCHIVED)
        assert sm.is_terminal() is True

    def test_state_machine_is_active(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.COLLECTING_INFORMATION)
        assert sm.is_active() is True
        sm2 = MeetingStateMachine(MeetingStatus.COMPLETED)
        assert sm2.is_active() is False

    def test_can_collect(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.CREATED)
        assert sm.can_collect() is True
        sm2 = MeetingStateMachine(MeetingStatus.READY)
        assert sm2.can_collect() is False

    def test_full_lifecycle(self) -> None:
        sm = MeetingStateMachine()
        assert sm.current_state == MeetingStatus.CREATED
        sm.transition_to(MeetingStatus.COLLECTING_INFORMATION)
        sm.transition_to(MeetingStatus.WAITING_CONFIRMATION)
        sm.transition_to(MeetingStatus.READY)
        sm.transition_to(MeetingStatus.SUBMITTED)
        sm.transition_to(MeetingStatus.COMPLETED)
        sm.transition_to(MeetingStatus.ARCHIVED)
        assert sm.is_terminal()

    def test_cancel_from_collecting(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.COLLECTING_INFORMATION)
        sm.transition_to(MeetingStatus.CANCELLED)
        assert sm.current_state == MeetingStatus.CANCELLED

    def test_fail_from_collecting(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.COLLECTING_INFORMATION)
        sm.transition_to(MeetingStatus.FAILED)
        assert sm.current_state == MeetingStatus.FAILED

    def test_recover_from_failed(self) -> None:
        sm = MeetingStateMachine(MeetingStatus.FAILED)
        sm.transition_to(MeetingStatus.COLLECTING_INFORMATION)
        assert sm.current_state == MeetingStatus.COLLECTING_INFORMATION


class TestMeetingFactory:
    def setup_method(self) -> None:
        self.factory = MeetingFactory()

    def test_create_meeting(self) -> None:
        meeting = self.factory.create(title="Test Meeting", user_id="user1")
        assert meeting.title == "Test Meeting"
        assert meeting.user_id == "user1"
        assert meeting.status == MeetingStatus.CREATED
        assert len(meeting.fields) > 0

    def test_create_meeting_with_fields(self) -> None:
        meeting = self.factory.create(title="Test")
        field_names = [f.name for f in meeting.fields]
        assert "title" in field_names
        assert "date" in field_names
        assert "time" in field_names

    def test_create_empty_title_raises_error(self) -> None:
        with pytest.raises(MeetingValidationError, match="title is required"):
            self.factory.create(title="")

    def test_restore_meeting(self) -> None:
        meeting = self.factory.restore(
            meeting_id="restored-id",
            title="Restored Meeting",
            user_id="user1",
            status="collecting_information",
        )
        assert meeting.title == "Restored Meeting"
        assert meeting.status == MeetingStatus.COLLECTING_INFORMATION
        assert str(meeting.meeting_id) == "restored-id"

    def test_restore_with_fields(self) -> None:
        fields = [
            {"name": "title", "value": "Test", "status": "collected", "required": True, "order": 0, "label": "Title"},
        ]
        meeting = self.factory.restore(meeting_id="id1", title="Test", fields=fields)
        assert len(meeting.fields) == 1
        assert meeting.fields[0].name == "title"
        assert meeting.fields[0].value == "Test"


class TestMeetingAggregate:
    def setup_method(self) -> None:
        self.factory = MeetingFactory()

    def test_start_collecting(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        assert meeting.status == MeetingStatus.COLLECTING_INFORMATION

    def test_collect_field(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.collect_field("title", "My Meeting")
        assert meeting.collected_fields.get("title") == "My Meeting"

    def test_missing_fields(self) -> None:
        meeting = self.factory.create(title="Test", policies=MeetingPolicies(required_fields=["title", "date"]))
        meeting.start_collecting()
        assert "title" in meeting.missing_field_names
        assert "date" in meeting.missing_field_names

    def test_request_confirmation(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.request_confirmation()
        assert meeting.status == MeetingStatus.WAITING_CONFIRMATION

    def test_confirm(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        for f in meeting.fields:
            if f.required:
                meeting.collect_field(f.name, "value")
        meeting.request_confirmation()
        meeting.confirm()
        assert meeting.status == MeetingStatus.READY

    def test_cancel(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.cancel("Changed mind")
        assert meeting.status == MeetingStatus.CANCELLED

    def test_fail(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.fail("Something went wrong")
        assert meeting.status == MeetingStatus.FAILED
        assert meeting.error == "Something went wrong"

    def test_submit(self) -> None:
        meeting = self._build_ready_meeting()
        meeting.submit("wf-123")
        assert meeting.status == MeetingStatus.SUBMITTED
        assert meeting.workflow_id == "wf-123"

    def test_complete(self) -> None:
        meeting = self._build_ready_meeting()
        meeting.submit("wf-123")
        meeting.complete("Success")
        assert meeting.status == MeetingStatus.COMPLETED

    def test_ready_for_workflow(self) -> None:
        meeting = self._build_ready_meeting()
        assert meeting.ready_for_workflow is True

    def test_not_ready_for_workflow(self) -> None:
        meeting = self.factory.create(title="Test")
        assert meeting.ready_for_workflow is False

    def test_next_field(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        nf = meeting.next_field
        assert nf is not None
        assert nf.name == meeting.fields[0].name

    def test_correct_field(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.collect_field("title", "Original")
        meeting.correct_field("title", "Corrected")
        assert meeting.collected_fields.get("title") == "Corrected"

    def test_drain_events(self) -> None:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        meeting.collect_field("title", "Value")
        events = meeting.drain_events()
        assert len(events) >= 2

    def _build_ready_meeting(self) -> Meeting:
        meeting = self.factory.create(title="Test")
        meeting.start_collecting()
        for f in meeting.fields:
            if f.required:
                meeting.collect_field(f.name, "value")
        meeting.request_confirmation()
        meeting.confirm()
        return meeting


class TestMeetingMetrics:
    def setup_method(self) -> None:
        self.collector = MeetingMetricsCollector()

    def test_initial_metrics(self) -> None:
        assert self.collector.metrics.total_meetings == 0

    def test_record_meeting_created(self) -> None:
        self.collector.record_meeting_created()
        assert self.collector.metrics.total_meetings == 1

    def test_record_field_collected(self) -> None:
        self.collector.record_field_collected()
        assert self.collector.metrics.total_fields_collected == 1

    def test_record_latency(self) -> None:
        self.collector.record_latency(100.0)
        assert self.collector.metrics.avg_latency_ms == 100.0

    def test_record_correction(self) -> None:
        self.collector.record_correction()
        assert self.collector.metrics.correction_count == 1

    def test_reset(self) -> None:
        self.collector.record_meeting_created()
        self.collector.reset()
        assert self.collector.metrics.total_meetings == 0


class TestMeetingHealth:
    def setup_method(self) -> None:
        self.checker = MeetingHealthChecker()

    @pytest.mark.asyncio
    async def test_healthy_no_metrics(self) -> None:
        health = await self.checker.check()
        assert health.status == MeetingHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthy_good_metrics(self) -> None:
        metrics = MeetingMetricsCollector()
        metrics.record_meeting_created()
        metrics.record_meeting_completed()
        health = await self.checker.check(metrics.metrics)
        assert health.status == MeetingHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_degraded_high_latency(self) -> None:
        checker = MeetingHealthChecker(max_avg_latency_ms=100.0)
        metrics = MeetingMetricsCollector()
        metrics.record_meeting_created()
        metrics.record_latency(500.0)
        health = await checker.check(metrics.metrics)
        assert health.status == MeetingHealthStatus.DEGRADED


class TestMeetingStatistics:
    def setup_method(self) -> None:
        self.stats = MeetingApplicationStatistics()

    def test_record_created(self) -> None:
        self.stats.record_meeting_created("user1")
        assert self.stats.data.total_meetings == 1
        assert self.stats.data.by_status.get("created") == 1

    def test_record_field_collected(self) -> None:
        self.stats.record_meeting_created("user1")
        self.stats.record_field_collected()
        assert self.stats.data.total_fields_collected == 1

    def test_unique_users(self) -> None:
        self.stats.record_meeting_created("user1")
        self.stats.record_meeting_created("user2")
        assert self.stats.data.total_meetings == 2
        assert len(self.stats.data.unique_users) == 2


class TestMeetingAgent:
    def setup_method(self) -> None:
        self.agent = MeetingAgent()

    @pytest.mark.asyncio
    async def test_start_meeting(self) -> None:
        ctx = MeetingContext(user_id="u1", conversation_id="c1", session_id="s1")
        result = await self.agent.start_meeting(ctx)
        assert result.meeting_id
        assert result.status in (MeetingStatus.CREATED, MeetingStatus.COLLECTING_INFORMATION)
        assert result.title == "Untitled Meeting"

    @pytest.mark.asyncio
    async def test_start_meeting_with_title(self) -> None:
        ctx = MeetingContext(user_id="u1", conversation_id="c1", session_id="s1", entities={"title": "My Meeting"})
        result = await self.agent.start_meeting(ctx)
        assert result.title == "My Meeting"

    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        ctx = MeetingContext(user_id="u1", conversation_id="c1", session_id="s1")
        result = await self.agent.start_meeting(ctx)
        status = await self.agent.get_status(result.meeting_id)
        assert status.meeting_id == result.meeting_id

    @pytest.mark.asyncio
    async def test_cancel_meeting(self) -> None:
        ctx = MeetingContext(user_id="u1", conversation_id="c1", session_id="s1")
        result = await self.agent.start_meeting(ctx)
        cancelled = await self.agent.cancel_meeting(result.meeting_id, "Test cancel")
        assert cancelled.status == MeetingStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_process_message_cancel(self) -> None:
        ctx = MeetingContext(user_id="u1", conversation_id="c1", session_id="s1")
        result = await self.agent.start_meeting(ctx)
        updated = await self.agent.process_message(result.meeting_id, "cancel", ctx)
        assert updated.status == MeetingStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_status_not_found(self) -> None:
        with pytest.raises(MeetingAgentError, match="not found"):
            await self.agent.get_status("nonexistent")
