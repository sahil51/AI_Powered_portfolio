
from application.ai.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderNotSupportedError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)


class TestProviderExceptions:
    def test_provider_error_defaults(self):
        err = ProviderError()
        assert err.status_code == 503
        assert "AI provider error" in err.message
        assert err.provider is None

    def test_provider_error_with_provider(self):
        err = ProviderError(provider="gemini")
        assert err.provider == "gemini"

    def test_configuration_error(self):
        err = ProviderConfigurationError()
        assert err.status_code == 500

    def test_timeout_error(self):
        err = ProviderTimeoutError()
        assert err.status_code == 504

    def test_rate_limit_error(self):
        err = ProviderRateLimitError()
        assert err.status_code == 429

    def test_authentication_error(self):
        err = ProviderAuthenticationError()
        assert err.status_code == 401

    def test_unavailable_error(self):
        err = ProviderUnavailableError()
        assert err.status_code == 503

    def test_not_supported_error(self):
        err = ProviderNotSupportedError()
        assert err.status_code == 400

    def test_validation_error(self):
        err = ProviderValidationError()
        assert err.status_code == 422

    def test_custom_message(self):
        err = ProviderError(message="Custom error", detail="Something went wrong")
        assert err.message == "Custom error"
        assert err.detail == "Something went wrong"


class TestProviderCapability:
    def test_enum_values(self):
        from application.ai.capability import ProviderCapability

        assert ProviderCapability.COMPLETION.value == "completion"
        assert ProviderCapability.STREAMING.value == "streaming"
        assert ProviderCapability.JSON_MODE.value == "json_mode"
        assert ProviderCapability.HEALTH_CHECK.value == "health_check"
