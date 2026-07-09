from __future__ import annotations

import logging
from typing import Any

from application.agent.execution import ExecutionManager
from application.agent.interfaces import AgentContext, AgentResult
from application.agent.lifecycle import LifecycleManager
from application.agent.models import AgentConfiguration, AgentStatistics
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.aggregate import Agent
from domain.agent.state import AgentStatus

logger = logging.getLogger("ai_assistant")


class AgentRuntime:
    def __init__(
        self,
        registry: AgentRegistry | None = None,
        config: AgentConfiguration | None = None,
    ) -> None:
        self._registry = registry or AgentRegistry()
        self._config = config or AgentConfiguration()
        self._execution = ExecutionManager(self._registry)
        self._lifecycle = LifecycleManager(self._registry)

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def config(self) -> AgentConfiguration:
        return self._config

    @property
    def execution(self) -> ExecutionManager:
        return self._execution

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

    async def execute(
        self,
        agent_id: str,
        context: AgentContext,
        timeout: float | None = None,
    ) -> AgentResult:
        effective_timeout = timeout or self._config.timeout
        return await self._execution.execute(agent_id, context, effective_timeout)

    async def execute_with_retry(
        self,
        agent_id: str,
        context: AgentContext,
        max_attempts: int | None = None,
    ) -> AgentResult:
        attempts = max_attempts or self._config.max_retries
        return await self._execution.retry(agent_id, context, attempts)

    async def pause(self, agent_id: str, reason: str = "") -> Agent:
        return await self._lifecycle.pause(agent_id, reason)

    async def resume(self, agent_id: str, reason: str = "") -> Agent:
        return await self._lifecycle.resume(agent_id, reason)

    async def cancel(self, agent_id: str, reason: str = "") -> Agent:
        return await self._lifecycle.cancel(agent_id, reason)

    async def restart(self, agent_id: str, session_id: str = "") -> Agent:
        return await self._lifecycle.restart(agent_id, session_id)

    async def recover(self, agent_id: str, session_id: str = "") -> Agent | None:
        return await self._lifecycle.recover(agent_id, session_id)

    async def heartbeat(self, agent_id: str) -> None:
        await self._lifecycle.heartbeat(agent_id)

    async def checkpoint(self, agent_id: str, data: dict[str, Any]) -> None:
        await self._lifecycle.checkpoint(agent_id, data)

    async def archive(self, agent_id: str, reason: str = "") -> Agent:
        return await self._lifecycle.archive(agent_id, reason)

    def get_status(self, agent_id: str) -> AgentStatus | None:
        return self._lifecycle.get_status(agent_id)

    def is_running(self, agent_id: str) -> bool:
        return self._execution.is_running(agent_id)

    def get_statistics(self, agent_id: str) -> AgentStatistics:
        return self._registry.get_statistics(agent_id)

    def list_agents(self) -> list[AgentRegistration]:
        return self._registry.list_agents()

    def list_running(self) -> list[str]:
        return self._execution.list_running()

    def register(self, registration: AgentRegistration) -> None:
        self._registry.register(registration)

    def unregister(self, agent_id: str) -> None:
        self._registry.unregister(agent_id)
