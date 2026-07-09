from __future__ import annotations

from exceptions.base import AppError


class PipelineError(AppError):
    status_code: int = 500
    message: str = "Pipeline error"

    def __init__(self, message: str | None = None, detail: str | None = None, stage: str | None = None) -> None:
        super().__init__(message=message or self.message, detail=detail)
        self.stage = stage


class PipelineConfigurationError(PipelineError):
    status_code: int = 500
    message: str = "Pipeline configuration error"


class PipelineTimeoutError(PipelineError):
    status_code: int = 504
    message: str = "Pipeline timeout"


class PipelineValidationError(PipelineError):
    status_code: int = 422
    message: str = "Pipeline validation error"


class PipelineBudgetExceededError(PipelineError):
    status_code: int = 400
    message: str = "Token budget exceeded"


class PipelineProviderError(PipelineError):
    status_code: int = 503
    message: str = "Pipeline provider error"


class PipelineContextError(PipelineError):
    status_code: int = 404
    message: str = "Pipeline context error"


class PipelinePromptError(PipelineError):
    status_code: int = 404
    message: str = "Pipeline prompt error"
