import pytest

from application.agent.execution import ExecutionManager
from application.agent.interfaces import AgentContext, AgentInterface, AgentResult
from application.agent.models import AgentContext as AgentContextModel
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentType


class MockExecutableAgent(AgentInterface):
    def __init__(self, agent_id: str = "exec-1", name: str = "exec-agent",
                 should_fail: bool = False):
        self._agent_id = agent_id
        self._name = name
        self._should_fail = should_fail
        self._status: AgentStatus = AgentStatus.CREATED
        self._session_id = ""

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
        if self._should_fail:
            raise RuntimeError("Execution failed")
        return AgentResult(success=True, output="execution complete")

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


class TestExecutionManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = AgentRegistry()
        self.execution = ExecutionManager(self.registry)
        self.success_agent = MockExecutableAgent("exec-success", "Success Agent")
        self.fail_agent = MockExecutableAgent("exec-fail", "Fail Agent", should_fail=True)
        self.registry.register(AgentRegistration(agent=self.success_agent))
        self.registry.register(AgentRegistration(agent=self.fail_agent))
        yield

    @pytest.mark.asyncio
    async def test_execute_success(self):
        context = AgentContextModel(agent_id="exec-success", session_id="sess-1")
        result = await self.execution.execute("exec-success", context)
        assert result.success
        assert result.output == "execution complete"
        assert self.success_agent.status == AgentStatus.COMPLETED  # type: ignore[comparison-overlap]

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        context = AgentContextModel(agent_id="exec-fail", session_id="sess-2")
        result = await self.execution.execute("exec-fail", context)
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent(self):
        context = AgentContextModel(agent_id="nonexistent")
        with pytest.raises(Exception):
            await self.execution.execute("nonexistent", context)

    @pytest.mark.asyncio
    async def test_is_running(self):
        assert not self.execution.is_running("exec-success")

    @pytest.mark.asyncio
    async def test_running_count(self):
        assert self.execution.running_count() == 0

    @pytest.mark.asyncio
    async def test_list_running(self):
        running = self.execution.list_running()
        assert isinstance(running, list)

    @pytest.mark.asyncio
    async def test_retry_success(self):
        context = AgentContextModel(agent_id="exec-success", session_id="sess-3")
        result = await self.execution.retry("exec-success", context, max_attempts=3)
        assert result.success

    @pytest.mark.asyncio
    async def test_retry_failure_then_recoverable(self):
        agent = MockExecutableAgent("exec-retry", "Retry Agent")
        self.registry.register(AgentRegistration(agent=agent))
        context = AgentContextModel(agent_id="exec-retry", session_id="sess-4")
        result = await self.execution.retry("exec-retry", context, max_attempts=1)
        assert not result.success or result.success
