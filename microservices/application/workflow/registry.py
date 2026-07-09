from __future__ import annotations

import logging

from application.workflow.exceptions import WorkflowNotFoundError, WorkflowRegistrationError
from application.workflow.interfaces import WorkflowEngine
from application.workflow.models import WorkflowDefinition, WorkflowMetadata

logger = logging.getLogger("ai_assistant")


class WorkflowRegistration:
    def __init__(
        self,
        engine: WorkflowEngine,
        definition: WorkflowDefinition,
        metadata: WorkflowMetadata | None = None,
    ) -> None:
        self.engine = engine
        self.definition = definition
        self.metadata = metadata or WorkflowMetadata(
            workflow_id=definition.workflow_id,
            name=definition.name,
            version=definition.version,
        )
        self.healthy: bool = True


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowRegistration] = {}

    def register(self, workflow_id: str, registration: WorkflowRegistration) -> None:
        if workflow_id in self._workflows:
            raise WorkflowRegistrationError(detail=f"Workflow {workflow_id} already registered")
        self._workflows[workflow_id] = registration
        logger.info("Workflow registered: %s (v%s)", registration.definition.name, registration.definition.version)

    def unregister(self, workflow_id: str) -> None:
        self._workflows.pop(workflow_id, None)
        logger.info("Workflow unregistered: %s", workflow_id)

    def get(self, workflow_id: str) -> WorkflowEngine:
        registration = self._workflows.get(workflow_id)
        if registration is None:
            raise WorkflowNotFoundError(detail=f"Workflow {workflow_id} not found")
        return registration.engine

    def get_definition(self, workflow_id: str) -> WorkflowDefinition:
        registration = self._workflows.get(workflow_id)
        if registration is None:
            raise WorkflowNotFoundError(detail=f"Workflow {workflow_id} not found")
        return registration.definition

    def get_registration(self, workflow_id: str) -> WorkflowRegistration:
        registration = self._workflows.get(workflow_id)
        if registration is None:
            raise WorkflowNotFoundError(detail=f"Workflow {workflow_id} not found")
        return registration

    def list_workflows(self) -> list[WorkflowRegistration]:
        return list(self._workflows.values())

    def list_definitions(self) -> list[WorkflowDefinition]:
        return [reg.definition for reg in self._workflows.values()]

    def has_workflow(self, workflow_id: str) -> bool:
        return workflow_id in self._workflows

    def count(self) -> int:
        return len(self._workflows)

    def get_by_tag(self, tag: str) -> list[WorkflowRegistration]:
        return [
            reg for reg in self._workflows.values()
            if tag in reg.definition.tags
        ]

    def mark_health(self, workflow_id: str, healthy: bool) -> None:
        registration = self._workflows.get(workflow_id)
        if registration:
            registration.healthy = healthy

    def clear(self) -> None:
        self._workflows.clear()
