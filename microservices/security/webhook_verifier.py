from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings
from security.exceptions import WebhookVerificationError


@dataclass
class WebhookVerificationResult:
    verified: bool
    error: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


class WebhookVerifier:
    def __init__(self, secret: str = "") -> None:
        self._secret = secret or settings.jwt_secret
        self._max_timestamp_age: int = 300
        self._processed_idempotency_keys: set[str] = set()

    @property
    def secret(self) -> str:
        return self._secret

    def set_secret(self, secret: str) -> None:
        self._secret = secret

    def verify_hmac(self, payload: str, signature: str) -> bool:
        if not self._secret:
            raise WebhookVerificationError(message="Webhook secret not configured")
        expected = hmac.new(
            self._secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_hmac_header(self, payload: str, signature_header: str) -> WebhookVerificationResult:
        try:
            valid = self.verify_hmac(payload, signature_header)
            if valid:
                return WebhookVerificationResult(verified=True)
            return WebhookVerificationResult(
                verified=False,
                error="HMAC signature mismatch",
            )
        except Exception as e:
            return WebhookVerificationResult(
                verified=False,
                error=str(e),
            )

    def validate_timestamp(self, timestamp: float) -> bool:
        now = time.time()
        age = abs(now - timestamp)
        if age > self._max_timestamp_age:
            return False
        return True

    def validate_timestamp_header(self, timestamp_str: str) -> WebhookVerificationResult:
        try:
            timestamp = float(timestamp_str)
            if self.validate_timestamp(timestamp):
                return WebhookVerificationResult(verified=True)
            return WebhookVerificationResult(
                verified=False,
                error="Timestamp outside valid window",
            )
        except (ValueError, TypeError) as e:
            return WebhookVerificationResult(
                verified=False,
                error=f"Invalid timestamp: {e}",
            )

    def check_replay(self, idempotency_key: str) -> WebhookVerificationResult:
        if idempotency_key in self._processed_idempotency_keys:
            return WebhookVerificationResult(
                verified=False,
                error="Replay attack detected: idempotency key already processed",
            )
        self._processed_idempotency_keys.add(idempotency_key)
        return WebhookVerificationResult(verified=True)

    def verify_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: float | None = None,
        idempotency_key: str | None = None,
    ) -> WebhookVerificationResult:
        if not self.verify_hmac(payload, signature):
            return WebhookVerificationResult(
                verified=False,
                error="HMAC signature mismatch",
            )
        if timestamp is not None and not self.validate_timestamp(timestamp):
            return WebhookVerificationResult(
                verified=False,
                error="Timestamp outside valid window",
            )
        if idempotency_key:
            replay_result = self.check_replay(idempotency_key)
            if not replay_result.verified:
                return replay_result
        return WebhookVerificationResult(verified=True)

    def verify_full(
        self,
        payload: str,
        signature: str,
        timestamp_str: str,
        idempotency_key: str,
    ) -> WebhookVerificationResult:
        hmac_result = self.verify_hmac_header(payload, signature)
        if not hmac_result.verified:
            return hmac_result
        ts_result = self.validate_timestamp_header(timestamp_str)
        if not ts_result.verified:
            return ts_result
        replay_result = self.check_replay(idempotency_key)
        if not replay_result.verified:
            return replay_result
        return WebhookVerificationResult(verified=True)
