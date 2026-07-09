import pytest

from application.ai.exceptions import ProviderValidationError
from application.ai.models import CompletionRequest
from application.ai.validation import validate_completion_request, validate_model_name


class TestValidateCompletionRequest:
    def test_valid_request(self):
        req = CompletionRequest(system_prompt="You are a helper", messages=[{"role": "user", "content": "hi"}])
        validate_completion_request(req)

    def test_valid_request_no_system(self):
        req = CompletionRequest(messages=[{"role": "user", "content": "hi"}])
        validate_completion_request(req)

    def test_missing_system_and_messages(self):
        req = CompletionRequest()
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "at least one" in exc.value.detail

    def test_invalid_temperature_low(self):
        req = CompletionRequest(system_prompt="test", temperature=-1.0)
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "temperature" in exc.value.detail

    def test_invalid_temperature_high(self):
        req = CompletionRequest(system_prompt="test", temperature=3.0)
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "temperature" in exc.value.detail

    def test_invalid_max_tokens(self):
        req = CompletionRequest(system_prompt="test", max_tokens=0)
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "max_tokens" in exc.value.detail

    def test_invalid_timeout(self):
        req = CompletionRequest(system_prompt="test", timeout=0)
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "timeout" in exc.value.detail

    def test_message_missing_role(self):
        req = CompletionRequest(messages=[{"content": "hi"}])
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "role" in exc.value.detail

    def test_message_missing_content(self):
        req = CompletionRequest(messages=[{"role": "user"}])
        with pytest.raises(ProviderValidationError) as exc:
            validate_completion_request(req)
        assert "content" in exc.value.detail


class TestValidateModelName:
    def test_valid(self):
        assert validate_model_name("gemini/gemini-2.0-flash") == "gemini/gemini-2.0-flash"

    def test_strips_whitespace(self):
        assert validate_model_name("  model  ") == "model"

    def test_empty_raises(self):
        with pytest.raises(ProviderValidationError):
            validate_model_name("")

    def test_none_raises(self):
        with pytest.raises(ProviderValidationError):
            validate_model_name("")
