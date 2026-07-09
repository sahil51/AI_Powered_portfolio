import contextvars
from collections.abc import Callable
from typing import Any

from application.di.exceptions import (
    CircularDependencyError,
    DependencyNotRegisteredError,
    ResolutionError,
)
from application.di.registry import ServiceDefinition, ServiceLifetime, ServiceRegistry
from application.di.validation import ContainerValidator


class DependencyContainer:
    def __init__(self) -> None:
        self._registry = ServiceRegistry()
        self._singletons: dict[str, Any] = {}
        self._resolving: set[str] = set()
        self._scoped_context: contextvars.ContextVar[dict[str, Any] | None] = (
            contextvars.ContextVar("di_scoped", default=None)
        )
        self._validator = ContainerValidator(self)

    @property
    def registry(self) -> ServiceRegistry:
        return self._registry

    def register(
        self,
        interface: type,
        implementation: type,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Callable[..., Any] | None = None,
        name: str | None = None,
    ) -> None:
        self._registry.register(interface, implementation, lifetime, factory, name)

    def register_instance(self, interface: type, instance: Any, name: str | None = None) -> None:
        key = self._key(interface, name)
        self._registry.register(interface, type(instance), ServiceLifetime.SINGLETON, name=name)
        self._singletons[key] = instance

    def has_registration(self, interface: type, name: str | None = None) -> bool:
        return self._registry.has(interface, name)

    def resolve(self, interface: type, name: str | None = None) -> Any:
        key = self._key(interface, name)

        definition = self._registry.get(interface, name)
        if definition is None:
            raise DependencyNotRegisteredError(
                service_name=f"{interface.__module__}.{interface.__qualname__}"
                + (f":{name}" if name else "")
            )

        if definition.lifetime == ServiceLifetime.SINGLETON:
            if key not in self._singletons:
                self._singletons[key] = self._build(definition, key)
            return self._singletons[key]

        if definition.lifetime == ServiceLifetime.SCOPED:
            scoped = self._scoped_context.get()
            if scoped is None:
                raise ResolutionError(
                    service_name=f"{interface.__module__}.{interface.__qualname__}",
                    detail="Scoped service requires an active scope. Use container.scope().",
                )
            if key not in scoped:
                scoped[key] = self._build(definition, key)
            return scoped[key]

        return self._build(definition, key)

    def _build(self, definition: ServiceDefinition, key: str) -> Any:
        if key in self._resolving:
            raise CircularDependencyError(chain=list(self._resolving) + [key])

        self._resolving.add(key)
        try:
            if definition.factory:
                instance = definition.factory()
            else:
                instance = self._construct(definition.implementation)
            return instance
        except CircularDependencyError:
            raise
        except Exception as e:
            raise ResolutionError(
                service_name=key,
                detail=str(e),
            )
        finally:
            self._resolving.discard(key)

    def _construct(self, implementation: type) -> Any:
        import inspect
        import typing

        init = implementation.__init__
        hints = typing.get_type_hints(init)
        sig = inspect.signature(init)
        kwargs: dict[str, Any] = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            annotation: type = hints.get(param_name, param.annotation)  # type: ignore[assignment]
            if annotation is param.empty:
                continue
            origin = typing.get_origin(annotation)
            if origin is not None:
                continue
            try:
                kwargs[param_name] = self.resolve(annotation)
            except DependencyNotRegisteredError:
                if param.default is not param.empty:
                    continue
                raise
        return implementation(**kwargs)

    def scope(self) -> "ScopeContext":
        return ScopeContext(self)

    def validate(self) -> list[str]:
        return self._validator.validate()

    def _key(self, interface: type, name: str | None = None) -> str:
        return f"{interface.__module__}.{interface.__qualname__}" + (f":{name}" if name else "")

    def clear(self) -> None:
        self._registry.clear()
        self._singletons.clear()
        self._resolving.clear()


class ScopeContext:
    def __init__(self, container: DependencyContainer) -> None:
        self._container = container
        self._token: contextvars.Token[dict[str, Any] | None] | None = None
        self._store: dict[str, Any] = {}

    def __enter__(self) -> "ScopeContext":
        self._token = self._container._scoped_context.set(self._store)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._token is not None:
            self._container._scoped_context.reset(self._token)
        self._store.clear()


container = DependencyContainer()
