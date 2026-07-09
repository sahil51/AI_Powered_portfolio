from __future__ import annotations

import logging
import time
from typing import Any

from application.meeting.exceptions import (
    MeetingAgentError,
    MeetingCollectionError,
)
from application.meeting.interfaces import MeetingAgentInterface
from application.meeting.metrics import MeetingMetricsCollector
from application.meeting.models import MeetingContext, MeetingMetadata, MeetingResult
from application.meeting.policies import MeetingApplicationPolicies, default_meeting_application_policies
from application.meeting.statistics import MeetingApplicationStatistics
from application.meeting.validator import MeetingApplicationValidator
from domain.meeting.aggregate import Meeting
from domain.meeting.factory import MeetingFactory
from domain.meeting.policies import MeetingPolicies
from domain.meeting.state import MeetingStatus
from domain.meeting.validator import MeetingValidator as DomainMeetingValidator

logger = logging.getLogger("ai_assistant")

FIELD_ENTITY_MAP: dict[str, list[str]] = {
    "title": ["title", "meeting_title"],
    "attendee": ["person_name", "attendee", "participant", "name"],
    "date": ["date", "preferred_date", "day"],
    "time": ["time", "preferred_time", "start_time"],
    "timezone": ["timezone", "tz"],
    "duration": ["duration", "length"],
    "meeting_type": ["meeting_type", "type"],
    "location": ["location", "place", "address"],
    "agenda": ["agenda", "purpose", "description"],
    "organizer": ["organizer", "organizer_name"],
    "priority": ["priority"],
    "description": ["description", "notes", "additional_notes"],
}


