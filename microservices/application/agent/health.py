from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.agent.registry import AgentRegistry
from domain.agent.state import AgentStatus

logger = logging.getLogger("ai_assistant")


class AgentRuntimeHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentHealth:
    agent_id: str = ""
    status: AgentRuntimeHealthStatus = AgentRuntimeHealthStatus.UNKNOWN
    agent_status: AgentStatus | None = None
    is_registered: bool = False
    is_running: bool = False
    latency_ms: float = 0.0
    last_check: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == AgentRuntimeHealthStatus.HEALTHY


@dataclass
class AgentRuntimeHealth:
    status: AgentRuntimeHealthStatus = AgentRuntimeHealthStatus.UNKNOWN
    total_agents: int = 0
    registered_agents: int = 0
    running_agents: int = 0
    healthy_agents: int = 0
    unhealthy_agents: int = 0
    agent_health: dict[str, AgentHealth] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    last_check: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.status == AgentRuntimeHealthStatus.HEALTHY


class AgentHealthChecker:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._cache: AgentRuntimeHealth | None = None

    async def check_runtime(self) -> AgentRuntimeHealth:
        start = time.time()
        health = AgentRuntimeHealth(last_check=start)
        agents = self._registry.list_agents()
        health.total_agents = len(agents)
        health.registered_agents = len(agents)
        errors: list[str] = []

        for reg in agents:
            agent_health = AgentHealth(
                agent_id=reg.agent.agent_id,
                agent_status=AgentStatus.CREATED,
                is_registered=True,
            )
            try:
                agent_health.agent_status = reg.agent.status
                agent_health.is_running = reg.agent.is_active
                if reg.healthy:
                    agent_health.status = AgentRuntimeHealthStatus.HEALTHY
                    health.healthy_agents += 1
                else:
                    agent_health.status = AgentRuntimeHealthStatus.DEGRADED
                    health.unhealthy_agents += 1
            except Exception as e:
                agent_health.status = AgentRuntimeHealthStatus.UNHEALTHY
                agent_health.error = str(e)
                health.unhealthy_agents += 1
                errors.append(f"Agent {reg.agent.agent_id}: {e}")

            health.agent_health[reg.agent.agent_id] = agent_health

        if errors:
            health.errors = errors
            health.status = AgentRuntimeHealthStatus.DEGRADED
        elif health.total_agents == 0:
            health.status = AgentRuntimeHealthStatus.HEALTHY
        elif health.unhealthy_agents == 0:
            health.status = AgentRuntimeHealthStatus.HEALTHY
        elif health.healthy_agents > 0:
            health.status = AgentRuntimeHealthStatus.DEGRADED
        else:
            health.status = AgentRuntimeHealthStatus.UNHEALTHY

        health.last_check = time.time()
        health.running_agents = len([a for a in agents if a.agent.is_active])
        self._cache = health
        return health

    def get_cached(self) -> AgentRuntimeHealth | None:
        return self._cache

    async def check_agent(self, agent_id: str) -> AgentHealth:
        start = time.time()
        health = AgentHealth(agent_id=agent_id, last_check=start)

        try:
            agent = self._registry.get(agent_id)
            health.is_registered = True
            health.agent_status = agent.status
            health.is_running = agent.is_active
            reg = self._registry.get_registration(agent_id)
            if reg.healthy:
                health.status = AgentRuntimeHealthStatus.HEALTHY
            else:
                health.status = AgentRuntimeHealthStatus.DEGRADED
        except Exception as e:
            health.status = AgentRuntimeHealthStatus.UNHEALTHY
            health.error = str(e)

        health.latency_ms = (time.time() - start) * 1000
        return health
