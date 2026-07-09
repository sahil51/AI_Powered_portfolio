import pytest

from application.workflow_client.exceptions import (
    WorkflowAuthenticationError,
    WorkflowClientError,
    WorkflowConnectionError,
    WorkflowSerializationError,
    WorkflowTimeoutError,
    WorkflowValidationError,
)
from application.workflow_client.health import WorkflowClientHealthChecker, WorkflowClientHealthStatus
from application.workflow_client.metrics import WorkflowClientMetricsCollector
from application.workflow_client.models import (
    WorkflowConfiguration,
    WorkflowMetadata,
    WorkflowOperation,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowResponseStatus,
    WorkflowResult,
)
from application.workflow_client.serializer import WorkflowSerializer
from application.workflow_client.tracker import WorkflowStatusTracker, WorkflowTrackingStatus
from application.workflow_client.validator import WorkflowValidator


class TestWorkflowModels:
    def test_workflow_request_defaults(self) -> None:
        req = WorkflowRequest(operation=WorkflowOperation.SCHEDULE_MEETING, payload={"title": "Test"})
        assert req.operation == WorkflowOperation.SCHEDULE_MEETING
        assert req.payload == {"title": "Test"}
        assert req.correlation_id == ""

    def test_workflow_response_success(self) -> None:
        resp = WorkflowResponse(
            status=WorkflowResponseStatus.SUCCESS,
            success=True,
            message="Meeting scheduled",
            http_status=200,
        )
        assert resp.success is True
        assert resp.http_status == 200
        assert resp.retry_allowed is False

    def test_workflow_response_failure(self) -> None:
        resp = WorkflowResponse(
            status=WorkflowResponseStatus.FAILURE,
            success=False,
            message="Failed",
            http_status=500,
        )
        assert resp.success is False

    def test_workflow_response_timeout(self) -> None:
        resp = WorkflowResponse(
            status=WorkflowResponseStatus.TIMEOUT,
            success=False,
            http_status=504,
            retry_allowed=True,
        )
        assert resp.retry_allowed is True
        assert resp.success is False

    def test_workflow_result(self) -> None:
        result = WorkflowResult(
            success=True,
            error=None,
            latency_ms=150.0,
            retry_attempt=0,
            correlation_id="corr1",
        )
        assert result.success is True
        assert result.latency_ms == 150.0

    def test_workflow_metadata_defaults(self) -> None:
        meta = WorkflowMetadata()
        assert meta.latency_ms == 0.0
        assert meta.retry_count == 0

    def test_configuration_defaults(self) -> None:
        config = WorkflowConfiguration(base_url="https://n8n.example.com")
        assert config.timeout_seconds == 30.0
        assert config.max_retries == 3

    def test_workflow_operation_values(self) -> None:
        assert WorkflowOperation.SCHEDULE_MEETING.value == "schedule_meeting"
        assert WorkflowOperation.RESCHEDULE_MEETING.value == "reschedule_meeting"
        assert WorkflowOperation.CANCEL_MEETING.value == "cancel_meeting"

    def test_workflow_response_status_values(self) -> None:
        assert WorkflowResponseStatus.SUCCESS.value == "success"
        assert WorkflowResponseStatus.RETRY.value == "retry"
        assert WorkflowResponseStatus.VALIDATION_ERROR.value == "validation_error"


