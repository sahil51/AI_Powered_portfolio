import hashlib
import hmac
import time

import jwt
import pytest

from config.settings import settings
from security.manager import SecurityManager


class TestSecurityIntegration:
    @pytest.fixture
    async def manager(self):
        import os
        os.environ["JWT_SECRET"] = settings.jwt_secret
        mgr = SecurityManager()
        await mgr.initialize()
        yield mgr
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_secrets_to_encryption_flow(self, manager):
        secret_value = manager.secrets_manager.get_secret("JWT_SECRET")
        assert secret_value == "super-secret-key-change-in-production"

        encrypted = manager.encryption_service.encrypt("sensitive-data")
        decrypted = manager.encryption_service.decrypt(encrypted)
        assert decrypted == "sensitive-data"

    @pytest.mark.asyncio
    async def test_jwt_validation_flow(self, manager):
        token = jwt.encode(
            {"sub": "user-1", "tenant_id": "tenant-1", "role": "admin"},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        result = manager.request_validator.validate_jwt(token)
        assert result.valid
        assert result.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_webhook_verification_flow(self, manager):
        payload = '{"event": "test"}'
        signature = hmac.new(
            manager.webhook_verifier.secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        timestamp = str(time.time())
        idempotency_key = "unique-123"

        result = manager.webhook_verifier.verify_full(payload, signature, timestamp, idempotency_key)
        assert result.verified

    @pytest.mark.asyncio
    async def test_rate_limit_then_circuit_breaker(self, manager):
        for _ in range(5):
            try:
                manager.rate_limit_manager.validate(manager.rate_limit_manager.get_rules()[0].scope, "heavy-user")
            except Exception:
                pass

        manager.circuit_breaker_registry.register("api-call", failure_threshold=3, reset_timeout_seconds=60)
        for _ in range(3):
            manager.circuit_breaker_registry.record_failure("api-call")

        available = manager.circuit_breaker_registry.is_available("api-call")
        assert not available

    @pytest.mark.asyncio
    async def test_audit_and_permission_flow(self, manager):
        manager.audit_logger.record_authentication("user-1", outcome="success")
        manager.audit_logger.record_authorization("user-1", "document", outcome="denied")
        manager.audit_logger.record_workflow_execution("wf-1")

        entries = manager.audit_logger.get_entries()
        assert len(entries) >= 3

        assert manager.permission_validator.has_permission("admin", "audit:read")

    @pytest.mark.asyncio
    async def test_resilience_with_circuit_breaker_and_retry(self, manager):
        call_count = [0]

        async def fail_then_succeed():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("temporary failure")
            return "success"

        result = await manager.resilience_manager.execute_with_resilience("test-op", fail_then_succeed)
        assert result == "success"
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_full_security_report(self, manager):
        report = manager.security_report()
        assert "secrets_configured" in report
        assert "encryption_initialized" in report
        assert "audit_entries" in report
        assert "circuit_breakers" in report

    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, manager):
        await manager.shutdown()
        assert not manager.initialized
        assert not manager.encryption_service.initialized
