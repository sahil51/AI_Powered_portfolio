from __future__ import annotations

import logging
from typing import Any

from application.agent.interfaces import AgentInterface
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.aggregate import Agent
from domain.agent.factory import AgentFactory as DomainAgentFactory
from domain.agent.value_objects import (
    AgentCapability,
    AgentPriority,
    AgentType,
)

logger = logging.getLogger("ai_assistant")


class AgentBuilder:
    def __init__(self) -> None:
        self._name: str = ""
        self._agent_type: AgentType = AgentType.CUSTOM
        self._capabilities: set[AgentCapability] = set()
        self._priority: AgentPriority = AgentPriority.MEDIUM
        self._display_name: str = ""
        self._description: str = ""
        self._version: str = "1.0.0"
        self._config: dict[str, Any] = {}
        self._metadata: dict[str, Any] = {}

    def with_name(self, name: str) -> AgentBuilder:
        self._name = name
        return self

    def with_type(self, agent_type: AgentType) -> AgentBuilder:
        self._agent_type = agent_type
        return self

    def with_capabilities(self, *capabilities: AgentCapability) -> AgentBuilder:
        self._capabilities.update(capabilities)
        return self

    def with_priority(self, priority: AgentPriority) -> AgentBuilder:
        self._priority = priority
        return self

    def with_display_name(self, display_name: str) -> AgentBuilder:
        self._display_name = display_name
        return self

    def with_description(self, description: str) -> AgentBuilder:
        self._description = description
        return self

    def with_version(self, version: str) -> AgentBuilder:
        self._version = version
        return self

    def with_config(self, config: dict[str, Any]) -> AgentBuilder:
        self._config = config
        return self

    def with_metadata(self, metadata: dict[str, Any]) -> AgentBuilder:
        self._metadata = metadata
        return self

    def build(self, agent: AgentInterface) -> AgentRegistration:
        return AgentRegistration(
            agent=agent,
            name=self._name,
            agent_type=self._agent_type,
            capabilities=self._capabilities,
            priority=self._priority,
            version=self._version,
            description=self._description,
            metadata=self._metadata,
        )


class AgentResolver:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry()

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    def resolve_by_id(self, agent_id: str) -> AgentInterface:
        return self._registry.get(agent_id)

    def resolve_by_type(self, agent_type: AgentType) -> list[AgentInterface]:
        return self._registry.get_by_type(agent_type)

    def resolve_by_capability(self, capability: AgentCapability) -> list[AgentInterface]:
        return self._registry.get_by_capability(capability)

    def resolve_default(self, agent_type: AgentType) -> AgentInterface | None:
        return self._registry.get_default_agent(agent_type)


class AgentLoader:
    def __init__(self, domain_factory: DomainAgentFactory | None = None) -> None:
        self._domain_factory = domain_factory or DomainAgentFactory()

    def load(self, agent_data: dict[str, Any]) -> Agent:
        agent_type = AgentType(agent_data.get("agent_type", "custom"))
        return self._domain_factory.restore(
            agent_id=agent_data.get("agent_id", ""),
            name=agent_data.get("name", ""),
            agent_type=agent_type,
            status=agent_data.get("status", "created"),
            capabilities=set(
                AgentCapability(c) for c in agent_data.get("capabilities", [])
            ) if agent_data.get("capabilities") else None,
            priority=AgentPriority(agent_data.get("priority", "medium")),
            correlation_id=agent_data.get("correlation_id"),
            session_id=agent_data.get("session_id"),
            config=agent_data.get("config"),
            checkpoint=agent_data.get("checkpoint"),
            error_count=agent_data.get("error_count", 0),
            created_at=agent_data.get("created_at"),
            updated_at=agent_data.get("updated_at"),
            started_at=agent_data.get("started_at"),
            completed_at=agent_data.get("completed_at"),
            version=agent_data.get("version", 1),
        )
