from __future__ import annotations

from typing import Any

from application.workflow.models import WorkflowContext, WorkflowDefinition, WorkflowRequest


class WorkflowValidationError(Exception):
    pass


class WorkflowValidator:
    def validate_definition(self, definition: WorkflowDefinition) -> list[str]:
        errors: list[str] = []
        if not definition.workflow_id:
            errors.append("Workflow ID is required")
        if not definition.name:
            errors.append("Workflow name is required")
        if not definition.version:
            errors.append("Workflow version is required")
        if definition.timeout <= 0:
            errors.append("Workflow timeout must be positive")
        if definition.max_retries < 0:
            errors.append("Workflow max_retries cannot be negative")
        if not isinstance(definition.input_schema, dict):
            errors.append("Workflow input_schema must be a dictionary")
        if not isinstance(definition.output_schema, dict):
            errors.append("Workflow output_schema must be a dictionary")
        return errors

    def validate_request(self, request: WorkflowRequest) -> list[str]:
        errors: list[str] = []
        if not request.workflow_id:
            errors.append("Workflow ID is required in request")
        if not isinstance(request.input_data, dict):
            errors.append("Workflow input_data must be a dictionary")
        return errors

    def validate_context(self, context: WorkflowContext) -> list[str]:
        errors: list[str] = []
        if not context.workflow_id:
            errors.append("Workflow ID is required in context")
        if not isinstance(context.input_data, dict):
            errors.append("Workflow input_data must be a dictionary")
        return errors

    def validate_input(self, definition: WorkflowDefinition, input_data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not definition.input_schema:
            return errors
        for key, expected_type in definition.input_schema.items():
            if key not in input_data:
                errors.append(f"Required input field '{key}' is missing")
                continue
            if isinstance(expected_type, str):
                actual_type = type(input_data[key]).__name__
                if actual_type != expected_type:
                    errors.append(f"Input field '{key}' expected type {expected_type}, got {actual_type}")
        return errors

    def validate_output(self, definition: WorkflowDefinition, output_data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not definition.output_schema:
            return errors
        for key, expected_type in definition.output_schema.items():
            if key in output_data and isinstance(expected_type, str):
                actual_type = type(output_data[key]).__name__
                if actual_type != expected_type:
                    errors.append(f"Output field '{key}' expected type {expected_type}, got {actual_type}")
        return errors

    def can_execute(self, errors: list[str]) -> bool:
        return len(errors) == 0

    def raise_if_invalid(self, errors: list[str]) -> None:
        if errors:
            raise WorkflowValidationError("; ".join(errors))
