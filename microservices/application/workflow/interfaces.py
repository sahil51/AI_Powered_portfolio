from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from application.workflow.models import (
    WorkflowContext,
    WorkflowDefinition,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowResult,
)


class WorkflowEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def execute(self, request: WorkflowRequest) -> WorkflowResponse:
        ...

    @abstractmethod
    async def execute_with_context(self, definition: WorkflowDefinition, context: WorkflowContext) -> WorkflowResult:
        ...

    @abstractmethod
    async def resume(self, execution_id: str, context: WorkflowContext | None = None) -> WorkflowResponse:
        ...

    @abstractmethod
    async def pause(self, execution_id: str, reason: str = "") -> WorkflowResponse:
        ...

    @abstractmethod
    async def cancel(self, execution_id: str, reason: str = "") -> WorkflowResponse:
        ...

    @abstractmethod
    async def retry(self, execution_id: str, context: WorkflowContext | None = None) -> WorkflowResponse:
        ...

    @abstractmethod
    async def checkpoint(self, execution_id: str, data: dict[str, Any]) -> WorkflowResponse:
        ...

    @abstractmethod
    async def recover(self, execution_id: str, context: WorkflowContext | None = None) -> WorkflowResponse:
        ...

    @abstractmethod
    async def get_status(self, execution_id: str) -> str:
        ...

    @abstractmethod
    async def get_result(self, execution_id: str) -> WorkflowResult | None:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    async def initialize(self) -> None:
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...


class WorkflowStep(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        ...

    @abstractmethod
    async def compensate(self, context: WorkflowContext) -> WorkflowContext:
        ...
