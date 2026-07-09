from __future__ import annotations

import logging
import time

from application.confirmation.exceptions import ConfirmationEngineError, ConfirmationValidationError
from application.confirmation.interfaces import ConfirmationEngineInterface
from application.confirmation.metrics import ConfirmationMetricsCollector
from application.confirmation.models import ConfirmationContext, ConfirmationResult
from application.confirmation.policies import ConfirmationPolicy, default_confirmation_policy
from application.confirmation.resolver import ConfirmationResolver
from application.confirmation.validator import ConfirmationValidator
from domain.enums.confirmation import ConfirmationType

logger = logging.getLogger("ai_assistant")


class ConfirmationEngine(ConfirmationEngineInterface):
    def __init__(
        self,
        resolver: ConfirmationResolver,
        validator: ConfirmationValidator | None = None,
        policy: ConfirmationPolicy | None = None,
        metrics_collector: ConfirmationMetricsCollector | None = None,
    ) -> None:
        self._resolver = resolver
        self._validator = validator or ConfirmationValidator()
        self._policy = policy or default_confirmation_policy()
        self._metrics = metrics_collector or ConfirmationMetricsCollector()

    async def process(self, context: ConfirmationContext) -> ConfirmationResult:
        start = time.time()

        try:
            self._validator.validate_context(context)
        except ConfirmationValidationError as e:
            self._metrics.record_resolution(
                confirmation_type=self._resolve_fallback_type(),
                latency_ms=0.0,
                success=False,
            )
            raise ConfirmationEngineError(str(e), detail=e.detail)

        try:
            result = await self._resolver.resolve(context)
        except Exception as e:
            self._metrics.record_resolution(
                confirmation_type=self._resolve_fallback_type(),
                latency_ms=(time.time() - start) * 1000,
                success=False,
            )
            raise ConfirmationEngineError(f"Resolution failed: {e}", detail=str(e))

        latency_ms = (time.time() - start) * 1000
        result.metadata.latency_ms = latency_ms

        self._metrics.record_resolution(
            confirmation_type=result.confirmation_type,
            latency_ms=latency_ms,
            success=True,
        )
        if result.ready_for_agent:
            self._metrics.record_agent_readiness()

        return result

    @property
    def metrics(self) -> ConfirmationMetricsCollector:
        return self._metrics

    def _resolve_fallback_type(self) -> ConfirmationType:
        return ConfirmationType.UNKNOWN
