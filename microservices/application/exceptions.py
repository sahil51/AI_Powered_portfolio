from exceptions.base import AppError


class ApplicationError(AppError):
    status_code: int = 500

    def __init__(self, message: str = "Application error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class ServiceError(ApplicationError):
    def __init__(self, message: str = "Service error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class ServiceValidationError(ApplicationError):
    status_code: int = 422

    def __init__(self, message: str = "Service validation error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class BootstrapError(ApplicationError):
    def __init__(self, message: str = "Bootstrap failed", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)
