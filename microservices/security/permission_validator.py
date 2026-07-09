from __future__ import annotations

from typing import Any


class PermissionValidator:
    def __init__(self) -> None:
        self._permissions: dict[str, set[str]] = {}

    def grant_permission(self, role: str, permission: str) -> None:
        if role not in self._permissions:
            self._permissions[role] = set()
        self._permissions[role].add(permission)

    def revoke_permission(self, role: str, permission: str) -> None:
        if role in self._permissions:
            self._permissions[role].discard(permission)

    def has_permission(self, role: str, permission: str) -> bool:
        return permission in self._permissions.get(role, set())

    def has_any_permission(self, role: str, permissions: list[str]) -> bool:
        role_perms = self._permissions.get(role, set())
        return any(p in role_perms for p in permissions)

    def has_all_permissions(self, role: str, permissions: list[str]) -> bool:
        role_perms = self._permissions.get(role, set())
        return all(p in role_perms for p in permissions)

    def get_role_permissions(self, role: str) -> set[str]:
        return set(self._permissions.get(role, set()))

    def load_default_permissions(self) -> None:
        admin_perms = {
            "conversation:read", "conversation:write", "conversation:delete",
            "memory:read", "memory:write", "memory:delete",
            "knowledge:read", "knowledge:write", "knowledge:delete",
            "meeting:read", "meeting:write", "meeting:delete",
            "workflow:read", "workflow:write", "workflow:execute",
            "admin:system", "admin:users", "admin:config",
            "audit:read", "metrics:read", "health:read",
        }
        user_perms = {
            "conversation:read", "conversation:write",
            "memory:read", "memory:write",
            "knowledge:read",
            "meeting:read", "meeting:write",
            "workflow:read", "workflow:execute",
        }
        viewer_perms = {
            "conversation:read",
            "memory:read",
            "knowledge:read",
            "meeting:read",
        }
        self._permissions["admin"] = admin_perms
        self._permissions["user"] = user_perms
        self._permissions["viewer"] = viewer_perms

    def validate_permission(
        self,
        role: str,
        permission: str,
    ) -> dict[str, Any]:
        allowed = self.has_permission(role, permission)
        return {
            "allowed": allowed,
            "role": role,
            "permission": permission,
            "reason": "" if allowed else f"Role {role} lacks permission {permission}",
        }

    def clear(self) -> None:
        self._permissions.clear()
