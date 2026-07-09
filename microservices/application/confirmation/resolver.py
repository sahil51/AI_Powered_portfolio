from __future__ import annotations

import json
import logging
import time
from typing import Any

from application.confirmation.exceptions import ConfirmationResolutionError
from application.confirmation.interfaces import ConfirmationResolverInterface
from application.confirmation.models import (
    ConfirmationContext,
    ConfirmationMetadata,
    ConfirmationResult,
)
from application.confirmation.policies import ConfirmationPolicy
from application.pipeline.models import PipelineContext
from application.pipeline.pipeline import AIResponsePipeline
from domain.enums.confirmation import ConfirmationType
from domain.enums.intent import IntentType

logger = logging.getLogger("ai_assistant")


class ConfirmationResolver(ConfirmationResolverInterface):
    def __init__(
        self,
        pipeline: AIResponsePipeline,
        policy: ConfirmationPolicy | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._policy = policy or ConfirmationPolicy()

    async def resolve(self, context: ConfirmationContext) -> ConfirmationResult:
        start = time.time()

        pipeline_result = await self._run_resolution(context)
        latency_ms = (time.time() - start) * 1000

        parsed = self._parse_response(pipeline_result.content)
        confirmation_type = self._resolve_confirmation_type(parsed, context)

        updated_entities = self._build_updated_entities(parsed, context)
        remaining_fields = self._determine_remaining_fields(parsed, context)

        confirmed = confirmation_type in (
            ConfirmationType.POSITIVE,
            ConfirmationType.PARTIAL,
            ConfirmationType.CORRECTION,
        )
        ready = self._policy.is_ready_for_agent(confirmation_type, context.current_intent)

        metadata = ConfirmationMetadata(
            latency_ms=latency_ms,
            model=pipeline_result.model,
            provider=pipeline_result.provider,
            prompt_version="1.0.0",
            correlation_id=pipeline_result.correlation_id,
            trace_id=pipeline_result.trace_id,
        )

        return ConfirmationResult(
            confirmation_type=confirmation_type,
            confirmed=confirmed,
            updated_entities=updated_entities,
            remaining_missing_fields=remaining_fields,
            corrected_field=parsed.get("corrected_field"),
            corrected_value=parsed.get("corrected_value"),
            reason=parsed.get("reason", ""),
            suggested_follow_up=parsed.get("suggested_follow_up", ""),
            ready_for_agent=ready,
            workflow_hint=self._resolve_workflow_hint(confirmation_type, context),
            metadata=metadata,
            raw_response=pipeline_result.content,
        )

    async def _run_resolution(self, context: ConfirmationContext) -> Any:
        ctx = self._build_pipeline_context(context)
        try:
            return await self._pipeline.orchestrate(ctx)
        except Exception as e:
            raise ConfirmationResolutionError(
                f"Confirmation resolution pipeline failed: {e}",
                detail=str(e),
            )

    def _build_pipeline_context(self, context: ConfirmationContext) -> PipelineContext:
        history_str = self._build_history_string(context)
        pending_q = ", ".join(context.pending_questions) if context.pending_questions else "None"
        pending_f = ", ".join(context.pending_fields) if context.pending_fields else "None"
        intent_str = context.current_intent.value if context.current_intent else "unknown"

        return PipelineContext(
            conversation_id=context.conversation_id,
            user_id=context.user_id,
            session_id=context.session_id,
            prompt_category="classification",
            prompt_name="classification.confirmation_resolution",
            prompt_version="1.0.0",
            prompt_variables={
                "conversation_history": history_str,
                "current_intent": intent_str,
                "pending_questions": pending_q,
                "pending_fields": pending_f,
                "user_reply": context.user_reply,
            },
            temperature=0.1,
            correlation_id=context.metadata.get("correlation_id"),
            trace_id=context.metadata.get("trace_id"),
        )

    def _build_history_string(self, context: ConfirmationContext) -> str:
        parts: list[str] = []
        for msg in context.conversation_history[-8:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts) if parts else "No prior conversation"

    def _parse_response(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                return json.loads(content[start:end])
            except (ValueError, json.JSONDecodeError):
                return self._heuristic_parse(content)

    def _heuristic_parse(self, content: str) -> dict[str, Any]:
        cleaned = content.strip().lower()
        if cleaned in ("yes", "okay", "proceed", "correct", "confirmed", "sure"):
            return {"confirmation_type": "positive", "reason": "User gave affirmative response"}
        if cleaned in ("no", "nope", "cancel", "stop", "never mind", "forget it"):
            return {"confirmation_type": "negative", "reason": "User gave negative response"}
        if "change" in cleaned or "modify" in cleaned or "edit" in cleaned:
            return {"confirmation_type": "modification", "reason": "User requested changes"}
        return {
            "confirmation_type": "ambiguous",
            "reason": "Could not parse structured response",
            "suggested_follow_up": "Could you please clarify your response?",
        }

    def _resolve_confirmation_type(
        self, parsed: dict[str, Any], context: ConfirmationContext
    ) -> ConfirmationType:
        raw_type = parsed.get("confirmation_type", "ambiguous")
        try:
            return ConfirmationType(raw_type)
        except ValueError:
            return ConfirmationType.AMBIGUOUS

    def _build_updated_entities(
        self, parsed: dict[str, Any], context: ConfirmationContext
    ) -> dict[str, Any]:
        modified = parsed.get("modified_fields", {})
        if isinstance(modified, dict):
            entities = dict(context.current_entities)
            entities.update(modified)
            return entities
        return dict(context.current_entities)

    def _determine_remaining_fields(
        self, parsed: dict[str, Any], context: ConfirmationContext
    ) -> list[str]:
        missing = parsed.get("missing_fields", [])
        if isinstance(missing, list):
            return [str(f) for f in missing]
        if context.pending_fields:
            confirmed = parsed.get("confirmed_fields", [])
            if isinstance(confirmed, list):
                return [f for f in context.pending_fields if f not in confirmed]
        return context.pending_fields

    def _resolve_workflow_hint(
        self, confirmation_type: ConfirmationType, context: ConfirmationContext
    ) -> str | None:
        if context.current_intent and self._policy.is_ready_for_agent(
            confirmation_type, context.current_intent
        ):
            hint_map: dict[IntentType, str] = {
                IntentType.MEETING_SCHEDULE: "schedule_meeting",
                IntentType.MEETING_RESCHEDULE: "reschedule_meeting",
                IntentType.MEETING_CANCEL: "cancel_meeting",
                IntentType.LEAD_QUALIFICATION: "qualify_lead",
                IntentType.TASK_CREATION: "create_task",
                IntentType.WORKFLOW_TRIGGER: "trigger_workflow",
            }
            return hint_map.get(context.current_intent)
        return None
