from __future__ import annotations

import logging
from typing import Any

from application.workflow.interfaces import WorkflowEngine
from application.workflow.models import WorkflowDefinition, WorkflowMetadata
from application.workflow.registry import WorkflowRegistration, WorkflowRegistry

logger = logging.getLogger("ai_assistant")


class WorkflowFactory:
    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def create_definition(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        timeout: float = 300.0,
        max_retries: int = 3,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        return WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version=version,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            timeout=timeout,
            max_retries=max_retries,
            tags=tags or [],
            metadata=metadata or {},
        )

    def create_registration(
        self,
        engine: WorkflowEngine,
        definition: WorkflowDefinition,
        metadata: WorkflowMetadata | None = None,
    ) -> WorkflowRegistration:
        return WorkflowRegistration(
            engine=engine,
            definition=definition,
            metadata=metadata or WorkflowMetadata(
                workflow_id=definition.workflow_id,
                name=definition.name,
                version=definition.version,
            ),
        )

    def register_workflow(
        self,
        workflow_id: str,
        engine: WorkflowEngine,
        definition: WorkflowDefinition,
    ) -> WorkflowRegistration:
        registration = self.create_registration(engine, definition)
        self._registry.register(workflow_id, registration)
        return registration


class WorkflowBuilder:
    def __init__(self) -> None:
        self._workflow_id: str = ""
        self._name: str = ""
        self._description: str = ""
        self._version: str = "1.0.0"
        self._input_schema: dict[str, Any] = {}
        self._output_schema: dict[str, Any] = {}
        self._timeout: float = 300.0
        self._max_retries: int = 3
        self._tags: list[str] = []
        self._metadata: dict[str, Any] = {}

    def with_id(self, workflow_id: str) -> WorkflowBuilder:
        self._workflow_id = workflow_id
        return self

    def with_name(self, name: str) -> WorkflowBuilder:
        self._name = name
        return self

    def with_description(self, description: str) -> WorkflowBuilder:
        self._description = description
        return self

    def with_version(self, version: str) -> WorkflowBuilder:
        self._version = version
        return self

    def with_input_schema(self, schema: dict[str, Any]) -> WorkflowBuilder:
        self._input_schema = schema
        return self

    def with_output_schema(self, schema: dict[str, Any]) -> WorkflowBuilder:
        self._output_schema = schema
        return self

    def with_timeout(self, timeout: float) -> WorkflowBuilder:
        self._timeout = timeout
        return self

    def with_max_retries(self, max_retries: int) -> WorkflowBuilder:
        self._max_retries = max_retries
        return self

    def with_tags(self, *tags: str) -> WorkflowBuilder:
        self._tags.extend(tags)
        return self

    def with_metadata(self, metadata: dict[str, Any]) -> WorkflowBuilder:
        self._metadata = metadata
        return self

    def build(self) -> WorkflowDefinition:
        return WorkflowDefinition(
            workflow_id=self._workflow_id,
            name=self._name,
            description=self._description,
            version=self._version,
            input_schema=self._input_schema,
            output_schema=self._output_schema,
            timeout=self._timeout,
            max_retries=self._max_retries,
            tags=list(self._tags),
            metadata=dict(self._metadata),
        )


class WorkflowResolver:
    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def resolve(self, workflow_id: str) -> WorkflowEngine:
        return self._registry.get(workflow_id)

    def resolve_all(self) -> list[WorkflowEngine]:
        return [reg.engine for reg in self._registry.list_workflows()]
