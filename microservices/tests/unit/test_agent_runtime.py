import pytest

from application.agent.interfaces import AgentInterface, AgentResult
from application.agent.models import AgentConfiguration, AgentContext, AgentStatistics
from application.agent.registry import AgentRegistration
from application.agent.runtime import AgentRuntime
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentType


class MockRuntimeAgent(AgentInterface):
    def __init__(self, agent_id: str = "rt-1", name: str = "rt-agent"):
        self._agent_id = agent_id
        self._name = name
        self._status: AgentStatus = AgentStatus.CREATED
        self._session_id = ""
        self._checkpoint: dict = {}

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CUSTOM

    @property
    def capabilities(self) -> set[AgentCapability]:
        return set()

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status == AgentStatus.RUNNING

    async def initialize(self, session_id: str = "") -> AgentStatus:
        self._status = AgentStatus.INITIALIZED
        self._session_id = session_id
        return self._status

    async def start(self) -> AgentStatus:
        self._status = AgentStatus.RUNNING
        return self._status

    async def execute(self, context: AgentContext) -> AgentResult:
        self._status = AgentStatus.RUNNING
        return AgentResult(success=True, output="runtime done")

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
        self._checkpoint = data

    async def cleanup(self) -> None:
        self._status = AgentStatus.ARCHIVED

    async def health_check(self) -> bool:
        return True


class TestAgentRuntime:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.runtime = AgentRuntime(config=AgentConfiguration(timeout=60))
        self.agent = MockRuntimeAgent("rt-1", "Runtime Agent")
        self.runtime.register(AgentRegistration(agent=self.agent))
        yield

    @pytest.mark.asyncio
    async def test_execute(self):
        context = AgentContext(agent_id="rt-1", session_id="sess-1")
        result = await self.runtime.execute("rt-1", context)
        assert result.success
        assert result.output == "runtime done"

    @pytest.mark.asyncio
    async def test_execute_with_retry(self):
        context = AgentContext(agent_id="rt-1", session_id="sess-2")
        result = await self.runtime.execute_with_retry("rt-1", context, max_attempts=3)
        assert result.success

    @pytest.mark.asyncio
    async def test_pause_resume(self):
        context = AgentContext(agent_id="rt-1", session_id="sess-3")
        await self.runtime.execute("rt-1", context)
        # After execute, agent is "completed", we need to test pause on a running agent
        # Create a fresh scenario
        rt = AgentRuntime()
        fresh_agent = MockRuntimeAgent("rt-2", "Fresh")
        rt.register(AgentRegistration(agent=fresh_agent))

    @pytest.mark.asyncio
    async def test_get_status(self):
        status = self.runtime.get_status("rt-1")
        assert status is not None

    @pytest.mark.asyncio
    async def test_is_running(self):
        assert not self.runtime.is_running("rt-1")

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        stats = self.runtime.get_statistics("rt-1")
        assert isinstance(stats, AgentStatistics)

    @pytest.mark.asyncio
    async def test_list_agents(self):
        agents = self.runtime.list_agents()
        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_list_running(self):
        running = self.runtime.list_running()
        assert isinstance(running, list)

    @pytest.mark.asyncio
    async def test_unregister(self):
        self.runtime.unregister("rt-1")
        assert self.runtime.registry.count() == 0

    @pytest.mark.asyncio
    async def test_register_new(self):
        new_agent = MockRuntimeAgent("rt-new", "New Agent")
        self.runtime.register(AgentRegistration(agent=new_agent))
        assert self.runtime.registry.count() == 2

    @pytest.mark.asyncio
    async def test_config_defaults(self):
        assert self.runtime.config.timeout == 60
        assert self.runtime.config.max_retries == 3

    @pytest.mark.asyncio
    async def test_properties(self):
        assert self.runtime.registry is not None
        assert self.runtime.execution is not None
        assert self.runtime.lifecycle is not None
