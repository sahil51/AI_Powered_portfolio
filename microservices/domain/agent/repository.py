from collections.abc import Sequence
from typing import Protocol

from domain.agent.aggregate import Agent
from domain.agent.value_objects import AgentId, AgentStatus, AgentType


class AgentRepository(Protocol):
    async def save(self, agent: Agent) -> None:
        ...

    async def get_by_id(self, agent_id: AgentId) -> Agent | None:
        ...

    async def get_by_id_str(self, agent_id: str) -> Agent | None:
        ...

    async def get_by_name(self, name: str) -> Agent | None:
        ...

    async def get_by_type(
        self,
        agent_type: AgentType,
        limit: int = 50,
    ) -> Sequence[Agent]:
        ...

    async def get_by_status(
        self,
        status: AgentStatus,
        limit: int = 50,
    ) -> Sequence[Agent]:
        ...

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        agent_type: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Agent], int]:
        ...

    async def delete(self, agent_id: AgentId) -> None:
        ...

    async def count_by_type(self, agent_type: AgentType) -> int:
        ...

    async def count_by_status(self, status: AgentStatus) -> int:
        ...

    async def get_stale_agents(self, timeout_seconds: int = 300) -> Sequence[Agent]:
        ...
