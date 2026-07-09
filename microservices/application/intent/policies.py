from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain.enums.intent import IntentType


@dataclass
class IntentPolicy:
    auto_accept_threshold: float = 0.85
    clarification_threshold: float = 0.60
    fallback_threshold: float = 0.30
    enable_entity_extraction: bool = True
    enable_context_resolution: bool = True
    enable_fallback_detection: bool = True
    require_confirmation_intents: set[IntentType] = field(default_factory=lambda: {
        IntentType.MEETING_SCHEDULE,
        IntentType.MEETING_RESCHEDULE,
        IntentType.MEETING_CANCEL,
        IntentType.LEAD_QUALIFICATION,
        IntentType.WORKFLOW_TRIGGER,
        IntentType.TASK_CREATION,
    })
    require_clarification_intents: set[IntentType] = field(default_factory=lambda: {
        IntentType.UNKNOWN,
        IntentType.FALLBACK,
    })
    auto_accept_intents: set[IntentType] = field(default_factory=lambda: {
        IntentType.GREETING,
        IntentType.GENERAL_CONVERSATION,
    })
    max_retries: int = 2
    timeout_seconds: float = 30.0
    confidence_lookup: dict[float, str] = field(default_factory=lambda: {
        0.85: "high",
        0.60: "medium",
        0.30: "low",
    })
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_confidence_label(self, score: float) -> str:
        if score >= self.auto_accept_threshold:
            return "high"
        if score >= self.clarification_threshold:
            return "medium"
        if score >= self.fallback_threshold:
            return "low"
        return "uncertain"

    def needs_confirmation(self, intent: IntentType) -> bool:
        return intent in self.require_confirmation_intents

    def needs_clarification(self, intent: IntentType) -> bool:
        return intent in self.require_clarification_intents or intent == IntentType.UNKNOWN

    def auto_accept(self, intent: IntentType) -> bool:
        return intent in self.auto_accept_intents


def default_intent_policy() -> IntentPolicy:
    return IntentPolicy()
