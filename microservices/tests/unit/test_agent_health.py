import pytest

from application.agent.health import AgentHealthChecker, AgentRuntimeHealthStatus
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.value_objects import AgentCapability, AgentType
from tests.unit.test_agent_registry import MockAgent


class TestAgentHealthChecker:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = AgentRegistry()
        self.checker = AgentHealthChecker(self.registry)
        self.agent1 = MockAgent("health-1", "Healthy Agent", AgentType.CONVERSATION,
                                {AgentCapability.CONVERSATION})
        self.registry.register(AgentRegistration(agent=self.agent1))
        yield

    @pytest.mark.asyncio
    async def test_check_runtime_healthy(self):
        health = await self.checker.check_runtime()
        assert health.total_agents == 1
        assert health.registered_agents == 1
        assert health.status == AgentRuntimeHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_runtime_empty(self):
        empty_registry = AgentRegistry()
        empty_checker = AgentHealthChecker(empty_registry)
        health = await empty_checker.check_runtime()
        assert health.total_agents == 0
        assert health.status == AgentRuntimeHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_agent(self):
        health = await self.checker.check_agent("health-1")
        assert health.agent_id == "health-1"
        assert health.is_registered
        assert health.is_healthy

    @pytest.mark.asyncio
    async def test_check_nonexistent_agent(self):
        health = await self.checker.check_agent("nonexistent")
        assert not health.is_registered
        assert health.status == AgentRuntimeHealthStatus.UNHEALTHY

    def test_get_cached_none_on_start(self):
        cached = self.checker.get_cached()
        assert cached is None

    @pytest.mark.asyncio
    async def test_get_cached_after_check(self):
        await self.checker.check_runtime()
        cached = self.checker.get_cached()
        assert cached is not None
        assert cached.total_agents == 1
