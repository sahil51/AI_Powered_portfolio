from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


class Initializable(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        ...


class Shutdownable(ABC):
    @abstractmethod
    async def shutdown(self) -> None:
        ...


@dataclass
class StartupHook:
    name: str
    handler: Callable[..., Awaitable[Any]]
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    critical: bool = True


@dataclass
class ShutdownHook:
    name: str
    handler: Callable[..., Awaitable[Any]]
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)


class LifecycleManager:
    def __init__(self) -> None:
        self._startup_hooks: list[StartupHook] = []
        self._shutdown_hooks: list[ShutdownHook] = []
        self._started = False

    def add_startup_hook(self, hook: StartupHook) -> None:
        self._startup_hooks.append(hook)

    def add_shutdown_hook(self, hook: ShutdownHook) -> None:
        self._shutdown_hooks.append(hook)

    async def run_startup(self) -> None:
        sorted_hooks = sorted(self._startup_hooks, key=lambda h: h.priority)
        for hook in sorted_hooks:
            try:
                await hook.handler()
            except Exception:
                if hook.critical:
                    raise
        self._started = True

    async def run_shutdown(self) -> None:
        sorted_hooks = sorted(self._shutdown_hooks, key=lambda h: h.priority, reverse=True)
        for hook in sorted_hooks:
            try:
                await hook.handler()
            except Exception:
                pass
        self._started = False

    @property
    def started(self) -> bool:
        return self._started


lifecycle = LifecycleManager()
