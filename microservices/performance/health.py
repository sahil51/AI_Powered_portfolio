import logging

from observability.health_aggregator import HealthComponent, HealthStatus
from performance.profiler import ConnectionPoolProfiler, PerformanceProfiler

logger = logging.getLogger("ai_assistant")


class PerformanceHealth:
    def __init__(
        self,
        profiler: PerformanceProfiler,
        pool_profiler: ConnectionPoolProfiler,
    ) -> None:
        self._profiler = profiler
        self._pool_profiler = pool_profiler

    def get_health(self) -> HealthComponent:
        details = {}
        status = HealthStatus.HEALTHY
        error_msg = ""

        try:
            cpu = self._profiler.get_cpu_usage()
            mem = self._profiler.get_memory_usage()
            db_pool = self._pool_profiler.get_db_pool_status()
            redis_pool = self._pool_profiler.get_redis_pool_status()

            details["cpu_pct"] = cpu
            details["memory"] = mem
            details["db_pool"] = db_pool
            details["redis_pool"] = redis_pool

            # Check for resource degradation
            if cpu > 90.0 or mem.get("percent", 0.0) > 90.0:
                status = HealthStatus.DEGRADED
                error_msg = "High resource consumption detected"

            # Check connection pool exhaustion
            if db_pool["total"] > 0 and (db_pool["active"] / db_pool["total"]) > 0.95:
                status = HealthStatus.DEGRADED
                error_msg = "Database connection pool saturated"

            if redis_pool["total"] > 0 and (redis_pool["active"] / redis_pool["total"]) > 0.95:
                status = HealthStatus.DEGRADED
                error_msg = "Redis connection pool saturated"

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error_msg = f"Performance profiling check failed: {e}"

        return HealthComponent(
            name="performance",
            status=status,
            details=details,
            error=error_msg,
        )
