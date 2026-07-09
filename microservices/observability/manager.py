from __future__ import annotations

import logging
from typing import Any

from config.settings import settings
from observability.alert_configuration import AlertConfiguration
from observability.dashboard_configuration import DashboardConfiguration
from observability.health_aggregator import HealthAggregator
from observability.logging_manager import LoggingManager
from observability.metrics_collector import MetricsCollector
from observability.metrics_registry import MetricsRegistry
from observability.statistics_collector import StatisticsCollector
from observability.telemetry_configuration import TelemetryConfiguration
from observability.tracing_manager import TracingManager

logger = logging.getLogger("ai_assistant.observability")


class ObservabilityManager:
    def __init__(self) -> None:
        self._initialized = False
        self._metrics_registry = MetricsRegistry()
        self._metrics_collector = MetricsCollector(self._metrics_registry)
        self._tracing_manager = TracingManager(service_name=settings.app_name)
        self._logging_manager = LoggingManager(app_name=settings.app_name, level=settings.log_level)
        self._health_aggregator = HealthAggregator()
        self._statistics_collector = StatisticsCollector()
        self._alert_configuration = AlertConfiguration()
        self._dashboard_configuration = DashboardConfiguration()
        self._telemetry_configuration = TelemetryConfiguration()

    @property
    def metrics_registry(self) -> MetricsRegistry:
        return self._metrics_registry

    @property
    def metrics_collector(self) -> MetricsCollector:
        return self._metrics_collector

    @property
    def tracing_manager(self) -> TracingManager:
        return self._tracing_manager

    @property
    def logging_manager(self) -> LoggingManager:
        return self._logging_manager

    @property
    def health_aggregator(self) -> HealthAggregator:
        return self._health_aggregator

    @property
    def statistics_collector(self) -> StatisticsCollector:
        return self._statistics_collector

    @property
    def alert_configuration(self) -> AlertConfiguration:
        return self._alert_configuration

    @property
    def dashboard_configuration(self) -> DashboardConfiguration:
        return self._dashboard_configuration

    @property
    def telemetry_configuration(self) -> TelemetryConfiguration:
        return self._telemetry_configuration

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Initializing observability manager")
        self._alert_configuration.load_defaults()
        self._dashboard_configuration.load_defaults()
        self._health_aggregator.register_component("database")
        self._health_aggregator.register_component("redis")
        self._health_aggregator.register_component("celery")
        self._health_aggregator.register_component("provider")
        self._health_aggregator.register_component("workflow")
        self._health_aggregator.register_component("knowledge")
        self._initialized = True
        logger.info("Observability manager initialized")

    async def shutdown(self) -> None:
        if not self._initialized:
            return
        logger.info("Shutting down observability manager")
        self._tracing_manager.clear()
        self._metrics_collector.reset()
        self._statistics_collector.reset()
        self._initialized = False
        logger.info("Observability manager shut down")

    async def health_report(self) -> dict[str, Any]:
        system = await self._health_aggregator.check_all()
        return {
            "status": system.status.value,
            "uptime_seconds": system.uptime_seconds,
            "components": {
                name: {
                    "status": comp.status.value,
                    "latency_ms": comp.latency_ms,
                    "error": comp.error,
                }
                for name, comp in system.components.items()
            },
        }

    def metrics_report(self) -> dict[str, Any]:
        return self._metrics_collector.get_metrics_data().__dict__

    def tracing_report(self) -> list[dict[str, Any]]:
        return self._tracing_manager.get_spans()

    def statistics_report(self) -> dict[str, Any]:
        return self._statistics_collector.snapshot()
