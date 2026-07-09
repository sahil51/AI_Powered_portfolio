from dataclasses import dataclass, field

from infrastructure.cache.connection import redis_manager


@dataclass
class IdentityHealthStatus:
    cache_connected: bool = False
    session_store_ok: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.cache_connected and not self.errors


async def check_identity_health() -> IdentityHealthStatus:
    status = IdentityHealthStatus()

    try:
        if redis_manager.is_connected:
            status.cache_connected = True
            status.session_store_ok = True
    except Exception as e:
        status.errors.append(f"Identity cache check failed: {e}")

    return status
