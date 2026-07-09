from exceptions.base import AppError


class ProviderError(AppError):
    status_code: int = 503
    message: str = "AI provider error"

    def __init__(self, message: str | None = None, detail: str | None = None, provider: str | None = None) -> None:
        self.provider = provider
        super().__init__(message=message or self.message, detail=detail)


class ProviderConfigurationError(ProviderError):
    status_code: int = 500
    message: str = "AI provider configuration error"


class ProviderTimeoutError(ProviderError):
    status_code: int = 504
    message: str = "AI provider timeout"


class ProviderRateLimitError(ProviderError):
    status_code: int = 429
    message: str = "AI provider rate limit exceeded"


class ProviderAuthenticationError(ProviderError):
    status_code: int = 401
    message: str = "AI provider authentication failed"


class ProviderUnavailableError(ProviderError):
    status_code: int = 503
    message: str = "AI provider unavailable"


class ProviderNotSupportedError(ProviderError):
    status_code: int = 400
    message: str = "AI provider capability not supported"


class ProviderValidationError(ProviderError):
    status_code: int = 422
    message: str = "AI provider validation error"
