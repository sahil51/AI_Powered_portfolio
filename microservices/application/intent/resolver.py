from __future__ import annotations

from application.intent.interfaces import IntentResolverInterface
from application.intent.models import ExtractedEntity, IntentContext, IntentResult
from application.intent.policies import IntentPolicy
from domain.enums.intent import IntentType


class IntentResolver(IntentResolverInterface):
    def __init__(self, policy: IntentPolicy | None = None) -> None:
        self._policy = policy or IntentPolicy()

    async def resolve(self, result: IntentResult, context: IntentContext) -> IntentResult:
        if result.intent == IntentType.FALLBACK:
            return self._resolve_fallback(result, context)

        if result.intent == IntentType.UNKNOWN:
            return self._resolve_unknown(result, context)

        if result.confidence < self._policy.fallback_threshold:
            return self._resolve_low_confidence(result, context)

        if result.needs_confirmation or result.needs_clarification or self._policy.needs_confirmation(result.intent):
            result.missing_fields = self._determine_missing_fields(result)

        return result

    def _resolve_fallback(self, result: IntentResult, context: IntentContext) -> IntentResult:
        fallback_intent = self._detect_intent_from_context(context)
        if fallback_intent != IntentType.UNKNOWN:
            return IntentResult(
                intent=fallback_intent,
                confidence=result.confidence * 0.85,
                confidence_level=result.confidence_level,
                entities=result.entities,
                needs_confirmation=self._policy.needs_confirmation(fallback_intent),
                needs_clarification=False,
                missing_fields=self._determine_missing_fields_for_intent(fallback_intent, result.entities),
                suggested_agent=result.suggested_agent,
                workflow_hint=result.workflow_hint,
                metadata=result.metadata,
                raw_response=result.raw_response,
            )
        result.needs_clarification = True
        return result

    def _resolve_unknown(self, result: IntentResult, context: IntentContext) -> IntentResult:
        detected = self._detect_intent_from_context(context)
        if detected != IntentType.UNKNOWN:
            return IntentResult(
                intent=detected,
                confidence=0.55,
                confidence_level=result.confidence_level,
                entities=result.entities,
                needs_confirmation=True,
                needs_clarification=False,
                suggested_agent=result.suggested_agent,
                workflow_hint=result.workflow_hint,
                metadata=result.metadata,
                raw_response=result.raw_response,
            )
        result.needs_clarification = True
        return result

    def _resolve_low_confidence(self, result: IntentResult, context: IntentContext) -> IntentResult:
        context_intent = self._detect_intent_from_context(context)
        if context_intent != IntentType.UNKNOWN and context_intent != result.intent:
            return IntentResult(
                intent=context_intent,
                confidence=0.60,
                confidence_level=result.confidence_level,
                entities=result.entities,
                needs_confirmation=True,
                needs_clarification=False,
                suggested_agent=result.suggested_agent,
                workflow_hint=result.workflow_hint,
                metadata=result.metadata,
                raw_response=result.raw_response,
            )
        result.needs_clarification = True
        return result

    def _detect_intent_from_context(self, context: IntentContext) -> IntentType:
        if not context.conversation_history:
            return IntentType.UNKNOWN
        for msg in reversed(context.conversation_history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                for intent in IntentType:
                    if intent == IntentType.UNKNOWN:
                        continue
                    if intent.value in content:
                        return intent
        return IntentType.UNKNOWN

    def _determine_missing_fields_for_intent(self, intent: IntentType, entities: ExtractedEntity) -> list[str]:
        intent_fields: dict[IntentType, list[str]] = {
            IntentType.MEETING_SCHEDULE: ["date", "time", "duration", "participants"],
            IntentType.MEETING_RESCHEDULE: ["date", "time"],
            IntentType.MEETING_CANCEL: ["meeting_id"],
            IntentType.LEAD_QUALIFICATION: ["name", "company", "email", "phone"],
            IntentType.TASK_CREATION: ["title", "description", "priority"],
            IntentType.REMINDER: ["title", "date", "time"],
            IntentType.INFORMATION_COLLECTION: [],
            IntentType.WORKFLOW_TRIGGER: ["workflow_name", "parameters"],
        }
        baseline = intent_fields.get(intent, [])
        entity_map = {
            "date": entities.date,
            "time": entities.time,
            "duration": str(entities.duration) if entities.duration else None,
            "name": entities.person_name,
            "company": entities.company,
            "email": entities.email,
            "phone": entities.phone,
            "title": None,
            "description": None,
            "priority": entities.priority,
            "participants": entities.person_name,
            "meeting_id": None,
            "workflow_name": entities.workflow_parameters.get("name") if entities.workflow_parameters else None,
            "parameters": None,
        }
        missing = []
        for field in baseline:
            val = entity_map.get(field)
            if not val:
                missing.append(field)
        return missing

    def _determine_missing_fields(self, result: IntentResult) -> list[str]:
        return self._determine_missing_fields_for_intent(result.intent, result.entities)