class TestWorkflowSerializer:
    def setup_method(self) -> None:
        self.serializer = WorkflowSerializer()

    def test_serialize_request(self) -> None:
        req = WorkflowRequest(
            operation=WorkflowOperation.SCHEDULE_MEETING,
            payload={"title": "Test"},
            correlation_id="corr1",
        )
        data = self.serializer.serialize_request(req)
        assert data["operation"] == "schedule_meeting"
        assert data["correlation_id"] == "corr1"
        assert data["payload"]["title"] == "Test"

    def test_serialize_request_json(self) -> None:
        req = WorkflowRequest(
            operation=WorkflowOperation.SCHEDULE_MEETING,
            payload={"title": "Test"},
            correlation_id="corr1",
        )
        json_str = self.serializer.serialize_request_json(req)
        assert '"operation": "schedule_meeting"' in json_str

    def test_deserialize_success_response(self) -> None:
        body = '{"status": "success", "message": "OK", "data": {"id": "123"}}'
        resp = self.serializer.deserialize_response(body, 200)
        assert resp.status == WorkflowResponseStatus.SUCCESS
        assert resp.success is True
        assert resp.data["id"] == "123"

    def test_deserialize_failure_response(self) -> None:
        body = '{"status": "failure", "message": "Error"}'
        resp = self.serializer.deserialize_response(body, 400)
        assert resp.status == WorkflowResponseStatus.FAILURE

    def test_deserialize_invalid_json(self) -> None:
        resp = self.serializer.deserialize_response("not json", 200)
        assert resp.status == WorkflowResponseStatus.UNEXPECTED_RESPONSE

    def test_deserialize_empty_body(self) -> None:
        resp = self.serializer.deserialize_response("", 200)
        assert resp.status == WorkflowResponseStatus.SUCCESS

    def test_deserialize_retry_status_code(self) -> None:
        body = '{"message": "rate limited"}'
        resp = self.serializer.deserialize_response(body, 429)
        assert resp.status == WorkflowResponseStatus.RETRY
        assert resp.retry_allowed is True

    def test_deserialize_timeout_status_code(self) -> None:
        resp = self.serializer.deserialize_response("", 504)
        assert resp.status == WorkflowResponseStatus.TIMEOUT

    def test_deserialize_auth_failure(self) -> None:
        resp = self.serializer.deserialize_response("", 403)
        assert resp.status == WorkflowResponseStatus.FAILURE


class TestWorkflowValidator:
    def setup_method(self) -> None:
        self.validator = WorkflowValidator()

    def test_validate_valid_request(self) -> None:
        req = WorkflowRequest(
            operation=WorkflowOperation.SCHEDULE_MEETING,
            payload={"title": "Test"},
            correlation_id="corr1",
        )
        self.validator.validate_request(req)

    def test_validate_missing_operation_raises_error(self) -> None:
        req = WorkflowRequest(operation="", payload={}, correlation_id="corr1")
        with pytest.raises(WorkflowValidationError, match="operation is required"):
            self.validator.validate_request(req)

    def test_validate_missing_correlation_id_raises_error(self) -> None:
        req = WorkflowRequest(operation=WorkflowOperation.SCHEDULE_MEETING, payload={"a": 1})
        with pytest.raises(WorkflowValidationError, match="Correlation ID"):
            self.validator.validate_request(req)

    def test_validate_missing_payload_raises_error(self) -> None:
        req = WorkflowRequest(operation=WorkflowOperation.SCHEDULE_MEETING, payload={}, correlation_id="c1")
        with pytest.raises(WorkflowValidationError, match="payload is required"):
            self.validator.validate_request(req)

    def test_validate_valid_config(self) -> None:
        config = WorkflowConfiguration(base_url="https://example.com")
        self.validator.validate_configuration(config)

    def test_validate_missing_base_url_raises_error(self) -> None:
        config = WorkflowConfiguration(base_url="")
        with pytest.raises(WorkflowValidationError, match="Base URL"):
            self.validator.validate_configuration(config)

    def test_validate_operation_valid(self) -> None:
        assert self.validator.validate_operation("schedule_meeting") is True

    def test_validate_operation_invalid(self) -> None:
        assert self.validator.validate_operation("invalid") is False


