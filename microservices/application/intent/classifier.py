from __future__ import annotations

import json
import logging
import time
from typing import Any

from application.intent.exceptions import IntentClassificationError
from application.intent.interfaces import IntentClassifierInterface
from application.intent.models import (
    ConfidenceLevel,
    ExtractedEntity,
    IntentContext,
    IntentMetadata,
    IntentRequest,
    IntentResult,
)
from application.intent.policies import IntentPolicy
from application.pipeline.models import PipelineContext, PipelineResult
from application.pipeline.pipeline import AIResponsePipeline
from application.prompts.registry import PromptRegistry
from domain.enums.intent import IntentType

logger = logging.getLogger("ai_assistant")


class IntentClassifier(IntentClassifierInterface):
    def __init__(
        self,
        pipeline: AIResponsePipeline,
        prompt_registry: PromptRegistry,
        policy: IntentPolicy | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._prompt_registry = prompt_registry
        self._policy = policy or IntentPolicy()

    async def classify(self, request: IntentRequest) -> IntentResult:
        start = time.time()
        context = request.context
        self._validate_context(context)

        classification_result = await self._run_classification(request)
        latency_ms = (time.time() - start) * 1000

        intent = self._parse_intent(classification_result.content)
        confidence = self._calculate_confidence(classification_result, intent)

        entities = ExtractedEntity()
        if self._policy.enable_entity_extraction and intent != IntentType.UNKNOWN:
            entities = await self._extract_entities(request, intent)

        metadata = IntentMetadata(
            latency_ms=latency_ms,
            model=classification_result.model,
            provider=classification_result.provider,
            prompt_version=request.prompt_version or "1.0.0",
            correlation_id=classification_result.correlation_id,
            trace_id=classification_result.trace_id,
        )

        return IntentResult(
            intent=intent,
            confidence=confidence,
            confidence_level=self._resolve_confidence_level(confidence),
            entities=entities,
            needs_confirmation=self._policy.needs_confirmation(intent),
            needs_clarification=self._policy.needs_clarification(intent),
            suggested_agent=self._resolve_suggested_agent(intent),
            workflow_hint=self._resolve_workflow_hint(intent, entities),
            metadata=metadata,
            raw_response=classification_result.content,
        )

    async def _run_classification(self, request: IntentRequest) -> PipelineResult:
        ctx = self._build_pipeline_context(request)
        try:
            return await self._pipeline.orchestrate(ctx)
        except Exception as e:
            raise IntentClassificationError(
                f"Classification pipeline failed: {e}",
                detail=str(e),
            )

    def _build_pipeline_context(self, request: IntentRequest) -> PipelineContext:
        context = request.context
        context_str = self._build_context_string(context)
        variables: dict[str, Any] = {
            "user_type": context.user_type,
            "message": context.message,
            "context": context_str,
        }
        variables.update(context.metadata)
        return PipelineContext(
            conversation_id=context.conversation_id,
            user_id=context.user_id,
            session_id=context.session_id,
            prompt_category="classification",
            prompt_name="classification.intent_enhanced",
            prompt_version=request.prompt_version,
            prompt_variables=variables,
            temperature=request.temperature,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )

    def _build_context_string(self, context: IntentContext) -> str:
        parts: list[str] = []
        if context.conversation_history:
            for msg in context.conversation_history[-6:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                parts.append(f"{role}: {content}")
        return "\n".join(parts) if parts else "No prior context"

    def _parse_intent(self, content: str) -> IntentType:
        raw = content.strip().lower().replace(".", "").replace('"', "").replace("'", "")
        try:
            return IntentType(raw)
        except ValueError:
            logger.warning("Unrecognized intent '%s', falling back to unknown", raw)
            return IntentType.UNKNOWN

    def _calculate_confidence(self, result: PipelineResult, intent: IntentType) -> float:
        base = 0.85
        if intent == IntentType.UNKNOWN:
            base = 0.40
        if not result.content or not result.content.strip():
            base = 0.20
        if result.finish_reason and result.finish_reason != "stop":
            base *= 0.8
        if result.token_usage and result.token_usage.total_tokens == 0:
            base *= 0.5
        return round(min(max(base, 0.0), 1.0), 4)

    def _resolve_confidence_level(self, confidence: float) -> ConfidenceLevel:
        label = self._policy.get_confidence_label(confidence)
        return ConfidenceLevel(label)

    def _resolve_suggested_agent(self, intent: IntentType) -> str | None:
        agent_map: dict[IntentType, str] = {
            IntentType.MEETING_SCHEDULE: "meeting_agent",
            IntentType.MEETING_RESCHEDULE: "meeting_agent",
            IntentType.MEETING_CANCEL: "meeting_agent",
            IntentType.LEAD_QUALIFICATION: "lead_agent",
            IntentType.TASK_CREATION: "task_agent",
            IntentType.REMINDER: "reminder_agent",
            IntentType.WORKFLOW_TRIGGER: "workflow_agent",
            IntentType.INFORMATION_COLLECTION: "information_agent",
            IntentType.QUESTION_ANSWERING: "knowledge_agent",
        }
        return agent_map.get(intent)

    def _resolve_workflow_hint(
        self, intent: IntentType, entities: ExtractedEntity
    ) -> str | None:
        hint_map: dict[IntentType, str] = {
            IntentType.MEETING_SCHEDULE: "schedule_meeting",
            IntentType.MEETING_RESCHEDULE: "reschedule_meeting",
            IntentType.MEETING_CANCEL: "cancel_meeting",
            IntentType.LEAD_QUALIFICATION: "qualify_lead",
            IntentType.TASK_CREATION: "create_task",
            IntentType.REMINDER: "set_reminder",
            IntentType.WORKFLOW_TRIGGER: "trigger_workflow",
        }
        hint = hint_map.get(intent)
        if hint and entities.workflow_parameters:
            return f"{hint}:{json.dumps(entities.workflow_parameters)}"
        return hint

    async def _extract_entities(
        self, request: IntentRequest, intent: IntentType
    ) -> ExtractedEntity:
        ctx = self._build_entity_context(request, intent)
        try:
            result = await self._pipeline.orchestrate(ctx)
            return self._parse_entities(result.content)
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)
            return ExtractedEntity()

    def _build_entity_context(self, request: IntentRequest, intent: IntentType) -> PipelineContext:
        context = request.context
        return PipelineContext(
            conversation_id=context.conversation_id,
            user_id=context.user_id,
            session_id=context.session_id,
            prompt_category="classification",
            prompt_name="classification.intent_entity",
            prompt_version="1.0.0",
            prompt_variables={
                "message": context.message,
                "context": self._build_context_string(context),
                "intent": intent.value,
            },
            temperature=0.1,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )

    def _parse_entities(self, content: str) -> ExtractedEntity:
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                data = json.loads(content[start:end])
            except (ValueError, json.JSONDecodeError):
                return ExtractedEntity()

        duration_raw = data.get("duration")
        duration = None
        if duration_raw is not None:
            try:
                duration = int(duration_raw)
            except (ValueError, TypeError):
                pass

        tags_raw = data.get("tags")
        tags: list[str] = []
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = [str(t) for t in tags_raw]

        workflow_raw = data.get("workflow_parameters", {})
        workflow_params: dict[str, Any] = {}
        if isinstance(workflow_raw, dict):
            workflow_params = workflow_raw

        return ExtractedEntity(
            person_name=data.get("person_name"),
            company=data.get("company"),
            email=data.get("email"),
            phone=data.get("phone"),
            date=data.get("date"),
            time=data.get("time"),
            timezone=data.get("timezone"),
            duration=duration,
            meeting_type=data.get("meeting_type"),
            priority=data.get("priority"),
            tags=tags,
            workflow_parameters=workflow_params,
            raw=data,
        )

    def _validate_context(self, context: IntentContext) -> None:
        if not context or not context.message or not context.message.strip():
            raise IntentClassificationError("Empty message provided for classification")
