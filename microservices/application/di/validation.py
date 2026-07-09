from typing import TYPE_CHECKING

from application.di.registry import ServiceLifetime

if TYPE_CHECKING:
    from application.di.container import DependencyContainer


class ContainerValidator:
    def __init__(self, container: "DependencyContainer") -> None:
        self._container = container

    def validate(self) -> list[str]:
        errors: list[str] = []
        registry = self._container.registry

        for key, definition in registry.all().items():
            if definition.lifetime == ServiceLifetime.SINGLETON:
                try:
                    instance = self._container.resolve(definition.interface, definition.name)
                    if instance is None:
                        errors.append(f"Singleton {key} resolved to None")
                except Exception as e:
                    errors.append(f"Singleton {key} resolution failed: {e}")

        return errors
