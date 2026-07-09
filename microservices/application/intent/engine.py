from __future__ import annotations

import logging
import time

from application.intent.classifier import IntentClassifier
from application.intent.exceptions import IntentEngineError, IntentValidationError
from application.intent.interfaces import IntentEngineInterface
from application.intent.metrics import IntentMetricsCollector
from application.intent.models import IntentRequest, IntentResult
from application.intent.policies import IntentPolicy, default_intent_policy
from application.intent.resolver import IntentResolver
from application.intent.statistics import IntentStatistics
from application.intent.validator import IntentValidator
from domain.enums.intent import IntentType

logger = logging.getLogger("ai_assistant")


class IntentEngine(IntentEngineInterface):
    def __init__(
        self,
        classifier: IntentClassifier,
        resolver: IntentResolver | None = None,
        validator: IntentValidator | None = None,
        policy: IntentPolicy | None = None,
        metrics_collector: IntentMetricsCollector | None = None,
        statistics: IntentStatistics | None = None,
    ) -> None:
        self._classifier = classifier
        self._resolver = resolver or IntentResolver()
        self._validator = validator or IntentValidator()
        self._policy = policy or default_intent_policy()
        self._metrics = metrics_collector or IntentMetricsCollector()
        self._statistics = statistics or IntentStatistics()

    async def analyze(self, request: IntentRequest) -> IntentResult:
        start = time.time()

        try:
            self._validator.validate_request(request)
        except IntentValidationError as e:
            self._metrics.record_classification(
                intent=self._resolve_fallback_intent(),
                confidence=0.0,
                latency_ms=0.0,
                success=False,
            )
            raise IntentEngineError(str(e), detail=e.detail)

        try:
            result = await self._classifier.classify(request)
        except Exception as e:
            self._metrics.record_classification(
                intent=self._resolve_fallback_intent(),
                confidence=0.0,
                latency_ms=(time.time() - start) * 1000,
                success=False,
            )
            raise IntentEngineError(f"Classification failed: {e}", detail=str(e))

        resolved = await self._resolver.resolve(result, request.context)
        latency_ms = (time.time() - start) * 1000

        self._metrics.record_classification(
            intent=resolved.intent,
            confidence=resolved.confidence,
            latency_ms=latency_ms,
            success=True,
        )
        if resolved.entities.raw:
            self._metrics.record_entity_extraction(success=True)
        if resolved.needs_clarification:
            self._metrics.record_clarification()
        if resolved.intent == IntentType.FALLBACK:
            self._metrics.record_fallback()
        if self._policy.auto_accept(resolved.intent):
            self._metrics.record_auto_accept()

        self._statistics.record(
            intent=resolved.intent,
            confidence=resolved.confidence,
            latency_ms=latency_ms,
            user_id=request.context.user_id,
            session_id=request.context.session_id,
        )

        resolved.metadata.latency_ms = latency_ms
        return resolved

    @property
    def metrics(self) -> IntentMetricsCollector:
        return self._metrics

    @property
    def statistics(self) -> IntentStatistics:
        return self._statistics

    def _resolve_fallback_intent(self) -> IntentType:
        return IntentType.UNKNOWN
