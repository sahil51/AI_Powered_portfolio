import pytest

from application.agent.interfaces import AgentInterface, AgentResult
from application.agent.lifecycle import LifecycleManager
from application.agent.models import AgentContext
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentType


class MockLifecycleAgent(AgentInterface):
    def __init__(self, agent_id: str = "life-1", name: str = "life-agent"):
        self._agent_id = agent_id
        self._name = name
        self._status: AgentStatus = AgentStatus.CREATED
        self._session_id = ""
        self._checkpoint_data: dict = {}

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
        return self._status in (AgentStatus.RUNNING, AgentStatus.WAITING)

    async def initialize(self, session_id: str = "") -> AgentStatus:
        self._session_id = session_id
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
        self._session_id = session_id
        return self._status

    async def heartbeat(self) -> None:
        pass

    async def save_checkpoint(self, data: dict) -> None:
        self._checkpoint_data = data

    async def cleanup(self) -> None:
        self._status = AgentStatus.ARCHIVED

    async def health_check(self) -> bool:
        return True


class TestLifecycleManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = AgentRegistry()
        self.lifecycle = LifecycleManager(self.registry)
        self.agent = MockLifecycleAgent("life-1", "Life Agent")
        self.registry.register(AgentRegistration(agent=self.agent))
        yield

    @pytest.mark.asyncio
    async def test_initialize(self):
        result = await self.lifecycle.initialize("life-1", "session-1")
        assert result == AgentStatus.INITIALIZED

    @pytest.mark.asyncio
    async def test_start(self):
        await self.lifecycle.initialize("life-1")
        result = await self.lifecycle.start("life-1")
        assert result == AgentStatus.RUNNING

    @pytest.mark.asyncio
    async def test_pause(self):
        await self.lifecycle.initialize("life-1")
        await self.lifecycle.start("life-1")
        result = await self.lifecycle.pause("life-1", "waiting")
        assert result == AgentStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume(self):
        await self.lifecycle.initialize("life-1")
        await self.lifecycle.start("life-1")
        await self.lifecycle.pause("life-1")
        result = await self.lifecycle.resume("life-1", "continue")
        assert result == AgentStatus.RUNNING

    @pytest.mark.asyncio
    async def test_cancel(self):
        result = await self.lifecycle.cancel("life-1", "no_reason")
        assert result == AgentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_complete(self):
        await self.lifecycle.initialize("life-1")
        await self.lifecycle.start("life-1")
        result = await self.lifecycle.complete("life-1", "done")
        assert result == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fail(self):
        await self.lifecycle.initialize("life-1")
        result = await self.lifecycle.fail("life-1", "error")
        assert result == AgentStatus.FAILED

    @pytest.mark.asyncio
    async def test_archive(self):
        await self.lifecycle.archive("life-1", "cleanup")
        assert self.agent.status == AgentStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_restart(self):
        await self.lifecycle.fail("life-1", "error")
        result = await self.lifecycle.restart("life-1", "session-new")
        assert result == AgentStatus.INITIALIZED

    @pytest.mark.asyncio
    async def test_heartbeat(self):
        await self.lifecycle.heartbeat("life-1")

    @pytest.mark.asyncio
    async def test_checkpoint(self):
        await self.lifecycle.checkpoint("life-1", {"step": 1})

    def test_get_status(self):
        status = self.lifecycle.get_status("life-1")
        assert status == AgentStatus.CREATED

    def test_get_status_nonexistent(self):
        status = self.lifecycle.get_status("nonexistent")
        assert status is None
