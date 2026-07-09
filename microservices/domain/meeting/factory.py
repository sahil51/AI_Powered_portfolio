from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.meeting.aggregate import Meeting
from domain.meeting.policies import MeetingPolicies, default_meeting_policies
from domain.meeting.state import MeetingStateMachine, MeetingStatus
from domain.meeting.validator import MeetingValidator
from domain.meeting.value_objects import (
    MeetingField,
    MeetingFieldStatus,
    MeetingId,
    MeetingMetadata,
)


class MeetingFactory:
    def __init__(self, validator: MeetingValidator | None = None) -> None:
        self._validator = validator or MeetingValidator()

    def create(
        self,
        title: str,
        user_id: str = "",
        conversation_id: str = "",
        session_id: str = "",
        policies: MeetingPolicies | None = None,
        correlation_id: str = "",
        metadata: MeetingMetadata | None = None,
        config: dict[str, Any] | None = None,
    ) -> Meeting:
        self._validator.validate_create(title)

        field_order = (policies or default_meeting_policies).get_collection_order()
        fields = [
            MeetingField(
                name=fname,
                required=(policies or default_meeting_policies).is_required(fname),
                order=idx,
                label=fname.replace("_", " ").title(),
            )
            for idx, fname in enumerate(field_order)
        ]

        return Meeting(
            meeting_id=MeetingId(),
            title=title,
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            fields=fields,
            state_machine=MeetingStateMachine(),
            policies=policies or default_meeting_policies,
            metadata=metadata or MeetingMetadata(),
            correlation_id=correlation_id,
            config=config or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def restore(
        self,
        meeting_id: str,
        title: str,
        user_id: str = "",
        conversation_id: str = "",
        session_id: str = "",
        status: str = "created",
        fields: list[dict[str, Any]] | None = None,
        policies: MeetingPolicies | None = None,
        correlation_id: str = "",
        metadata: MeetingMetadata | None = None,
        config: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        completed_at: datetime | None = None,
        workflow_id: str = "",
        error: str = "",
        version: int = 1,
    ) -> Meeting:
        mid = MeetingId()
        object.__setattr__(mid, "value", meeting_id)

        restored_fields: list[MeetingField] = []
        if fields:
            for f in fields:
                restored_fields.append(
                    MeetingField(
                        name=f.get("name", ""),
                        value=f.get("value"),
                        status=MeetingFieldStatus(f.get("status", "pending")),
                        required=f.get("required", True),
                        order=f.get("order", 0),
                        label=f.get("label", ""),
                        validation_error=f.get("validation_error"),
                    )
                )

        return Meeting(
            meeting_id=mid,
            title=title,
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            fields=restored_fields,
            state_machine=MeetingStateMachine(MeetingStatus(status)),
            policies=policies or default_meeting_policies,
            metadata=metadata or MeetingMetadata(),
            correlation_id=correlation_id,
            config=config or {},
            workflow_id=workflow_id,
            error=error,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
            completed_at=completed_at,
            version=version,
        )
