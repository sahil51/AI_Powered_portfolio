from exceptions.base import AppError


class SecurityError(AppError):
    status_code = 403
    message = "Security error"


class SecurityConfigurationError(SecurityError):
    status_code = 500
    message = "Security configuration error"


class SecurityValidationError(SecurityError):
    status_code = 422
    message = "Security validation error"


class EncryptionError(SecurityError):
    status_code = 500
    message = "Encryption error"


class WebhookVerificationError(SecurityError):
    status_code = 401
    message = "Webhook verification failed"


class RateLimitExceededError(SecurityError):
    status_code = 429
    message = "Rate limit exceeded"


class ReplayAttackError(SecurityError):
    status_code = 401
    message = "Replay attack detected"
