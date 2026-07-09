from __future__ import annotations

from application.ai.metrics import ProviderMetricsCollector


class LiteLLMMetrics(ProviderMetricsCollector):
    def __init__(self) -> None:
        super().__init__()
