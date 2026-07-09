from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from application.agent.models import AgentContext
from domain.agent.aggregate import Agent
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentType


class AgentInterface(ABC):
    @property
    @abstractmethod
    def agent_id(self) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        ...

    @property
    @abstractmethod
    def capabilities(self) -> set[AgentCapability]:
        ...

    @property
    @abstractmethod
    def status(self) -> AgentStatus:
        ...

    @property
    @abstractmethod
    def is_active(self) -> bool:
        ...

    @abstractmethod
    async def initialize(self, session_id: str = "") -> Agent:
        ...

    @abstractmethod
    async def start(self) -> Agent:
        ...

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def pause(self, reason: str = "") -> Agent:
        ...

    @abstractmethod
    async def resume(self, reason: str = "") -> Agent:
        ...

    @abstractmethod
    async def cancel(self, reason: str = "") -> Agent:
        ...

    @abstractmethod
    async def complete(self, result: str = "") -> Agent:
        ...

    @abstractmethod
    async def fail(self, error: str = "", recoverable: bool = False) -> Agent:
        ...

    @abstractmethod
    async def archive(self, reason: str = "") -> Agent:
        ...

    @abstractmethod
    async def restart(self, session_id: str = "") -> Agent:
        ...

    @abstractmethod
    async def heartbeat(self) -> None:
        ...

    @abstractmethod
    async def save_checkpoint(self, data: dict) -> None:
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


class AgentResult:
    def __init__(
        self,
        success: bool = True,
        output: str = "",
        data: dict[str, Any] | None = None,
        error: str | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        self.success = success
        self.output = output
        self.data = data or {}
        self.error = error
        self.latency_ms = latency_ms



