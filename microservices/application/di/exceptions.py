from application.exceptions import ApplicationError


class DependencyNotRegisteredError(ApplicationError):
    def __init__(self, service_name: str) -> None:
        super().__init__(
            message=f"Dependency not registered: {service_name}",
            detail=service_name,
        )


class CircularDependencyError(ApplicationError):
    def __init__(self, chain: list[str]) -> None:
        super().__init__(
            message=f"Circular dependency detected: {' -> '.join(chain)}",
            detail=" -> ".join(chain),
        )


class ResolutionError(ApplicationError):
    def __init__(self, service_name: str, detail: str | None = None) -> None:
        super().__init__(
            message=f"Failed to resolve dependency: {service_name}",
            detail=detail or service_name,
        )


class ContainerValidationError(ApplicationError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__(
            message="Container validation failed",
            detail="; ".join(errors),
        )


class ServiceLifetimeError(ApplicationError):
    def __init__(self, service_name: str, detail: str) -> None:
        super().__init__(
            message=f"Service lifetime error: {service_name}",
            detail=detail,
        )
