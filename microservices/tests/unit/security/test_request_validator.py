import pytest

from security.request_validator import RequestValidator


class TestRequestValidator:
    @pytest.fixture
    def validator(self):
        return RequestValidator()

    def test_validate_headers_valid(self, validator):
        result = validator.validate_headers({"content-type": "application/json"})
        assert result.valid

    def test_validate_headers_invalid(self, validator):
        result = validator.validate_headers({"content-type": "text/html"})
        assert not result.valid

    def test_validate_payload_size_within_limit(self, validator):
        result = validator.validate_payload_size(b"small payload")
        assert result.valid

    def test_validate_payload_size_exceeded(self, validator):
        large = b"x" * (1024 * 1024 + 1)
        result = validator.validate_payload_size(large)
        assert not result.valid

    def test_validate_payload_json_valid(self, validator):
        result = validator.validate_payload_json('{"key": "value"}')
        assert result.valid

    def test_validate_payload_json_invalid(self, validator):
        result = validator.validate_payload_json("{invalid}")
        assert not result.valid

    def test_validate_tenant_allowed(self, validator):
        result = validator.validate_tenant("tenant-1", ["tenant-1", "tenant-2"])
        assert result.valid

    def test_validate_tenant_denied(self, validator):
        result = validator.validate_tenant("tenant-3", ["tenant-1", "tenant-2"])
        assert not result.valid

    def test_validate_correlation_id_valid(self, validator):
        result = validator.validate_correlation_id("corr-123")
        assert result.valid

    def test_validate_correlation_id_missing(self, validator):
        result = validator.validate_correlation_id("")
        assert not result.valid

    def test_validate_correlation_id_too_long(self, validator):
        result = validator.validate_correlation_id("x" * 65)
        assert not result.valid