class MeetingAgent(MeetingAgentInterface):
    def __init__(
        self,
        factory: MeetingFactory | None = None,
        domain_validator: DomainMeetingValidator | None = None,
        app_validator: MeetingApplicationValidator | None = None,
        policies: MeetingApplicationPolicies | None = None,
        domain_policies: MeetingPolicies | None = None,
        metrics_collector: MeetingMetricsCollector | None = None,
        statistics: MeetingApplicationStatistics | None = None,
    ) -> None:
        self._factory = factory or MeetingFactory()
        self._domain_validator = domain_validator or DomainMeetingValidator()
        self._app_validator = app_validator or MeetingApplicationValidator()
        self._policies = policies or default_meeting_application_policies()
        self._domain_policies = domain_policies
        self._metrics = metrics_collector or MeetingMetricsCollector()
        self._statistics = statistics or MeetingApplicationStatistics()
        self._meetings: dict[str, Meeting] = {}

    async def start_meeting(self, context: MeetingContext) -> MeetingResult:
        self._app_validator.validate_context(context)
        start = time.time()

        meeting = self._factory.create(
            title=self._extract_title(context),
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            session_id=context.session_id,
            policies=self._domain_policies,
            correlation_id=context.correlation_id,
        )

        if self._policies.auto_start_collection:
            meeting.start_collecting()
            self._apply_entities(meeting, context)

        self._meetings[str(meeting.meeting_id)] = meeting
        self._metrics.record_meeting_created()
        self._statistics.record_meeting_created(context.user_id)
        self._metrics.record_latency((time.time() - start) * 1000)

        return self._build_result(meeting)

    async def process_message(
        self, meeting_id: str, message: str, context: MeetingContext
    ) -> MeetingResult:
        start = time.time()
        meeting = self._get_meeting(meeting_id)

        if message.lower() in ("cancel", "cancel it", "never mind", "forget it", "stop"):
            meeting.cancel("User requested cancellation")
            self._metrics.record_meeting_cancelled()
            self._metrics.record_latency((time.time() - start) * 1000)
            return self._build_result(meeting, message="Meeting cancelled")

        if meeting.status == MeetingStatus.CANCELLED:
            return self._build_result(
                meeting, error="Meeting is already cancelled"
            )

        if meeting.status == MeetingStatus.COMPLETED:
            return self._build_result(
                meeting, error="Meeting is already completed"
            )

        if message.lower().startswith("change ") or message.lower().startswith("modify "):
            return await self._handle_correction(meeting, message, context)

        if self._is_reschedule_request(message):
            return await self._handle_reschedule(meeting, message, context)

        if meeting.status in (MeetingStatus.CREATED, MeetingStatus.COLLECTING_INFORMATION):
            self._process_field_update(meeting, message, context)
            self._metrics.record_field_collected()
            self._statistics.record_field_collected()

        if meeting.status == MeetingStatus.WAITING_CONFIRMATION:
            self._process_confirmation(meeting, context)

        if meeting.ready_for_workflow and self._policies.require_confirmation_before_submit:
            if meeting.status != MeetingStatus.WAITING_CONFIRMATION:
                meeting.request_confirmation()

        self._metrics.record_latency((time.time() - start) * 1000)
        return self._build_result(meeting)

    async def get_status(self, meeting_id: str) -> MeetingResult:
        meeting = self._get_meeting(meeting_id)
        return self._build_result(meeting)

    async def cancel_meeting(self, meeting_id: str, reason: str = "") -> MeetingResult:
        meeting = self._get_meeting(meeting_id)
        meeting.cancel(reason or "Cancelled by user")
        self._metrics.record_meeting_cancelled()
        return self._build_result(meeting, message="Meeting cancelled")

    async def _handle_correction(
        self, meeting: Meeting, message: str, context: MeetingContext
    ) -> MeetingResult:
        if not self._policies.enable_correction:
            raise MeetingCollectionError("Corrections are disabled")

        field_name = self._detect_correction_field(message)
        field_value = self._extract_correction_value(message)
        if field_name and field_value:
            meeting.correct_field(field_name, field_value)
            self._metrics.record_correction()
            self._statistics.record_correction()
            if meeting.status in (MeetingStatus.READY, MeetingStatus.WAITING_CONFIRMATION):
                meeting.resume_collecting()
        return self._build_result(
            meeting,
            message=f"Corrected {field_name} to {field_value}" if field_name else "Processing correction",
        )

    async def _handle_reschedule(
        self, meeting: Meeting, message: str, context: MeetingContext
    ) -> MeetingResult:
        if not self._policies.enable_reschedule:
            raise MeetingCollectionError("Rescheduling is disabled")

        meeting.resume_collecting()
        self._apply_entities(meeting, context)
        self._metrics.record_reschedule()
        self._statistics.record_reschedule()
        return self._build_result(meeting, message="Rescheduling meeting")

    def _get_meeting(self, meeting_id: str) -> Meeting:
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            raise MeetingAgentError(f"Meeting not found: {meeting_id}")
        return meeting

    def _process_field_update(
        self, meeting: Meeting, message: str, context: MeetingContext
    ) -> None:
        self._domain_validator.validate_field_collection(meeting)
        self._apply_entities(meeting, context)

        next_f = meeting.next_field
        if next_f and not next_f.is_collected:
            extracted = self._extract_field_from_message(message, next_f.name)
            if extracted:
                meeting.collect_field(next_f.name, extracted)

        if meeting.missing_fields:
            next_field = meeting.next_field
            if next_field and meeting.status == MeetingStatus.COLLECTING_INFORMATION:
                pass
        elif meeting.status == MeetingStatus.COLLECTING_INFORMATION:
            meeting.request_confirmation()

    def _process_confirmation(self, meeting: Meeting, context: MeetingContext) -> None:
        confirmation = context.confirmation_type.lower() if context.confirmation_type else ""
        if confirmation in ("positive", "correction"):
            meeting.confirm()
        elif confirmation == "modification":
            self._apply_entities(meeting, context)
        elif confirmation == "cancellation":
            meeting.cancel("User cancelled during confirmation")

    def _apply_entities(self, meeting: Meeting, context: MeetingContext) -> None:
        for field_name, entity_keys in FIELD_ENTITY_MAP.items():
            if any(f.name == field_name and f.is_collected for f in meeting.fields):
                continue
            for key in entity_keys:
                value = context.entities.get(key)
                if value:
                    meeting.collect_field(field_name, str(value))
                    break

    def _extract_field_from_message(self, message: str, field_name: str) -> str | None:
        if field_name == "title":
            return message.strip()[:100]
        if field_name == "attendee":
            return message.strip()
        return None

    def _extract_title(self, context: MeetingContext) -> str:
        title = context.entities.get("title") or context.entities.get("meeting_title")
        if title:
            return str(title)
        if context.intent:
            intent_label = context.intent.replace("_", " ").title()
            return f"{intent_label} Discussion"
        return "Untitled Meeting"

    def _detect_correction_field(self, message: str) -> str | None:
        lowered = message.lower()
        for field_name, labels in FIELD_ENTITY_MAP.items():
            for label in labels:
                if label.lower() in lowered:
                    return field_name
        return None

    def _extract_correction_value(self, message: str) -> str | None:
        parts = message.split("to", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return None

    def _is_reschedule_request(self, message: str) -> bool:
        lowered = message.lower()
        keywords = [
            "reschedule", "rescheduling", "change date", "change time",
            "different day", "different time", "next week", "next monday",
            "next tuesday", "next month",
        ]
        return any(k in lowered for k in keywords)

    def _build_result(
        self, meeting: Meeting, message: str = "", error: str | None = None
    ) -> MeetingResult:
        metadata = MeetingMetadata(
            latency_ms=0.0,
            correlation_id=meeting.correlation_id,
        )
        return MeetingResult(
            meeting_id=str(meeting.meeting_id),
            status=meeting.status,
            title=meeting.title,
            collected_fields=meeting.collected_fields,
            missing_fields=meeting.missing_field_names,
            next_field=meeting.next_field.label if meeting.next_field else None,
            ready_for_workflow=meeting.ready_for_workflow,
            needs_confirmation=meeting.status == MeetingStatus.WAITING_CONFIRMATION,
            needs_clarification=len(meeting.missing_fields) > 0 and meeting.status not in (
                MeetingStatus.COMPLETED,
                MeetingStatus.CANCELLED,
                MeetingStatus.ARCHIVED,
            ),
            workflow_request=self._build_workflow_request(meeting) if meeting.ready_for_workflow else None,
            message=message or self._build_status_message(meeting),
            error=error,
            metadata=metadata,
        )

    def _build_status_message(self, meeting: Meeting) -> str:
        if meeting.status == MeetingStatus.CREATED:
            return "Meeting session created"
        if meeting.status == MeetingStatus.COLLECTING_INFORMATION:
            next_f = meeting.next_field
            if next_f:
                return f"Please provide the {next_f.label.lower()}"
            return "Collecting meeting information"
        if meeting.status == MeetingStatus.WAITING_CONFIRMATION:
            return "Please confirm the meeting details"
        if meeting.status == MeetingStatus.READY:
            return "Meeting details are complete and ready"
        if meeting.status == MeetingStatus.COMPLETED:
            return "Meeting has been completed"
        if meeting.status == MeetingStatus.CANCELLED:
            return "Meeting has been cancelled"
        if meeting.status == MeetingStatus.FAILED:
            return f"Meeting failed: {meeting.error}"
        return f"Meeting status: {meeting.status.value}"

    def _build_workflow_request(self, meeting: Meeting) -> dict[str, Any]:
        return {
            "meeting_id": str(meeting.meeting_id),
            "title": meeting.title,
            **meeting.collected_fields,
            "metadata": {
                "user_id": meeting.user_id,
                "conversation_id": meeting.conversation_id,
                "session_id": meeting.session_id,
                "correlation_id": meeting.correlation_id,
            },
        }
