from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain.enums.confirmation import ConfirmationType
from domain.enums.intent import IntentType


@dataclass
class ConfirmationPolicy:
    require_all_fields_for_ready: bool = False
    enable_context_resolution: bool = True
    enable_memory_integration: bool = True
    max_clarification_rounds: int = 3
    ambiguous_retry_count: int = 1
    default_agent_intents: set[IntentType] = field(default_factory=lambda: {
        IntentType.MEETING_SCHEDULE,
        IntentType.MEETING_RESCHEDULE,
        IntentType.MEETING_CANCEL,
        IntentType.LEAD_QUALIFICATION,
        IntentType.TASK_CREATION,
        IntentType.WORKFLOW_TRIGGER,
    })
    ready_confirmation_types: set[ConfirmationType] = field(default_factory=lambda: {
        ConfirmationType.POSITIVE,
        ConfirmationType.CORRECTION,
    })
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_ready_for_agent(self, confirmation_type: ConfirmationType, intent: IntentType | None) -> bool:
        if confirmation_type in self.ready_confirmation_types:
            return True
        if confirmation_type == ConfirmationType.PARTIAL and intent in self.default_agent_intents:
            return True
        return False


def default_confirmation_policy() -> ConfirmationPolicy:
    return ConfirmationPolicy()
