from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.workflow.registry import WorkflowRegistry

logger = logging.getLogger("ai_assistant")


class WorkflowEngineHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class WorkflowEngineHealth:
    workflow_id: str = ""
    status: WorkflowEngineHealthStatus = WorkflowEngineHealthStatus.UNKNOWN
    engine_name: str = ""
    is_registered: bool = False
    healthy: bool = False
    latency_ms: float = 0.0
    last_check: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == WorkflowEngineHealthStatus.HEALTHY


@dataclass
class WorkflowRegistryHealth:
    status: WorkflowEngineHealthStatus = WorkflowEngineHealthStatus.UNKNOWN
    total_workflows: int = 0
    registered_workflows: int = 0
    healthy_workflows: int = 0
    unhealthy_workflows: int = 0
    workflow_health: dict[str, WorkflowEngineHealth] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    last_check: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.status == WorkflowEngineHealthStatus.HEALTHY


class WorkflowHealthChecker:
    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._cache: WorkflowRegistryHealth | None = None

    async def check_registry(self) -> WorkflowRegistryHealth:
        start = time.time()
        health = WorkflowRegistryHealth(last_check=start)
        workflows = self._registry.list_workflows()
        health.total_workflows = len(workflows)
        health.registered_workflows = len(workflows)
        errors: list[str] = []

        for reg in workflows:
            engine_health = WorkflowEngineHealth(
                workflow_id=reg.definition.workflow_id,
                engine_name=reg.engine.name,
                is_registered=True,
                healthy=reg.healthy,
            )
            try:
                healthy_flag = await reg.engine.health_check()
                engine_health.healthy = healthy_flag
                if healthy_flag:
                    engine_health.status = WorkflowEngineHealthStatus.HEALTHY
                    health.healthy_workflows += 1
                else:
                    engine_health.status = WorkflowEngineHealthStatus.DEGRADED
                    health.unhealthy_workflows += 1
            except Exception as e:
                engine_health.status = WorkflowEngineHealthStatus.UNHEALTHY
                engine_health.error = str(e)
                health.unhealthy_workflows += 1
                errors.append(f"Workflow {reg.definition.workflow_id}: {e}")

            health.workflow_health[reg.definition.workflow_id] = engine_health

        if errors:
            health.errors = errors
            health.status = WorkflowEngineHealthStatus.DEGRADED
        elif health.total_workflows == 0:
            health.status = WorkflowEngineHealthStatus.HEALTHY
        elif health.unhealthy_workflows == 0:
            health.status = WorkflowEngineHealthStatus.HEALTHY
        elif health.healthy_workflows > 0:
            health.status = WorkflowEngineHealthStatus.DEGRADED
        else:
            health.status = WorkflowEngineHealthStatus.UNHEALTHY

        health.last_check = time.time()
        self._cache = health
        return health

    def get_cached(self) -> WorkflowRegistryHealth | None:
        return self._cache

    async def check_engine(self, workflow_id: str) -> WorkflowEngineHealth:
        start = time.time()
        health = WorkflowEngineHealth(workflow_id=workflow_id, last_check=start)
        try:
            engine = self._registry.get(workflow_id)
            health.is_registered = True
            health.engine_name = engine.name
            healthy_flag = await engine.health_check()
            health.healthy = healthy_flag
            health.status = (
                WorkflowEngineHealthStatus.HEALTHY if healthy_flag
                else WorkflowEngineHealthStatus.DEGRADED
            )
        except Exception as e:
            health.status = WorkflowEngineHealthStatus.UNHEALTHY
            health.error = str(e)

        health.latency_ms = (time.time() - start) * 1000
        return health
