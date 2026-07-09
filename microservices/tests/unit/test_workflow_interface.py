import pytest

from application.workflow.models import (
    WorkflowContext,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowMetadata,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowResult,
    WorkflowStatus,
)


class TestWorkflowModels:
    def test_workflow_definition_defaults(self):
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test Workflow")
        assert definition.workflow_id == "wf-1"
        assert definition.name == "Test Workflow"
        assert definition.version == "1.0.0"
        assert definition.timeout == 300.0
        assert definition.max_retries == 3

    def test_workflow_context_defaults(self):
        context = WorkflowContext(workflow_id="wf-1")
        assert context.workflow_id == "wf-1"
        assert context.input_data == {}
        assert context.config == {}

    def test_workflow_request_defaults(self):
        request = WorkflowRequest(workflow_id="wf-1")
        assert request.workflow_id == "wf-1"
        assert request.priority == 0

    def test_workflow_response_success(self):
        response = WorkflowResponse(success=True, execution_id="exec-1")
        assert response.success
        assert response.execution_id == "exec-1"
        assert response.status == WorkflowStatus.COMPLETED

    def test_workflow_execution_defaults(self):
        execution = WorkflowExecution(execution_id="exec-1", workflow_id="wf-1")
        assert execution.status == WorkflowStatus.PENDING
        assert execution.retry_count == 0
        assert execution.max_retries == 3

    def test_workflow_result_defaults(self):
        result = WorkflowResult(execution_id="exec-1")
        assert result.success
        assert result.status == WorkflowStatus.COMPLETED
        assert result.steps_completed == 0

    def test_workflow_metadata_defaults(self):
        metadata = WorkflowMetadata(workflow_id="wf-1", name="Test")
        assert metadata.workflow_id == "wf-1"
        assert metadata.version == "1.0.0"
        assert metadata.health


