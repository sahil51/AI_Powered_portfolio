from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from application.agent.exceptions import (
    AgentExecutionError,
)
from application.agent.interfaces import AgentContext, AgentInterface, AgentResult
from application.agent.registry import AgentRegistry
from domain.agent.aggregate import Agent

logger = logging.getLogger("ai_assistant")


class ExecutionManager:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._running: dict[str, asyncio.Task[Any]] = {}
        self._timeouts: dict[str, asyncio.TimerHandle] = {}

    async def execute(
        self,
        agent_id: str,
        context: AgentContext,
        timeout: float = 300.0,
    ) -> AgentResult:
        agent = self._registry.get(agent_id)
        if agent is None:
            raise AgentExecutionError(detail=f"Agent {agent_id} not found")

        if agent_id in self._running:
            raise AgentExecutionError(detail=f"Agent {agent_id} is already running")

        start = time.time()
        task = asyncio.create_task(self._run_agent(agent, context))

        self._running[agent_id] = task
        timeout_handle = None

        if timeout > 0:
            loop = asyncio.get_running_loop()
            timeout_handle = loop.call_later(
                timeout,
                lambda: self._handle_timeout(agent_id, task),
            )
            self._timeouts[agent_id] = timeout_handle

        try:
            result = await task
            elapsed = (time.time() - start) * 1000
            result.latency_ms = elapsed

            stats = self._registry.get_statistics(agent_id)
            stats.total_executions += 1
            if result.success:
                stats.successful_executions += 1
            else:
                stats.failed_executions += 1
            stats.total_latency_ms += elapsed
            stats.avg_latency_ms = stats.total_latency_ms / stats.total_executions
            stats.last_execution_time = time.time()

            return result
        except asyncio.CancelledError:
            elapsed = (time.time() - start) * 1000
            stats = self._registry.get_statistics(agent_id)
            stats.total_executions += 1
            stats.failed_executions += 1
            stats.timeout_count += 1
            return AgentResult(
                success=False,
                error="Execution timed out",
                latency_ms=elapsed,
            )
        finally:
            self._running.pop(agent_id, None)
            handle = self._timeouts.pop(agent_id, None)
            if handle is not None:
                handle.cancel()

    async def pause(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        return await agent.pause(reason)

    async def resume(self, agent_id: str, reason: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        return await agent.resume(reason)

    async def cancel(self, agent_id: str, reason: str = "") -> Agent:
        task = self._running.get(agent_id)
        if task is not None and not task.done():
            task.cancel()
        agent = self._registry.get(agent_id)
        return await agent.cancel(reason)

    async def restart(self, agent_id: str, session_id: str = "") -> Agent:
        agent = self._registry.get(agent_id)
        return await agent.restart(session_id)

    async def retry(
        self,
        agent_id: str,
        context: AgentContext,
        max_attempts: int = 3,
    ) -> AgentResult:
        last_error: str | None = None
        for attempt in range(max_attempts):
            try:
                result = await self.execute(agent_id, context)
                if result.success:
                    stats = self._registry.get_statistics(agent_id)
                    stats.retry_count += attempt
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                logger.warning("Retry %d/%d for agent %s failed: %s", attempt + 1, max_attempts, agent_id, e)
            if attempt < max_attempts - 1:
                await asyncio.sleep(1.0 * (attempt + 1))

        stats = self._registry.get_statistics(agent_id)
        stats.retry_count += max_attempts
        return AgentResult(success=False, error=f"All {max_attempts} retry attempts failed: {last_error}")

    def is_running(self, agent_id: str) -> bool:
        return agent_id in self._running

    def running_count(self) -> int:
        return len(self._running)

    def list_running(self) -> list[str]:
        return list(self._running.keys())

    async def _run_agent(self, agent: AgentInterface, context: AgentContext) -> AgentResult:
        try:
            await agent.initialize(context.session_id)
            await agent.start()
            result = await agent.execute(context)
            if result.success:
                await agent.complete(result.output)
            else:
                await agent.fail(result.error or "Unknown error")
            return result
        except Exception as e:
            try:
                await agent.fail(str(e))
            except Exception:
                pass
            return AgentResult(success=False, error=str(e))

    def _handle_timeout(self, agent_id: str, task: asyncio.Task[Any]) -> None:
        if not task.done():
            task.cancel()
            logger.warning("Agent %s execution timed out, task cancelled", agent_id)
