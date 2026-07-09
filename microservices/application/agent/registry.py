from __future__ import annotations

import logging
from typing import Any

from application.agent.exceptions import AgentNotFoundError, AgentRegistrationError
from application.agent.interfaces import AgentInterface
from application.agent.models import AgentStatistics
from domain.agent.value_objects import AgentCapability, AgentPriority, AgentType

logger = logging.getLogger("ai_assistant")


class AgentRegistration:
    def __init__(
        self,
        agent: AgentInterface,
        name: str = "",
        agent_type: AgentType = AgentType.CUSTOM,
        capabilities: set[AgentCapability] | None = None,
        priority: AgentPriority = AgentPriority.MEDIUM,
        version: str = "1.0.0",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.agent = agent
        self.name = name or agent.name
        self.agent_type = agent_type
        self.capabilities = capabilities or agent.capabilities
        self.priority = priority
        self.version = version
        self.description = description
        self.metadata = metadata or {}
        self.healthy: bool = True
        self.statistics: AgentStatistics = AgentStatistics()


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRegistration] = {}
        self._agent_type_index: dict[AgentType, set[str]] = {}
        self._capability_index: dict[AgentCapability, set[str]] = {}

    def register(self, registration: AgentRegistration) -> None:
        agent_id = registration.agent.agent_id
        if agent_id in self._agents:
            raise AgentRegistrationError(detail=f"Agent {agent_id} already registered")
        self._agents[agent_id] = registration

        at = registration.agent_type
        if at not in self._agent_type_index:
            self._agent_type_index[at] = set()
        self._agent_type_index[at].add(agent_id)

        for cap in registration.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = set()
            self._capability_index[cap].add(agent_id)

        logger.info("Agent registered: %s (%s)", registration.name, agent_id)

    def unregister(self, agent_id: str) -> None:
        registration = self._agents.pop(agent_id, None)
        if registration is None:
            return

        at = registration.agent_type
        if at in self._agent_type_index:
            self._agent_type_index[at].discard(agent_id)

        for cap in registration.capabilities:
            if cap in self._capability_index:
                self._capability_index[cap].discard(agent_id)

        logger.info("Agent unregistered: %s", agent_id)

    def get(self, agent_id: str) -> AgentInterface:
        registration = self._agents.get(agent_id)
        if registration is None:
            raise AgentNotFoundError(detail=f"Agent {agent_id} not found")
        return registration.agent

    def get_registration(self, agent_id: str) -> AgentRegistration:
        registration = self._agents.get(agent_id)
        if registration is None:
            raise AgentNotFoundError(detail=f"Agent {agent_id} not found")
        return registration

    def get_by_type(self, agent_type: AgentType) -> list[AgentInterface]:
        agent_ids = self._agent_type_index.get(agent_type, set())
        return [self._agents[aid].agent for aid in agent_ids if aid in self._agents]

    def get_by_capability(self, capability: AgentCapability) -> list[AgentInterface]:
        agent_ids = self._capability_index.get(capability, set())
        return [self._agents[aid].agent for aid in agent_ids if aid in self._agents]

    def get_by_priority(self, priority: AgentPriority) -> list[AgentInterface]:
        return [
            reg.agent
            for reg in self._agents.values()
            if reg.priority == priority
        ]

    def list_agents(self) -> list[AgentRegistration]:
        return list(self._agents.values())

    def list_types(self) -> list[AgentType]:
        return list(self._agent_type_index.keys())

    def list_capabilities(self) -> list[AgentCapability]:
        return list(self._capability_index.keys())

    def get_default_agent(self, agent_type: AgentType) -> AgentInterface | None:
        agents = self.get_by_type(agent_type)
        if not agents:
            return None
        agents.sort(key=lambda a: self._get_priority(a.agent_id))
        return agents[0]

    def count(self) -> int:
        return len(self._agents)

    def has_agent(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def mark_health(self, agent_id: str, healthy: bool) -> None:
        registration = self._agents.get(agent_id)
        if registration:
            registration.healthy = healthy

    def get_health(self, agent_id: str) -> bool:
        registration = self._agents.get(agent_id)
        return registration.healthy if registration else False

    def get_statistics(self, agent_id: str) -> AgentStatistics:
        registration = self._agents.get(agent_id)
        if registration is None:
            raise AgentNotFoundError(detail=f"Agent {agent_id} not found")
        return registration.statistics

    def clear(self) -> None:
        self._agents.clear()
        self._agent_type_index.clear()
        self._capability_index.clear()

    def _get_priority(self, agent_id: str) -> int:
        priority_order = {
            AgentPriority.CRITICAL: 0,
            AgentPriority.HIGH: 1,
            AgentPriority.MEDIUM: 2,
            AgentPriority.LOW: 3,
            AgentPriority.BACKGROUND: 4,
        }
        reg = self._agents.get(agent_id)
        if reg is None:
            return 99
        return priority_order.get(reg.priority, 99)
