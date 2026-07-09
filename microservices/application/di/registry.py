from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ServiceLifetime(Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


@dataclass
class ServiceDefinition:
    interface: type
    implementation: type
    factory: Callable[..., Any] | None = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    name: str | None = None


class ServiceRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, ServiceDefinition] = {}

    def register(
        self,
        interface: type,
        implementation: type,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Callable[..., Any] | None = None,
        name: str | None = None,
    ) -> None:
        key = self._key(interface, name)
        if key in self._definitions:
            return
        self._definitions[key] = ServiceDefinition(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=lifetime,
            name=name,
        )

    def get(self, interface: type, name: str | None = None) -> ServiceDefinition | None:
        return self._definitions.get(self._key(interface, name))

    def has(self, interface: type, name: str | None = None) -> bool:
        return self._key(interface, name) in self._definitions

    def all(self) -> dict[str, ServiceDefinition]:
        return dict(self._definitions)

    def clear(self) -> None:
        self._definitions.clear()

    def _key(self, interface: type, name: str | None = None) -> str:
        return f"{interface.__module__}.{interface.__qualname__}" + (f":{name}" if name else "")
