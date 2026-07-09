import logging
from datetime import datetime, timezone
from typing import Optional

from performance.benchmark import PerformanceBenchmark
from performance.models import PerformanceReport, SLOThresholds
from performance.profiler import ConnectionPoolProfiler, PerformanceProfiler
from performance.validator import PerformanceValidator

logger = logging.getLogger("ai_assistant")


class PerformanceManager:
    def __init__(
        self,
        profiler: PerformanceProfiler,
        pool_profiler: ConnectionPoolProfiler,
        benchmark: PerformanceBenchmark,
        validator: PerformanceValidator,
    ) -> None:
        self.profiler = profiler
        self.pool_profiler = pool_profiler
        self.benchmark = benchmark
        self.validator = validator

    async def generate_system_report(
        self,
        slo_thresholds: Optional[SLOThresholds] = None,
    ) -> PerformanceReport:
        thresholds = slo_thresholds or SLOThresholds()
        errors = []
        recommendations = []

        # 1. Run Benchmarks
        bench_results = await self.benchmark.run_all()
        bench_errors = self.validator.validate_benchmark(bench_results, thresholds)
        errors.extend(bench_errors)

        # 2. Profile Resources
        cpu = self.profiler.get_cpu_usage()
        mem = self.profiler.get_memory_usage()
        res_errors = self.validator.validate_resources(cpu, mem.get("percent", 0.0), thresholds)
        errors.extend(res_errors)

        # 3. Compile pool status
        db_pool = self.pool_profiler.get_db_pool_status()
        redis_pool = self.pool_profiler.get_redis_pool_status()

        # 4. Generate recommendations based on profiling details
        if cpu > 70.0:
            recommendations.append("High CPU utilization. Scaling Celery concurrency or replicas is recommended.")
        if mem.get("percent", 0.0) > 75.0:
            recommendations.append(
                "High memory utilization. Restructure GC cycles or allocate additional container memory."
            )
        if db_pool["total"] > 0 and (db_pool["active"] / db_pool["total"]) > 0.8:
            recommendations.append(
                f"DB Pool utilization is high ({db_pool['active']}/{db_pool['total']}). "
                "Increase database pool_size and max_overflow configuration."
            )
        if redis_pool["total"] > 0 and (redis_pool["active"] / redis_pool["total"]) > 0.8:
            recommendations.append(
                f"Redis pool utilization is high ({redis_pool['active']}/{redis_pool['total']}). "
                "Tune max_connections in CacheService configuration."
            )

        if not recommendations:
            recommendations.append(
                "System is performing within optimal parameters. No performance optimizations required at this time."
            )

        passed = len(errors) == 0

        summary = {
            "cpu_usage_pct": cpu,
            "memory_usage_pct": mem.get("percent", 0.0),
            "memory_rss_mb": mem.get("rss_bytes", 0.0) / (1024 * 1024),
            "db_pool_active": db_pool["active"],
            "db_pool_total": db_pool["total"],
            "redis_pool_active": redis_pool["active"],
            "redis_pool_total": redis_pool["total"],
            "thread_count": self.profiler.get_thread_count(),
            "async_tasks_count": self.profiler.get_async_tasks_count(),
        }

        return PerformanceReport(
            timestamp=datetime.now(timezone.utc),
            benchmarks=bench_results,
            validator_passed=passed,
            errors=errors,
            recommendations=recommendations,
            metrics_summary=summary,
        )
