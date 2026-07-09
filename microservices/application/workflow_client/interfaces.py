from __future__ import annotations

from abc import ABC, abstractmethod

from application.workflow_client.models import (
    WorkflowConfiguration,
    WorkflowRequest,
    WorkflowResponse,
)


class WorkflowClient(ABC):
    @abstractmethod
    async def execute(self, request: WorkflowRequest) -> WorkflowResponse:
        ...

    @abstractmethod
    async def cancel(self, correlation_id: str) -> bool:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @property
    @abstractmethod
    def configuration(self) -> WorkflowConfiguration:
        ...
