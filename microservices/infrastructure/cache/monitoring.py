import time
from dataclasses import dataclass, field

import redis.asyncio as aioredis


@dataclass
class RedisMetrics:
    pool_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    hit_ratio: float = 0.0
    miss_ratio: float = 0.0
    lock_acquired: int = 0
    lock_failed: int = 0
    lock_contention: int = 0
    total_commands: int = 0
    commands_per_second: float = 0.0
    memory_used: int = 0
    memory_fragmentation: float = 0.0
    latency_ms: float = 0.0
    connected_clients: int = 0
    errors: list[str] = field(default_factory=list)


class RedisMonitor:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis
        self._command_count = 0
        self._start_time = time.monotonic()
        self._last_latency: float = 0.0

    async def collect_metrics(self) -> RedisMetrics:
        metrics = RedisMetrics()

        try:
            info = await self._redis.info()
            metrics.connected_clients = int(info.get("connected_clients", 0))
            metrics.memory_used = int(info.get("used_memory", 0))
            metrics.memory_fragmentation = float(info.get("mem_fragmentation_ratio", 0.0))
            metrics.total_commands = int(info.get("total_commands_processed", 0))

            uptime = time.monotonic() - self._start_time
            metrics.commands_per_second = self._command_count / uptime if uptime > 0 else 0.0
        except Exception as e:
            metrics.errors.append(f"Info collection failed: {e}")

        try:
            pool = self._redis.connection_pool
            if pool:
                metrics.pool_size = pool.max_connections
        except Exception:
            pass

        try:
            start = time.monotonic()
            await self._redis.ping()
            metrics.latency_ms = (time.monotonic() - start) * 1000
        except Exception as e:
            metrics.errors.append(f"Latency check failed: {e}")
            metrics.latency_ms = -1.0

        return metrics

    async def check_latency(self) -> float:
        start = time.monotonic()
        try:
            await self._redis.ping()
            self._last_latency = (time.monotonic() - start) * 1000
        except Exception:
            self._last_latency = -1.0
        return self._last_latency

    def increment_commands(self, count: int = 1) -> None:
        self._command_count += count

    @property
    def uptime(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def last_latency(self) -> float:
        return self._last_latency
