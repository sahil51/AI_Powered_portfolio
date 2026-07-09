from __future__ import annotations

from typing import Any

from config.settings import settings
from monitoring.logger import logger
from security.audit_logger import AuditLogger
from security.circuit_breaker_registry import CircuitBreakerRegistry
from security.encryption_service import EncryptionService
from security.permission_validator import PermissionValidator
from security.rate_limit_manager import RateLimitManager
from security.request_validator import RequestValidator
from security.resilience_manager import ResilienceManager
from security.retry_policy_registry import RetryPolicyRegistry
from security.secrets_manager import SecretsManager
from security.webhook_verifier import WebhookVerifier


class SecurityManager:
    def __init__(self) -> None:
        self._initialized = False
        self._secrets_manager = SecretsManager()
        self._encryption_service = EncryptionService()
        self._audit_logger = AuditLogger()
        self._webhook_verifier = WebhookVerifier(secret=settings.jwt_secret)
        self._request_validator = RequestValidator()
        self._permission_validator = PermissionValidator()
        self._rate_limit_manager = RateLimitManager()
        self._circuit_breaker_registry = CircuitBreakerRegistry()
        self._retry_policy_registry = RetryPolicyRegistry()
        self._resilience_manager = ResilienceManager(
            circuit_breaker_registry=self._circuit_breaker_registry,
            retry_policy_registry=self._retry_policy_registry,
        )

    @property
    def secrets_manager(self) -> SecretsManager:
        return self._secrets_manager

    @property
    def encryption_service(self) -> EncryptionService:
        return self._encryption_service

    @property
    def audit_logger(self) -> AuditLogger:
        return self._audit_logger

    @property
    def webhook_verifier(self) -> WebhookVerifier:
        return self._webhook_verifier

    @property
    def request_validator(self) -> RequestValidator:
        return self._request_validator

    @property
    def permission_validator(self) -> PermissionValidator:
        return self._permission_validator

    @property
    def rate_limit_manager(self) -> RateLimitManager:
        return self._rate_limit_manager

    @property
    def circuit_breaker_registry(self) -> CircuitBreakerRegistry:
        return self._circuit_breaker_registry

    @property
    def retry_policy_registry(self) -> RetryPolicyRegistry:
        return self._retry_policy_registry

    @property
    def resilience_manager(self) -> ResilienceManager:
        return self._resilience_manager

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Initializing security manager")
        await self._secrets_manager.initialize()
        await self._encryption_service.initialize()
        self._permission_validator.load_default_permissions()
        self._rate_limit_manager.load_default_rules()
        self._retry_policy_registry.register_defaults()
        self._initialized = True
        logger.info("Security manager initialized")

    async def shutdown(self) -> None:
        if not self._initialized:
            return
        logger.info("Shutting down security manager")
        await self._secrets_manager.shutdown()
        await self._encryption_service.shutdown()
        self._rate_limit_manager.reset()
        self._circuit_breaker_registry.reset_all()
        self._resilience_manager.reset()
        self._audit_logger.clear()
        self._permission_validator.clear()
        self._initialized = False
        logger.info("Security manager shut down")

    def security_report(self) -> dict[str, Any]:
        return {
            "secrets_configured": len(self._secrets_manager.list_secret_keys()),
            "secrets_valid": self._secrets_manager.validate_all(),
            "encryption_initialized": self._encryption_service.initialized,
            "audit_entries": len(self._audit_logger.get_entries()),
            "permissions_loaded": bool(self._permission_validator.get_role_permissions("admin")),
            "rate_limit_rules": len(self._rate_limit_manager.get_rules()),
            "circuit_breakers": self._circuit_breaker_registry.get_all_states(),
        }

    def resilience_report(self) -> dict[str, Any]:
        return self._resilience_manager.get_resilience_report()
