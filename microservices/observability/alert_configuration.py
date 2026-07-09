from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlertRule:
    name: str
    description: str
    severity: AlertSeverity
    condition: str
    duration_seconds: int = 60
    threshold: float = 0.0
    enabled: bool = True
    cooldown_seconds: int = 300

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "condition": self.condition,
            "duration_seconds": self.duration_seconds,
            "threshold": self.threshold,
            "enabled": self.enabled,
            "cooldown_seconds": self.cooldown_seconds,
        }


class AlertConfiguration:
    def __init__(self) -> None:
        self._rules: dict[str, AlertRule] = {}

    def add_rule(self, rule: AlertRule) -> None:
        self._rules[rule.name] = rule

    def remove_rule(self, name: str) -> None:
        self._rules.pop(name, None)

    def get_rule(self, name: str) -> AlertRule | None:
        return self._rules.get(name)

    def get_rules(self) -> list[AlertRule]:
        return list(self._rules.values())

    def get_default_rules(self) -> list[AlertRule]:
        return [
            AlertRule(
                name="high_latency",
                description="Request latency exceeds threshold",
                severity=AlertSeverity.WARNING,
                condition="http_request_duration_seconds > 5.0",
                threshold=5.0,
            ),
            AlertRule(
                name="high_error_rate",
                description="Error rate exceeds threshold",
                severity=AlertSeverity.CRITICAL,
                condition="rate(errors_total[5m]) > 0.05",
                threshold=0.05,
            ),
            AlertRule(
                name="queue_backlog",
                description="Task queue depth exceeds threshold",
                severity=AlertSeverity.WARNING,
                condition="queue_depth > 100",
                threshold=100,
            ),
            AlertRule(
                name="database_down",
                description="Database health check failed",
                severity=AlertSeverity.CRITICAL,
                condition="database_status != 1",
            ),
            AlertRule(
                name="redis_down",
                description="Redis health check failed",
                severity=AlertSeverity.CRITICAL,
                condition="redis_status != 1",
            ),
            AlertRule(
                name="embedding_failure",
                description="Embedding provider failures",
                severity=AlertSeverity.WARNING,
                condition="rate(embedding_operations_total{status='error'}[5m]) > 0.1",
            ),
            AlertRule(
                name="provider_failure",
                description="AI provider call failures",
                severity=AlertSeverity.CRITICAL,
                condition="rate(provider_calls_total{status='error'}[5m]) > 0.1",
            ),
            AlertRule(
                name="knowledge_failure",
                description="Knowledge operation failures",
                severity=AlertSeverity.WARNING,
                condition="rate(knowledge_operations_total{status='error'}[5m]) > 0.1",
            ),
            AlertRule(
                name="workflow_failure",
                description="Workflow execution failures",
                severity=AlertSeverity.WARNING,
                condition="rate(workflow_operations_total{status='error'}[5m]) > 0.1",
            ),
        ]

    def load_defaults(self) -> None:
        for rule in self.get_default_rules():
            self._rules[rule.name] = rule

    def to_dict(self) -> list[dict[str, Any]]:
        return [rule.to_dict() for rule in self._rules.values()]

    def clear(self) -> None:
        self._rules.clear()
