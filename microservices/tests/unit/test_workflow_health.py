import pytest

from application.workflow.health import (
    WorkflowEngineHealth,
    WorkflowEngineHealthStatus,
    WorkflowHealthChecker,
    WorkflowRegistryHealth,
)
from application.workflow.models import WorkflowDefinition
from application.workflow.registry import WorkflowRegistration, WorkflowRegistry


class MockWorkflowEngine:
    def __init__(self, name: str = "mock-engine", healthy: bool = True):
        self._name = name
        self._healthy = healthy

    @property
    def name(self) -> str:
        return self._name

    async def health_check(self) -> bool:
        return self._healthy


class TestWorkflowHealthChecker:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = WorkflowRegistry()
        self.checker = WorkflowHealthChecker(self.registry)
        self.engine1 = MockWorkflowEngine("engine-1", True)
        self.definition1 = WorkflowDefinition(workflow_id="wf-1", name="Workflow 1")
        self.registry.register("wf-1", WorkflowRegistration(engine=self.engine1, definition=self.definition1))
        yield

    @pytest.mark.asyncio
    async def test_check_registry_healthy(self):
        health = await self.checker.check_registry()
        assert health.total_workflows == 1
        assert health.healthy_workflows == 1
        assert health.status == WorkflowEngineHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_registry_empty(self):
        empty_registry = WorkflowRegistry()
        empty_checker = WorkflowHealthChecker(empty_registry)
        health = await empty_checker.check_registry()
        assert health.total_workflows == 0
        assert health.status == WorkflowEngineHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_registry_degraded(self):
        unhealthy_engine = MockWorkflowEngine("engine-2", False)
        unhealthy_def = WorkflowDefinition(workflow_id="wf-2", name="Workflow 2")
        self.registry.register("wf-2", WorkflowRegistration(engine=unhealthy_engine, definition=unhealthy_def))
        health = await self.checker.check_registry()
        assert health.total_workflows == 2
        assert health.status == WorkflowEngineHealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_engine(self):
        health = await self.checker.check_engine("wf-1")
        assert health.workflow_id == "wf-1"
        assert health.is_registered
        assert health.is_healthy

    @pytest.mark.asyncio
    async def test_check_nonexistent_engine(self):
        health = await self.checker.check_engine("nonexistent")
        assert not health.is_healthy
        assert health.status == WorkflowEngineHealthStatus.UNHEALTHY

    def test_get_cached_none(self):
        assert self.checker.get_cached() is None

    @pytest.mark.asyncio
    async def test_get_cached_after_check(self):
        await self.checker.check_registry()
        cached = self.checker.get_cached()
        assert cached is not None
        assert cached.total_workflows == 1

    def test_workflow_engine_health_defaults(self):
        health = WorkflowEngineHealth()
        assert health.status == WorkflowEngineHealthStatus.UNKNOWN
        assert not health.is_healthy

    def test_workflow_registry_health_defaults(self):
        health = WorkflowRegistryHealth()
        assert health.status == WorkflowEngineHealthStatus.UNKNOWN
        assert not health.is_healthy
