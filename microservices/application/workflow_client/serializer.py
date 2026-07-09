from __future__ import annotations

import json
from typing import Any

from application.workflow_client.exceptions import WorkflowSerializationError
from application.workflow_client.models import (
    WorkflowRequest,
    WorkflowResponse,
    WorkflowResponseStatus,
)


class WorkflowSerializer:
    def serialize_request(self, request: WorkflowRequest) -> dict[str, Any]:
        try:
            return {
                "operation": request.operation.value,
                "correlation_id": request.correlation_id,
                "idempotency_key": request.idempotency_key,
                "payload": request.payload,
                "metadata": request.metadata,
            }
        except Exception as e:
            raise WorkflowSerializationError(
                f"Failed to serialize workflow request: {e}",
                detail=str(e),
            )

    def serialize_request_json(self, request: WorkflowRequest) -> str:
        data = self.serialize_request(request)
        try:
            return json.dumps(data)
        except Exception as e:
            raise WorkflowSerializationError(
                f"Failed to serialize request to JSON: {e}",
                detail=str(e),
            )

    def deserialize_response(self, body: str, status_code: int) -> WorkflowResponse:
        try:
            data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            return WorkflowResponse(
                status=WorkflowResponseStatus.UNEXPECTED_RESPONSE,
                success=False,
                message="Invalid JSON response",
                http_status=status_code,
            )

        status = self._resolve_status(data.get("status", ""), status_code)
        return WorkflowResponse(
            status=status,
            success=status == WorkflowResponseStatus.SUCCESS,
            message=data.get("message", ""),
            data=data.get("data", {}),
            http_status=status_code,
            retry_allowed=status in (
                WorkflowResponseStatus.RETRY,
                WorkflowResponseStatus.TIMEOUT,
            ),
            correlation_id=data.get("correlation_id", ""),
        )

    def deserialize_response_json(self, body: str, status_code: int) -> WorkflowResponse:
        return self.deserialize_response(body, status_code)

    def _resolve_status(
        self, status_str: str, status_code: int
    ) -> WorkflowResponseStatus:
        try:
            return WorkflowResponseStatus(status_str)
        except ValueError:
            pass

        if 200 <= status_code < 300:
            return WorkflowResponseStatus.SUCCESS
        if status_code == 400:
            return WorkflowResponseStatus.VALIDATION_ERROR
        if status_code == 401 or status_code == 403:
            return WorkflowResponseStatus.FAILURE
        if status_code == 408 or status_code == 504:
            return WorkflowResponseStatus.TIMEOUT
        if status_code == 429:
            return WorkflowResponseStatus.RETRY
        if 500 <= status_code < 600:
            return WorkflowResponseStatus.RETRY
        return WorkflowResponseStatus.UNEXPECTED_RESPONSE
