import pytest

from application.agent.exceptions import AgentNotFoundError, AgentRegistrationError
from application.agent.interfaces import AgentInterface, AgentResult
from application.agent.models import AgentContext
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentPriority, AgentType


class MockAgent(AgentInterface):
    def __init__(self, agent_id: str = "mock-1", name: str = "mock",
                 agent_type: AgentType = AgentType.CUSTOM,
                 capabilities: set[AgentCapability] | None = None):
        self._agent_id = agent_id
        self._name = name
        self._agent_type = agent_type
        self._capabilities = capabilities or set()
        self._status: AgentStatus = AgentStatus.CREATED

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def agent_type(self) -> AgentType:
        return self._agent_type

    @property
    def capabilities(self) -> set[AgentCapability]:
        return self._capabilities

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status in (AgentStatus.RUNNING, AgentStatus.WAITING)

    async def initialize(self, session_id: str = "") -> AgentStatus:
        self._status = AgentStatus.INITIALIZED
        return self._status

    async def start(self) -> AgentStatus:
        self._status = AgentStatus.RUNNING
        return self._status

    async def execute(self, context: AgentContext) -> AgentResult:
        self._status = AgentStatus.RUNNING
        return AgentResult(success=True, output="done")

    async def pause(self, reason: str = "") -> AgentStatus:
        self._status = AgentStatus.PAUSED
        return self._status

    async def resume(self, reason: str = "") -> AgentStatus:
        self._status = AgentStatus.RUNNING
        return self._status

    async def cancel(self, reason: str = "") -> AgentStatus:
        self._status = AgentStatus.CANCELLED
        return self._status

    async def complete(self, result: str = "") -> AgentStatus:
        self._status = AgentStatus.COMPLETED
        return self._status

    async def fail(self, error: str = "", recoverable: bool = False) -> AgentStatus:
        self._status = AgentStatus.FAILED
        return self._status

    async def archive(self, reason: str = "") -> AgentStatus:
        self._status = AgentStatus.ARCHIVED
        return self._status

    async def restart(self, session_id: str = "") -> AgentStatus:
        self._status = AgentStatus.INITIALIZED
        return self._status

    async def heartbeat(self) -> None:
        pass

    async def save_checkpoint(self, data: dict) -> None:
        pass

    async def cleanup(self) -> None:
        self._status = AgentStatus.ARCHIVED

    async def health_check(self) -> bool:
        return True


class TestAgentRegistry:
    def setup_method(self):
        self.registry = AgentRegistry()
        self.agent1 = MockAgent("agent-1", "Agent One", AgentType.CONVERSATION,
                                {AgentCapability.CONVERSATION})
        self.agent2 = MockAgent("agent-2", "Agent Two", AgentType.ANALYSIS,
                                {AgentCapability.ANALYSIS, AgentCapability.CONVERSATION})
        self.agent3 = MockAgent("agent-3", "Agent Three", AgentType.WORKFLOW,
                                {AgentCapability.WORKFLOW_EXECUTION})

    def test_register_agent(self):
        reg = AgentRegistration(agent=self.agent1, name="Agent One", agent_type=AgentType.CONVERSATION)
        self.registry.register(reg)
        assert self.registry.count() == 1
        assert self.registry.has_agent("agent-1")

    def test_register_duplicate_raises(self):
        reg1 = AgentRegistration(agent=self.agent1)
        reg2 = AgentRegistration(agent=self.agent1)
        self.registry.register(reg1)
        with pytest.raises(AgentRegistrationError):
            self.registry.register(reg2)

    def test_unregister_agent(self):
        reg = AgentRegistration(agent=self.agent1)
        self.registry.register(reg)
        self.registry.unregister("agent-1")
        assert not self.registry.has_agent("agent-1")
        assert self.registry.count() == 0

    def test_get_agent(self):
        reg = AgentRegistration(agent=self.agent1)
        self.registry.register(reg)
        agent = self.registry.get("agent-1")
        assert agent.agent_id == "agent-1"

    def test_get_nonexistent_raises(self):
        with pytest.raises(AgentNotFoundError):
            self.registry.get("nonexistent")

    def test_get_by_type(self):
        self.registry.register(AgentRegistration(agent=self.agent1, agent_type=AgentType.CONVERSATION))
        self.registry.register(AgentRegistration(agent=self.agent2, agent_type=AgentType.ANALYSIS))
        agents = self.registry.get_by_type(AgentType.CONVERSATION)
        assert len(agents) == 1
        assert agents[0].agent_id == "agent-1"

    def test_get_by_capability(self):
        self.registry.register(AgentRegistration(agent=self.agent1, capabilities={AgentCapability.CONVERSATION}))
        self.registry.register(AgentRegistration(agent=self.agent2, capabilities={AgentCapability.ANALYSIS}))
        agents = self.registry.get_by_capability(AgentCapability.CONVERSATION)
        assert len(agents) == 1

    def test_get_by_capability_multiple(self):
        self.registry.register(AgentRegistration(agent=self.agent1, capabilities={AgentCapability.CONVERSATION}))
        self.registry.register(AgentRegistration(agent=self.agent2, capabilities={AgentCapability.CONVERSATION}))
        agents = self.registry.get_by_capability(AgentCapability.CONVERSATION)
        assert len(agents) == 2

    def test_list_agents(self):
        self.registry.register(AgentRegistration(agent=self.agent1))
        self.registry.register(AgentRegistration(agent=self.agent2))
        agents = self.registry.list_agents()
        assert len(agents) == 2

    def test_list_types(self):
        self.registry.register(AgentRegistration(agent=self.agent1, agent_type=AgentType.CONVERSATION))
        self.registry.register(AgentRegistration(agent=self.agent2, agent_type=AgentType.ANALYSIS))
        types = self.registry.list_types()
        assert AgentType.CONVERSATION in types
        assert AgentType.ANALYSIS in types

    def test_get_default_agent(self):
        self.registry.register(
            AgentRegistration(agent=self.agent1, agent_type=AgentType.CONVERSATION, priority=AgentPriority.HIGH)
        )
        self.registry.register(
            AgentRegistration(agent=self.agent2, agent_type=AgentType.CONVERSATION, priority=AgentPriority.LOW)
        )
        default = self.registry.get_default_agent(AgentType.CONVERSATION)
        assert default is not None
        assert default.agent_id == "agent-1"

    def test_get_default_agent_no_match(self):
        default = self.registry.get_default_agent(AgentType.CONVERSATION)
        assert default is None

    def test_mark_health(self):
        reg = AgentRegistration(agent=self.agent1)
        self.registry.register(reg)
        self.registry.mark_health("agent-1", False)
        assert not self.registry.get_health("agent-1")

    def test_get_statistics(self):
        reg = AgentRegistration(agent=self.agent1)
        self.registry.register(reg)
        stats = self.registry.get_statistics("agent-1")
        assert stats.total_executions == 0

    def test_get_statistics_nonexistent_raises(self):
        with pytest.raises(AgentNotFoundError):
            self.registry.get_statistics("nonexistent")

    def test_clear(self):
        self.registry.register(AgentRegistration(agent=self.agent1))
        self.registry.register(AgentRegistration(agent=self.agent2))
        self.registry.clear()
        assert self.registry.count() == 0
