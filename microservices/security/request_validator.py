from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import jwt

from config.settings import settings


@dataclass
class RequestValidationResult:
    valid: bool
    error: str = ""
    claims: dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    tenant_id: str = ""


class RequestValidator:
    def __init__(self) -> None:
        self._max_payload_size: int = 1024 * 1024
        self._allowed_content_types: list[str] = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]

    def validate_jwt(self, token: str) -> RequestValidationResult:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            return RequestValidationResult(
                valid=True,
                claims=payload,
                user_id=payload.get("sub", ""),
                tenant_id=payload.get("tenant_id", ""),
            )
        except jwt.ExpiredSignatureError:
            return RequestValidationResult(valid=False, error="Token expired")
        except jwt.InvalidTokenError as e:
            return RequestValidationResult(valid=False, error=f"Invalid token: {e}")

    def validate_headers(self, headers: dict[str, str]) -> RequestValidationResult:
        content_type = headers.get("content-type", "")
        if content_type:
            base_type = content_type.split(";")[0].strip()
            if base_type and base_type not in self._allowed_content_types:
                return RequestValidationResult(
                    valid=False,
                    error=f"Unsupported content type: {content_type}",
                )
        return RequestValidationResult(valid=True)

    def validate_payload_size(self, payload: bytes | str) -> RequestValidationResult:
        size = len(payload) if isinstance(payload, bytes) else len(payload.encode())
        if size > self._max_payload_size:
            return RequestValidationResult(
                valid=False,
                error=f"Payload size {size} exceeds maximum {self._max_payload_size}",
            )
        return RequestValidationResult(valid=True)

    def validate_payload_json(self, payload: str) -> RequestValidationResult:
        try:
            json.loads(payload)
            return RequestValidationResult(valid=True)
        except json.JSONDecodeError as e:
            return RequestValidationResult(
                valid=False,
                error=f"Invalid JSON payload: {e}",
            )

    def validate_tenant(self, request_tenant: str, user_tenants: list[str]) -> RequestValidationResult:
        if request_tenant and user_tenants and request_tenant not in user_tenants:
            return RequestValidationResult(
                valid=False,
                error=f"Tenant {request_tenant} not authorized",
            )
        return RequestValidationResult(valid=True)

    def validate_correlation_id(self, correlation_id: str) -> RequestValidationResult:
        if not correlation_id:
            return RequestValidationResult(valid=False, error="Missing correlation ID")
        if len(correlation_id) > 64:
            return RequestValidationResult(valid=False, error="Correlation ID too long")
        return RequestValidationResult(valid=True)

    def validate_request(
        self,
        token: str | None = None,
        headers: dict[str, str] | None = None,
        payload: bytes | str | None = None,
        correlation_id: str | None = None,
    ) -> RequestValidationResult:
        if token:
            jwt_result = self.validate_jwt(token)
            if not jwt_result.valid:
                return jwt_result
        if headers:
            header_result = self.validate_headers(headers)
            if not header_result.valid:
                return header_result
        if payload:
            size_result = self.validate_payload_size(payload)
            if not size_result.valid:
                return size_result
            if isinstance(payload, bytes):
                payload = payload.decode()
            json_result = self.validate_payload_json(payload)
            if not json_result.valid:
                return json_result
        if correlation_id:
            cid_result = self.validate_correlation_id(correlation_id)
            if not cid_result.valid:
                return cid_result
        return RequestValidationResult(valid=True)
