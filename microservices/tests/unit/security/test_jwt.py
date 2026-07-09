import jwt
import pytest

from config.settings import settings
from security.request_validator import RequestValidator


class TestJWTValidation:
    @pytest.fixture
    def validator(self):
        return RequestValidator()

    def test_valid_jwt(self, validator, monkeypatch):
        monkeypatch.setattr(settings, "jwt_secret", "test-secret")
        monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
        token = jwt.encode({"sub": "user-1", "tenant_id": "tenant-1"}, "test-secret", algorithm="HS256")
        result = validator.validate_jwt(token)
        assert result.valid
        assert result.user_id == "user-1"
        assert result.tenant_id == "tenant-1"

    def test_expired_jwt(self, validator, monkeypatch):
        import time
        monkeypatch.setattr(settings, "jwt_secret", "test-secret")
        monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
        token = jwt.encode(
            {"sub": "user-1", "exp": int(time.time()) - 3600},
            "test-secret",
            algorithm="HS256",
        )
        result = validator.validate_jwt(token)
        assert not result.valid
        assert "expired" in result.error

    def test_invalid_jwt(self, validator):
        result = validator.validate_jwt("invalid-token")
        assert not result.valid

    def test_malformed_jwt(self, validator):
        result = validator.validate_jwt("not.a.token")
        assert not result.valid
