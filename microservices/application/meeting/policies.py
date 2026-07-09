from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain.meeting.policies import MeetingPolicies, default_meeting_policies


@dataclass
class MeetingApplicationPolicies:
    domain_policies: MeetingPolicies = field(default_factory=lambda: default_meeting_policies)
    auto_start_collection: bool = True
    require_confirmation_before_submit: bool = True
    enable_entity_extraction: bool = True
    enable_correction: bool = True
    enable_reschedule: bool = True
    enable_cancellation: bool = True
    max_collection_attempts: int = 15
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def required_fields(self) -> list[str]:
        return self.domain_policies.required_fields

    @property
    def optional_fields(self) -> list[str]:
        return self.domain_policies.optional_fields

    @property
    def field_collection_order(self) -> list[str]:
        return self.domain_policies.get_collection_order()


def default_meeting_application_policies() -> MeetingApplicationPolicies:
    return MeetingApplicationPolicies()
