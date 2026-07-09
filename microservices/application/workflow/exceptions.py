from exceptions.base import AppError


class WorkflowError(AppError):
    status_code: int = 502
    message: str = "Workflow error"

    def __init__(self, message: str | None = None, detail: str | None = None, workflow_id: str | None = None) -> None:
        self.workflow_id = workflow_id
        super().__init__(message=message or self.message, detail=detail)


class WorkflowNotFoundError(WorkflowError):
    status_code: int = 404
    message: str = "Workflow not found"


class WorkflowConfigurationError(WorkflowError):
    status_code: int = 500
    message: str = "Workflow configuration error"


class WorkflowExecutionError(WorkflowError):
    status_code: int = 500
    message: str = "Workflow execution error"


class WorkflowTimeoutError(WorkflowError):
    status_code: int = 504
    message: str = "Workflow timeout"


class WorkflowStateError(WorkflowError):
    status_code: int = 409
    message: str = "Workflow state error"


class WorkflowValidationError(WorkflowError):
    status_code: int = 422
    message: str = "Workflow validation error"


class WorkflowRegistrationError(WorkflowError):
    status_code: int = 409
    message: str = "Workflow registration error"


class WorkflowRecoveryError(WorkflowError):
    status_code: int = 500
    message: str = "Workflow recovery error"


class WorkflowNotImplementedError(WorkflowError):
    status_code: int = 501
    message: str = "Workflow not implemented"
