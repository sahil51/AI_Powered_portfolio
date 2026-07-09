from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid

import aiohttp

from application.workflow_client.exceptions import (
    WorkflowAuthenticationError,
    WorkflowClientError,
    WorkflowConnectionError,
    WorkflowTimeoutError,
)
from application.workflow_client.interfaces import WorkflowClient
from application.workflow_client.metrics import WorkflowClientMetricsCollector
from application.workflow_client.models import (
    WorkflowConfiguration,
    WorkflowMetadata,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowResponseStatus,
)
from application.workflow_client.serializer import WorkflowSerializer
from application.workflow_client.tracker import WorkflowStatusTracker
from application.workflow_client.validator import WorkflowValidator

logger = logging.getLogger("ai_assistant")


class WebhookWorkflowClient(WorkflowClient):
    def __init__(
        self,
        config: WorkflowConfiguration,
        serializer: WorkflowSerializer | None = None,
        validator: WorkflowValidator | None = None,
        tracker: WorkflowStatusTracker | None = None,
        metrics_collector: WorkflowClientMetricsCollector | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._config = config
        self._serializer = serializer or WorkflowSerializer()
        self._validator = validator or WorkflowValidator()
        self._tracker = tracker or WorkflowStatusTracker()
        self._metrics = metrics_collector or WorkflowClientMetricsCollector()
        self._session = session
        self._owned_session = session is None

    @property
    def configuration(self) -> WorkflowConfiguration:
        return self._config

    async def execute(self, request: WorkflowRequest) -> WorkflowResponse:
        self._validator.validate_configuration(self._config)
        self._validator.validate_request(request)

        if not request.correlation_id:
            request.correlation_id = str(uuid.uuid4())
        if self._config.enable_idempotency and not request.idempotency_key:
            request.idempotency_key = str(uuid.uuid4())

        tracking = self._tracker.start(
            request.correlation_id,
            request.operation,
            self._config.max_retries,
        )

        last_error: str | None = None
        start_time = time.time()

        for attempt in range(self._config.max_retries + 1):
            tracking.attempt = attempt

            try:
                response = await self._send_request(request, attempt)
                latency_ms = (time.time() - start_time) * 1000

                self._metrics.record_request(
                    request.operation, response.status, latency_ms, retry=attempt > 0
                )

                is_retry = response.retry_allowed and attempt < self._config.max_retries
                if is_retry:
                    delay = self._get_retry_delay(attempt)
                    logger.info(
                        "Retrying workflow %s (attempt %d/%d) after %.1fs",
                        request.correlation_id,
                        attempt + 1,
                        self._config.max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                if response.status == WorkflowResponseStatus.SUCCESS:
                    self._tracker.complete(request.correlation_id, True, latency_ms)
                else:
                    self._tracker.fail(
                        request.correlation_id,
                        response.message or f"Status: {response.status.value}",
                    )

                response.metadata = WorkflowMetadata(
                    latency_ms=latency_ms,
                    retry_count=attempt,
                    status_code=response.http_status,
                )
                return response

            except WorkflowClientError as e:
                last_error = str(e)
                if attempt < self._config.max_retries:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        "Workflow error (attempt %d/%d): %s, retrying in %.1fs",
                        attempt + 1,
                        self._config.max_retries,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    latency_ms = (time.time() - start_time) * 1000
                    self._metrics.record_request(
                        request.operation,
                        WorkflowResponseStatus.FAILURE,
                        latency_ms,
                        retry=attempt > 0,
                    )
                    self._tracker.fail(request.correlation_id, str(e))
                    raise

        latency_ms = (time.time() - start_time) * 1000
        self._tracker.fail(request.correlation_id, last_error or "Max retries exceeded")
        return WorkflowResponse(
            status=WorkflowResponseStatus.FAILURE,
            success=False,
            message=last_error or "Max retries exceeded",
        )

    async def cancel(self, correlation_id: str) -> bool:
        record = self._tracker.cancel(correlation_id)
        return record is not None

    async def health_check(self) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = self._build_url("health")
                async with session.get(url) as resp:
                    return resp.status < 500
        except Exception:
            return False

    async def _send_request(self, request: WorkflowRequest, attempt: int) -> WorkflowResponse:
        serialized = self._serializer.serialize_request(request)
        url = self._build_url(request.operation.value)
        headers = self._build_headers(request)
        body = json.dumps(serialized)
        timeout_seconds = request.timeout_seconds or self._config.timeout_seconds

        if self._config.enable_hmac_signature:
            signature = self._compute_hmac(body)
            headers["X-Signature"] = signature

        headers["Content-Type"] = "application/json"
        if request.correlation_id:
            headers["X-Correlation-Id"] = request.correlation_id
        if request.idempotency_key:
            headers["X-Idempotency-Key"] = request.idempotency_key

        headers.update(self._config.headers)
        headers.update(request.headers)

        session = await self._get_session()
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        try:
            async with session.post(
                url, data=body, headers=headers, timeout=timeout
            ) as resp:
                response_body = await resp.text()
                response = self._serializer.deserialize_response_json(
                    response_body, resp.status
                )
                response.correlation_id = request.correlation_id
                return response
        except asyncio.TimeoutError:
            raise WorkflowTimeoutError(
                f"Workflow request timed out after {timeout_seconds}s",
                detail=f"Operation: {request.operation.value}",
            )
        except aiohttp.ClientConnectorError as e:
            raise WorkflowConnectionError(
                f"Connection failed to {url}",
                detail=str(e),
            )
        except aiohttp.ClientResponseError as e:
            if e.status in (401, 403):
                raise WorkflowAuthenticationError(
                    f"Authentication failed with status {e.status}",
                    detail=str(e),
                )
            raise WorkflowClientError(
                f"HTTP error {e.status} from {url}",
                detail=str(e),
            )

    def _build_url(self, path: str) -> str:
        base = self._config.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _build_headers(self, request: WorkflowRequest) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    def _compute_hmac(self, body: str) -> str:
        secret = self._config.hmac_secret.encode() if self._config.hmac_secret else b""
        signature = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
        return signature

    def _get_retry_delay(self, attempt: int) -> float:
        delay = self._config.retry_delay_seconds * (
            self._config.retry_backoff_multiplier ** attempt
        )
        return min(delay, 30.0)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owned_session = True
        return self._session

    async def close(self) -> None:
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()