class TestWorkflowTracker:
    def setup_method(self) -> None:
        self.tracker = WorkflowStatusTracker()

    def test_start_tracking(self) -> None:
        record = self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        assert record.correlation_id == "corr1"
        assert record.status == WorkflowTrackingStatus.IN_FLIGHT

    def test_complete_tracking(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        record = self.tracker.complete("corr1", True, 150.0)
        assert record is not None
        assert record.status == WorkflowTrackingStatus.SUCCEEDED
        assert record.latency_ms == 150.0

    def test_fail_tracking(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        record = self.tracker.fail("corr1", "Error occurred")
        assert record is not None
        assert record.status == WorkflowTrackingStatus.FAILED
        assert record.error == "Error occurred"

    def test_cancel_tracking(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        record = self.tracker.cancel("corr1")
        assert record is not None
        assert record.status == WorkflowTrackingStatus.CANCELLED

    def test_get_record(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        record = self.tracker.get("corr1")
        assert record is not None
        assert record.correlation_id == "corr1"

    def test_get_nonexistent_record(self) -> None:
        record = self.tracker.get("nonexistent")
        assert record is None

    def test_list_active(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        self.tracker.start("corr2", WorkflowOperation.CANCEL_MEETING)
        self.tracker.complete("corr1", True, 100.0)
        active = self.tracker.list_active()
        assert len(active) == 1
        assert active[0].correlation_id == "corr2"

    def test_clear(self) -> None:
        self.tracker.start("corr1", WorkflowOperation.SCHEDULE_MEETING)
        self.tracker.clear()
        assert self.tracker.get("corr1") is None


class TestWorkflowMetrics:
    def setup_method(self) -> None:
        self.collector = WorkflowClientMetricsCollector()

    def test_initial_metrics(self) -> None:
        assert self.collector.metrics.total_requests == 0

    def test_record_success(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        assert self.collector.metrics.total_requests == 1
        assert self.collector.metrics.successful_requests == 1

    def test_record_failure(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.FAILURE, 100.0)
        assert self.collector.metrics.failed_requests == 1

    def test_record_timeout(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.TIMEOUT, 100.0)
        assert self.collector.metrics.timeout_count == 1

    def test_record_retry(self) -> None:
        self.collector.record_request(
            WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0, retry=True
        )
        assert self.collector.metrics.retry_count == 1

    def test_avg_latency(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 200.0)
        assert self.collector.metrics.avg_latency_ms == 150.0

    def test_requests_by_operation(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        self.collector.record_request(WorkflowOperation.CANCEL_MEETING, WorkflowResponseStatus.SUCCESS, 50.0)
        assert self.collector.metrics.requests_by_operation.get("schedule_meeting") == 1
        assert self.collector.metrics.requests_by_operation.get("cancel_meeting") == 1

    def test_reset(self) -> None:
        self.collector.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        self.collector.reset()
        assert self.collector.metrics.total_requests == 0


class TestWorkflowHealth:
    def setup_method(self) -> None:
        self.checker = WorkflowClientHealthChecker()

    @pytest.mark.asyncio
    async def test_healthy_no_metrics(self) -> None:
        health = await self.checker.check()
        assert health.status == WorkflowClientHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthy_good_metrics(self) -> None:
        metrics = WorkflowClientMetricsCollector()
        metrics.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        health = await self.checker.check(metrics.metrics)
        assert health.status == WorkflowClientHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_degraded_low_success(self) -> None:
        checker = WorkflowClientHealthChecker(min_success_rate=0.9)
        metrics = WorkflowClientMetricsCollector()
        metrics.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.SUCCESS, 100.0)
        metrics.record_request(WorkflowOperation.SCHEDULE_MEETING, WorkflowResponseStatus.FAILURE, 100.0)
        health = await checker.check(metrics.metrics)
        assert health.status == WorkflowClientHealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_consecutive_failures_unhealthy(self) -> None:
        checker = WorkflowClientHealthChecker(max_consecutive_failures=2)
        checker.record_failure("err1")
        checker.record_failure("err2")
        checker.record_failure("err3")
        health = await checker.check()
        assert health.status == WorkflowClientHealthStatus.UNHEALTHY


class TestWorkflowExceptions:
    def test_error_hierarchy(self) -> None:
        assert issubclass(WorkflowConnectionError, WorkflowClientError)
        assert issubclass(WorkflowTimeoutError, WorkflowClientError)
        assert issubclass(WorkflowValidationError, WorkflowClientError)
        assert issubclass(WorkflowAuthenticationError, WorkflowClientError)
        assert issubclass(WorkflowSerializationError, WorkflowClientError)

    def test_error_with_detail(self) -> None:
        err = WorkflowClientError("Failed", detail="Connection refused")
        assert err.detail == "Connection refused"

    def test_connection_error(self) -> None:
        err = WorkflowConnectionError("Could not connect")
        assert err.message == "Could not connect"