class TestWorkflowValidator:
    def test_validate_definition_valid(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test", version="1.0.0")
        errors = validator.validate_definition(definition)
        assert len(errors) == 0

    def test_validate_definition_missing_id(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        definition = WorkflowDefinition(workflow_id="", name="Test", version="1.0.0")
        errors = validator.validate_definition(definition)
        assert "Workflow ID is required" in errors

    def test_validate_definition_missing_name(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        definition = WorkflowDefinition(workflow_id="wf-1", name="", version="1.0.0")
        errors = validator.validate_definition(definition)
        assert "Workflow name is required" in errors

    def test_validate_request_valid(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        request = WorkflowRequest(workflow_id="wf-1", input_data={"key": "value"})
        errors = validator.validate_request(request)
        assert len(errors) == 0

    def test_validate_request_missing_id(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        request = WorkflowRequest(workflow_id="")
        errors = validator.validate_request(request)
        assert "Workflow ID is required in request" in errors

    def test_validate_context_valid(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        context = WorkflowContext(workflow_id="wf-1")
        errors = validator.validate_context(context)
        assert len(errors) == 0

    def test_can_execute_no_errors(self):
        from application.workflow.validator import WorkflowValidator
        validator = WorkflowValidator()
        assert validator.can_execute([])
        assert not validator.can_execute(["error"])

    def test_raise_if_invalid(self):
        from application.workflow.validator import WorkflowValidationError, WorkflowValidator
        validator = WorkflowValidator()
        with pytest.raises(WorkflowValidationError):
            validator.raise_if_invalid(["error"])
        validator.raise_if_invalid([])


class TestWorkflowRegistry:
    def test_register_and_get(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test")
        registration = WorkflowRegistration(engine=None, definition=definition)  # type: ignore
        registry.register("wf-1", registration)
        assert registry.has_workflow("wf-1")
        assert registry.count() == 1

    def test_register_duplicate_raises(self):
        from application.workflow.exceptions import WorkflowRegistrationError
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test")
        registration = WorkflowRegistration(engine=None, definition=definition)  # type: ignore
        registry.register("wf-1", registration)
        with pytest.raises(WorkflowRegistrationError):
            registry.register("wf-1", registration)

    def test_unregister(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test")
        registration = WorkflowRegistration(engine=None, definition=definition)  # type: ignore
        registry.register("wf-1", registration)
        registry.unregister("wf-1")
        assert not registry.has_workflow("wf-1")

    def test_list_workflows(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        d1 = WorkflowDefinition(workflow_id="wf-1", name="Test1")
        d2 = WorkflowDefinition(workflow_id="wf-2", name="Test2")
        registry.register("wf-1", WorkflowRegistration(engine=None, definition=d1))  # type: ignore
        registry.register("wf-2", WorkflowRegistration(engine=None, definition=d2))  # type: ignore
        assert len(registry.list_workflows()) == 2
        assert len(registry.list_definitions()) == 2

    def test_get_by_tag(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        d1 = WorkflowDefinition(workflow_id="wf-1", name="Test1", tags=["urgent"])
        d2 = WorkflowDefinition(workflow_id="wf-2", name="Test2", tags=["normal"])
        registry.register("wf-1", WorkflowRegistration(engine=None, definition=d1))  # type: ignore
        registry.register("wf-2", WorkflowRegistration(engine=None, definition=d2))  # type: ignore
        urgent = registry.get_by_tag("urgent")
        assert len(urgent) == 1

    def test_mark_health(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(workflow_id="wf-1", name="Test")
        registration = WorkflowRegistration(engine=None, definition=definition)  # type: ignore
        registry.register("wf-1", registration)
        registry.mark_health("wf-1", False)
        reg = registry.get_registration("wf-1")
        assert not reg.healthy

    def test_clear(self):
        from application.workflow.registry import WorkflowRegistration, WorkflowRegistry
        registry = WorkflowRegistry()
        d1 = WorkflowDefinition(workflow_id="wf-1", name="Test1")
        registry.register("wf-1", WorkflowRegistration(engine=None, definition=d1))  # type: ignore
        registry.clear()
        assert registry.count() == 0


class TestWorkflowFactory:
    def test_create_definition(self):
        from application.workflow.factory import WorkflowFactory
        from application.workflow.registry import WorkflowRegistry
        registry = WorkflowRegistry()
        factory = WorkflowFactory(registry)
        definition = factory.create_definition("wf-1", "Test", "A test workflow")
        assert definition.workflow_id == "wf-1"
        assert definition.name == "Test"
        assert definition.description == "A test workflow"

    def test_register_workflow(self):
        from application.workflow.factory import WorkflowFactory
        from application.workflow.registry import WorkflowRegistry
        registry = WorkflowRegistry()
        factory = WorkflowFactory(registry)
        definition = factory.create_definition("wf-1", "Test")
        engine = None
        factory.register_workflow("wf-1", engine, definition)  # type: ignore
        assert registry.count() == 1


class TestWorkflowBuilder:
    def test_build_definition(self):
        from application.workflow.factory import WorkflowBuilder
        builder = WorkflowBuilder()
        definition = (builder
                      .with_id("wf-1")
                      .with_name("Test Workflow")
                      .with_description("A test")
                      .with_version("2.0.0")
                      .with_timeout(600.0)
                      .with_max_retries(5)
                      .with_tags("urgent", "test")
                      .build())
        assert definition.workflow_id == "wf-1"
        assert definition.name == "Test Workflow"
        assert definition.version == "2.0.0"
        assert definition.timeout == 600.0
        assert definition.max_retries == 5
        assert "urgent" in definition.tags

    def test_build_with_schema(self):
        from application.workflow.factory import WorkflowBuilder
        builder = WorkflowBuilder()
        definition = (builder
                      .with_id("wf-2")
                      .with_name("Schema WF")
                      .with_input_schema({"name": "str"})
                      .with_output_schema({"result": "str"})
                      .build())
        assert definition.input_schema == {"name": "str"}
        assert definition.output_schema == {"result": "str"}
