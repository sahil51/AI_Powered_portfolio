class AppError(Exception):
    status_code: int = 500
    message: str = "Internal server error"
    detail: str | None = None

    def __init__(self, message: str | None = None, detail: str | None = None):
        if message:
            self.message = message
        if detail:
            self.detail = detail
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ValidationError(AppError):
    status_code = 422
    message = "Validation error"


class InfrastructureError(AppError):
    status_code = 503
    message = "Infrastructure unavailable"


class LLMError(InfrastructureError):
    message = "LLM service unavailable"


class WorkflowError(AppError):
    status_code = 502
    message = "Workflow execution failed"


class BusinessError(AppError):
    status_code = 400
    message = "Business rule violation"


__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationError",
    "InfrastructureError",
    "LLMError",
    "WorkflowError",
    "BusinessError",
]
