from __future__ import annotations

from application.workflow_client.exceptions import WorkflowValidationError
from application.workflow_client.models import (
    WorkflowConfiguration,
    WorkflowOperation,
    WorkflowRequest,
    WorkflowResponse,
)


class WorkflowValidator:
    def validate_request(self, request: WorkflowRequest) -> None:
        if not request.operation:
            raise WorkflowValidationError("Workflow operation is required")
        if not request.correlation_id:
            raise WorkflowValidationError("Correlation ID is required")
        if not request.payload:
            raise WorkflowValidationError("Workflow payload is required")

    def validate_configuration(self, config: WorkflowConfiguration) -> None:
        if not config.base_url:
            raise WorkflowValidationError("Base URL is required")
        if config.timeout_seconds <= 0:
            raise WorkflowValidationError("Timeout must be positive")
        if config.max_retries < 0:
            raise WorkflowValidationError("Max retries cannot be negative")

    def validate_response(self, response: WorkflowResponse) -> bool:
        if not response.status:
            raise WorkflowValidationError("Response status is required")
        return True

    def validate_operation(self, operation: str) -> bool:
        try:
            WorkflowOperation(operation)
            return True
        except ValueError:
            return False
