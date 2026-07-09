from __future__ import annotations

import logging
from typing import Any

from application.agent.exceptions import AgentStateError
from application.agent.registry import AgentRegistry
from domain.agent.aggregate import Agent
from domain.agent.state import AgentStatus

logger = logging.getLogger("ai_assistant")


class LifecycleManager:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    async def initialize(self, agent_id: str, session_id: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.initialize(session_id)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["initialized"] = reg.statistics.state_transitions.get("initialized", 0) + 1
        return domain_agent

    async def start(self, agent_id: str) -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.start()
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["started"] = reg.statistics.state_transitions.get("started", 0) + 1
        return domain_agent

    async def pause(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.pause(reason)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.pause_count += 1
        reg.statistics.state_transitions["paused"] = reg.statistics.state_transitions.get("paused", 0) + 1
        return domain_agent

    async def resume(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.resume(reason)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.resume_count += 1
        reg.statistics.state_transitions["resumed"] = reg.statistics.state_transitions.get("resumed", 0) + 1
        return domain_agent

    async def cancel(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.cancel(reason)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.cancel_count += 1
        reg.statistics.state_transitions["cancelled"] = reg.statistics.state_transitions.get("cancelled", 0) + 1
        return domain_agent

    async def complete(self, agent_id: str, result: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.complete(result)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["completed"] = reg.statistics.state_transitions.get("completed", 0) + 1
        return domain_agent

    async def fail(self, agent_id: str, error: str = "", recoverable: bool = False) -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.fail(error, recoverable)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["failed"] = reg.statistics.state_transitions.get("failed", 0) + 1
        return domain_agent

    async def archive(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.archive(reason)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["archived"] = reg.statistics.state_transitions.get("archived", 0) + 1
        return domain_agent

    async def restart(self, agent_id: str, session_id: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        domain_agent = await agent.restart(session_id)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.state_transitions["restarted"] = reg.statistics.state_transitions.get("restarted", 0) + 1
        return domain_agent

    async def heartbeat(self, agent_id: str) -> None:
        agent = self._registry.get(agent_id)
        await agent.heartbeat()
        reg = self._registry.get_registration(agent_id)
        reg.statistics.heartbeat_count += 1

    async def checkpoint(self, agent_id: str, data: dict[str, Any]) -> None:
        agent = self._registry.get(agent_id)
        await agent.save_checkpoint(data)
        reg = self._registry.get_registration(agent_id)
        reg.statistics.checkpoint_count += 1

    async def recover(self, agent_id: str, session_id: str = "") -> Agent | None:
        agent = self._registry.get(agent_id)
        try:
            domain_agent = await agent.restart(session_id)
            reg = self._registry.get_registration(agent_id)
            reg.statistics.recovery_count += 1
            reg.statistics.state_transitions["recovered"] = reg.statistics.state_transitions.get("recovered", 0) + 1
            return domain_agent
        except Exception as e:
            logger.error("Recovery failed for agent %s: %s", agent_id, e)
            raise AgentStateError(detail=f"Recovery failed: {e}") from e

    def get_status(self, agent_id: str) -> AgentStatus | None:
        try:
            agent = self._registry.get(agent_id)
            return agent.status
        except Exception:
            return None
