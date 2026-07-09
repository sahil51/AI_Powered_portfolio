import pytest

from performance.benchmark import PerformanceBenchmark
from performance.concurrency import ConcurrencyTester
from performance.load_runner import LoadTestRunner
from performance.manager import PerformanceManager
from performance.models import LoadTestConfig, SLOThresholds
from performance.profiler import ConnectionPoolProfiler, PerformanceProfiler
from performance.stress_runner import StressTestRunner
from performance.validator import PerformanceValidator


@pytest.mark.asyncio
async def test_performance_benchmark():
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_all()
    assert len(results) > 0
    for res in results:
        assert res.status == "success"
        assert res.latency_ms > 0.0


@pytest.mark.asyncio
async def test_load_test_runner():
    runner = LoadTestRunner()
    config = LoadTestConfig(concurrent_users=2, duration_seconds=1)
    report = await runner.run_load_test(config)
    assert report["total_requests"] >= 0
    assert report["success_rate"] >= 0.0
    assert report["avg_latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_stress_test_runner():
    runner = StressTestRunner()
    db_stress = await runner.run_postgres_saturation(concurrency=3)
    assert db_stress.scenario_name == "database_saturation"
    assert db_stress.success_rate >= 0.0

    redis_stress = await runner.run_redis_saturation(concurrency=3)
    assert redis_stress.scenario_name == "redis_saturation"
    assert redis_stress.success_rate >= 0.0

    provider_stress = await runner.run_provider_failure()
    assert provider_stress.scenario_name == "provider_failure"
    assert provider_stress.success_rate == 0.0


@pytest.mark.asyncio
async def test_concurrency_tester():
    tester = ConcurrencyTester()
    res = await tester.test_lock_concurrency(lock_key="test_lock", concurrency=3)
    assert res["concurrency"] == 3
    assert res["acquired_count"] > 0
    assert res["success"] is True


@pytest.mark.asyncio
async def test_performance_manager():
    profiler = PerformanceProfiler()
    pool_profiler = ConnectionPoolProfiler()
    benchmark = PerformanceBenchmark()
    validator = PerformanceValidator()

    manager = PerformanceManager(
        profiler=profiler,
        pool_profiler=pool_profiler,
        benchmark=benchmark,
        validator=validator,
    )

    thresholds = SLOThresholds(max_p95_latency_ms=300.0)
    report = await manager.generate_system_report(slo_thresholds=thresholds)

    assert report.validator_passed is True
    assert len(report.benchmarks) > 0
    assert "cpu_usage_pct" in report.metrics_summary
    assert len(report.recommendations) > 0
