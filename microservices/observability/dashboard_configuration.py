from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DashboardPanelType(Enum):
    GRAPH = "graph"
    SINGLE_STAT = "single_stat"
    TABLE = "table"
    HEATMAP = "heatmap"


class DashboardDataSource(Enum):
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"


@dataclass
class DashboardPanel:
    title: str
    description: str = ""
    panel_type: DashboardPanelType = DashboardPanelType.GRAPH
    data_source: DashboardDataSource = DashboardDataSource.PROMETHEUS
    query: str = ""
    unit: str = ""
    span: int = 6

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "type": self.panel_type.value,
            "data_source": self.data_source.value,
            "query": self.query,
            "unit": self.unit,
            "span": self.span,
        }


class DashboardConfiguration:
    def __init__(self) -> None:
        self._panels: list[DashboardPanel] = []

    def add_panel(self, panel: DashboardPanel) -> None:
        self._panels.append(panel)

    def get_panels(self) -> list[DashboardPanel]:
        return list(self._panels)

    def get_default_panels(self) -> list[DashboardPanel]:
        return [
            DashboardPanel(
                title="HTTP Request Rate",
                description="Rate of HTTP requests by endpoint",
                query='rate(http_requests_total[5m])',
                unit="req/s",
            ),
            DashboardPanel(
                title="HTTP Latency (P95)",
                description="95th percentile HTTP request latency",
                query='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))',
                unit="s",
            ),
            DashboardPanel(
                title="Error Rate",
                description="Error rate by component",
                query='rate(errors_total[5m])',
                unit="errors/s",
            ),
            DashboardPanel(
                title="LLM Token Usage",
                description="Token usage by model",
                query='rate(tokens_total[5m])',
                unit="tokens/s",
            ),
            DashboardPanel(
                title="LLM Cost",
                description="Cost by model",
                query='rate(cost_total_usd[5m])',
                unit="$/s",
            ),
            DashboardPanel(
                title="Queue Depth",
                description="Queue depth by queue",
                query='queue_depth',
                unit="tasks",
            ),
            DashboardPanel(
                title="Active Workflows",
                description="Active workflow count",
                query='active_workflows',
                panel_type=DashboardPanelType.SINGLE_STAT,
                unit="count",
                span=3,
            ),
            DashboardPanel(
                title="Conversation Rate",
                description="Conversation operations per second",
                query='rate(conversation_operations_total[5m])',
                unit="ops/s",
            ),
            DashboardPanel(
                title="Provider Latency",
                description="Provider call latency by provider",
                query='rate(provider_duration_seconds_sum[5m]) / rate(provider_duration_seconds_count[5m])',
                unit="s",
            ),
            DashboardPanel(
                title="Database Operations",
                description="PostgreSQL operations per second",
                query='rate(postgresql_operations_total[5m])',
                unit="ops/s",
            ),
            DashboardPanel(
                title="Redis Operations",
                description="Redis operations per second",
                query='rate(redis_operations_total[5m])',
                unit="ops/s",
            ),
            DashboardPanel(
                title="Retry Rate",
                description="Retry rate by component",
                query='rate(retries_total[5m])',
                unit="retries/s",
            ),
        ]

    def load_defaults(self) -> None:
        for panel in self.get_default_panels():
            self._panels.append(panel)

    def to_dict(self) -> list[dict[str, Any]]:
        return [panel.to_dict() for panel in self._panels]

    def clear(self) -> None:
        self._panels.clear()

    def export_grafana_json(self) -> dict[str, Any]:
        panels = []
        for i, panel in enumerate(self._panels):
            panels.append({
                "id": i + 1,
                "title": panel.title,
                "description": panel.description,
                "type": "graph" if panel.panel_type == DashboardPanelType.GRAPH else "singlestat",
                "gridPos": {
                    "h": 8,
                    "w": panel.span,
                    "x": (i * panel.span) % 24,
                    "y": (i // (24 // max(panel.span, 1))) * 8,
                },
                "targets": [{"expr": panel.query, "legendFormat": "{{label}}"}],
                "options": {},
            })
        return {
            "title": f"{self.__class__.__name__}",
            "version": 1,
            "panels": panels,
        }
