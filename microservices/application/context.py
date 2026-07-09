from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from config.settings import Settings, settings


class ApplicationContext:
    def __init__(self) -> None:
        self._settings: Settings = settings
        self._services: dict[str, Any] = {}
        self._started = False

    @property
    def settings(self) -> Settings:
        return self._settings

    def set(self, key: str, value: Any) -> None:
        self._services[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._services.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._services

    def remove(self, key: str) -> None:
        self._services.pop(key, None)

    def clear(self) -> None:
        self._services.clear()

    @property
    def started(self) -> bool:
        return self._started

    @started.setter
    def started(self, value: bool) -> None:
        self._started = value


app_context = ApplicationContext()


@asynccontextmanager
async def app_context_scope() -> AsyncGenerator[ApplicationContext, None]:
    yield app_context
