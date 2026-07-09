from dataclasses import dataclass, field

from infrastructure.cache.connection import redis_manager
from monitoring.logger import logger


@dataclass
class RedisHealthStatus:
    connected: bool = False
    ping_ms: float = 0.0
    pool_available: int = 0
    memory_used_mb: float = 0.0
    connected_clients: int = 0
    mode: str = "standalone"
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.connected and not self.errors


async def check_redis_health() -> RedisHealthStatus:
    status = RedisHealthStatus()

    try:
        start = __import__("time").monotonic()
        await redis_manager.client.ping()
        status.ping_ms = (__import__("time").monotonic() - start) * 1000
        status.connected = True
    except Exception as e:
        status.errors.append(f"Ping failed: {e}")
        logger.warning(f"Redis health check ping failed: {e}")

    try:
        info = await redis_manager.client.info()
        status.memory_used_mb = int(info.get("used_memory", 0)) / (1024 * 1024)
        status.connected_clients = int(info.get("connected_clients", 0))
    except Exception as e:
        status.errors.append(f"Info failed: {e}")

    if redis_manager.config.sentinel_enabled:
        status.mode = "sentinel"

    return status
