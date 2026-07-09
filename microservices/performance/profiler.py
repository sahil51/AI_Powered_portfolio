import asyncio
import logging
import os
import threading
from typing import Any

logger = logging.getLogger("ai_assistant")

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]


class PerformanceProfiler:
    def __init__(self) -> None:
        if psutil is None:
            logger.warning("psutil is not installed. Using fallback CPU/Memory profiling.")

    def get_cpu_usage(self) -> float:
        if psutil:
            try:
                return psutil.cpu_percent(interval=None)
            except Exception as e:
                logger.debug(f"Failed to read psutil cpu_percent: {e}")
        # Fallback
        return 0.0

    def get_memory_usage(self) -> dict[str, float]:
        if psutil:
            try:
                process = psutil.Process(os.getpid())
                mem = process.memory_info()
                return {
                    "rss_bytes": float(mem.rss),
                    "vms_bytes": float(mem.vms),
                    "percent": float(process.memory_percent()),
                }
            except Exception as e:
                logger.debug(f"Failed to read psutil memory_info: {e}")
        # Fallback
        return {
            "rss_bytes": 0.0,
            "vms_bytes": 0.0,
            "percent": 0.0,
        }

    def get_thread_count(self) -> int:
        if psutil:
            try:
                process = psutil.Process(os.getpid())
                return process.num_threads()
            except Exception as e:
                logger.debug(f"Failed to read psutil thread count: {e}")
        return threading.active_count()

    def get_async_tasks_count(self) -> int:
        try:
            return len(asyncio.all_tasks())
        except Exception:
            return 0


class ConnectionPoolProfiler:
    def __init__(self, db_engine: Any = None, redis_client: Any = None) -> None:
        self._db_engine = db_engine
        self._redis_client = redis_client

    def get_db_pool_status(self) -> dict[str, int]:
        active = 0
        idle = 0
        total = 0
        try:
            engine = self._db_engine
            if engine is None:
                from infrastructure.database.session import db
                if db.is_connected:
                    engine = db.engine

            if engine is not None and hasattr(engine, "sync_engine"):
                pool = engine.sync_engine.pool
                active = pool.checkedout()
                idle = pool.checkedin()
                total = pool.size()
        except Exception as e:
            logger.debug(f"Database connection pool profiling failed: {e}")

        return {
            "active": active,
            "idle": idle,
            "total": total,
        }

    def get_redis_pool_status(self) -> dict[str, int]:
        active = 0
        idle = 0
        total = 20
        try:
            client = self._redis_client
            if client is None:
                from infrastructure.cache.redis_client import redis_pool
                client = redis_pool

            if client is not None and hasattr(client, "connection_pool"):
                pool = client.connection_pool
                # aioredis connection pool tracks connections in use
                if hasattr(pool, "_in_use"):
                    active = len(pool._in_use)
                if hasattr(pool, "_available_connections"):
                    idle = len(pool._available_connections)
                if hasattr(pool, "max_connections"):
                    total = pool.max_connections
        except Exception as e:
            logger.debug(f"Redis connection pool profiling failed: {e}")

        return {
            "active": active,
            "idle": idle,
            "total": total,
        }
