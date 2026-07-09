import pytest

from security.permission_validator import PermissionValidator


class TestPermissionValidator:
    @pytest.fixture
    def validator(self):
        v = PermissionValidator()
        v.load_default_permissions()
        return v

    def test_admin_has_permission(self, validator):
        assert validator.has_permission("admin", "admin:system")
        assert validator.has_permission("admin", "conversation:write")

    def test_user_has_permission(self, validator):
        assert validator.has_permission("user", "conversation:read")
        assert validator.has_permission("user", "knowledge:read")
        assert not validator.has_permission("user", "admin:system")

    def test_viewer_permissions(self, validator):
        assert validator.has_permission("viewer", "conversation:read")
        assert not validator.has_permission("viewer", "conversation:write")

    def test_grant_permission(self, validator):
        validator.grant_permission("user", "admin:system")
        assert validator.has_permission("user", "admin:system")

    def test_revoke_permission(self, validator):
        validator.revoke_permission("admin", "admin:system")
        assert not validator.has_permission("admin", "admin:system")

    def test_has_any_permission(self, validator):
        assert validator.has_any_permission("user", ["nonexistent", "conversation:read"])
        assert not validator.has_any_permission("viewer", ["admin:system", "workflow:write"])

    def test_has_all_permissions(self, validator):
        assert validator.has_all_permissions("admin", ["conversation:read", "conversation:write"])
        assert not validator.has_all_permissions("user", ["conversation:read", "admin:system"])

    def test_get_role_permissions(self, validator):
        perms = validator.get_role_permissions("admin")
        assert "admin:system" in perms

    def test_empty_role(self, validator):
        assert not validator.has_permission("nonexistent", "anything")

    def test_validate_permission_allowed(self, validator):
        result = validator.validate_permission("user", "conversation:read")
        assert result["allowed"]

    def test_validate_permission_denied(self, validator):
        result = validator.validate_permission("viewer", "workflow:write")
        assert not result["allowed"]

    def test_clear(self, validator):
        validator.clear()
        assert not validator.has_permission("admin", "admin:system")
