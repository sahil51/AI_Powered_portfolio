from __future__ import annotations


class WorkflowClientError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class WorkflowConnectionError(WorkflowClientError):
    pass


class WorkflowTimeoutError(WorkflowClientError):
    pass


class WorkflowValidationError(WorkflowClientError):
    pass


class WorkflowAuthenticationError(WorkflowClientError):
    pass


class WorkflowSerializationError(WorkflowClientError):
    pass
