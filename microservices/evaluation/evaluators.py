from __future__ import annotations

import time
from typing import Any

from evaluation.models import (
    EvaluationCase,
    EvaluationOutput,
)
from evaluation.registry import EvaluationRegistry


class IntentEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        predicted_intent = case.input.get("query", "")
        expected_intent = case.baseline.expected_intent
        exact_match = predicted_intent.strip().lower() == expected_intent.strip().lower() if expected_intent else False
        return EvaluationOutput(
            predicted_intent=predicted_intent,
            confidence=1.0 if exact_match else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class EntityEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        predicted_entities: list[dict[str, str]] = case.input.get("entities", [])
        return EvaluationOutput(
            predicted_entities=predicted_entities,
            confidence=1.0 if predicted_entities else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class ConfirmationEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        resolution = case.input.get("resolution", "")
        expected = case.baseline.golden_answer
        passed = resolution.strip().lower() == expected.strip().lower() if expected else False
        return EvaluationOutput(
            predicted_value=resolution,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class MemoryEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        recalled = case.input.get("recalled", "")
        expected = case.baseline.expected_output
        passed = recalled.strip().lower() == expected.strip().lower() if expected else False
        return EvaluationOutput(
            predicted_value=recalled,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class KnowledgeRetrievalEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        results: list[dict[str, Any]] = case.input.get("results", [])
        return EvaluationOutput(
            predicted_value=results,
            confidence=1.0 if results else 0.0,
            latency_ms=(time.time() - start) * 1000,
            token_count=case.input.get("token_count", 0),
        )


class HybridSearchEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        results: list[dict[str, Any]] = case.input.get("hybrid_results", [])
        return EvaluationOutput(
            predicted_value=results,
            confidence=1.0 if results else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class ContextBuilderEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        context = case.input.get("context", {})
        expected = case.baseline.expected_context
        return EvaluationOutput(
            predicted_value=context,
            confidence=1.0 if context == expected else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class PromptRenderingEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        rendered = case.input.get("rendered", "")
        expected = case.baseline.expected_output
        passed = rendered.strip() == expected.strip() if expected else False
        return EvaluationOutput(
            predicted_value=rendered,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
            token_count=case.input.get("token_count", 0),
        )


class MeetingAgentEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        action = case.input.get("action", "")
        expected = case.baseline.expected_workflow
        passed = action.strip().lower() == expected.strip().lower() if expected else False
        return EvaluationOutput(
            predicted_workflow=action,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class WorkflowRequestEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        request: dict[str, Any] = case.input.get("request", {})
        expected_workflow = case.baseline.expected_workflow
        actual_workflow = request.get("workflow_type", "")
        passed = actual_workflow == expected_workflow if expected_workflow else False
        return EvaluationOutput(
            predicted_workflow=actual_workflow,
            predicted_value=request,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


class ResponseValidationEvaluator:
    async def evaluate(self, case: EvaluationCase) -> EvaluationOutput:
        start = time.time()
        response = case.input.get("response", "")
        expected = case.baseline.golden_answer
        case.input.get("hallucinated", False)
        passed = (response.strip().lower() == expected.strip().lower()) if expected else True
        return EvaluationOutput(
            predicted_value=response,
            confidence=1.0 if passed else 0.0,
            latency_ms=(time.time() - start) * 1000,
        )


def register_default_evaluators(registry: EvaluationRegistry) -> None:
    from evaluation.models import EvaluationType

    intent = IntentEvaluator()
    entity = EntityEvaluator()
    confirmation = ConfirmationEvaluator()
    memory = MemoryEvaluator()
    knowledge = KnowledgeRetrievalEvaluator()
    hybrid = HybridSearchEvaluator()
    context = ContextBuilderEvaluator()
    prompt = PromptRenderingEvaluator()
    meeting = MeetingAgentEvaluator()
    workflow = WorkflowRequestEvaluator()
    response = ResponseValidationEvaluator()

    registry.register(EvaluationType.INTENT_CLASSIFICATION, intent.evaluate)
    registry.register(EvaluationType.ENTITY_EXTRACTION, entity.evaluate)
    registry.register(EvaluationType.CONFIRMATION_RESOLUTION, confirmation.evaluate)
    registry.register(EvaluationType.CONVERSATION_MEMORY, memory.evaluate)
    registry.register(EvaluationType.KNOWLEDGE_RETRIEVAL, knowledge.evaluate)
    registry.register(EvaluationType.HYBRID_SEARCH, hybrid.evaluate)
    registry.register(EvaluationType.CONTEXT_BUILDER, context.evaluate)
    registry.register(EvaluationType.PROMPT_RENDERING, prompt.evaluate)
    registry.register(EvaluationType.MEETING_AGENT, meeting.evaluate)
    registry.register(EvaluationType.WORKFLOW_REQUEST, workflow.evaluate)
    registry.register(EvaluationType.RESPONSE_VALIDATION, response.evaluate)
