from performance.models import BenchmarkResult, SLOThresholds
from performance.profiler import ConnectionPoolProfiler, PerformanceProfiler
from performance.statistics import PerformanceStatistics
from performance.validator import PerformanceValidator


def test_performance_profiler_metrics():
    profiler = PerformanceProfiler()
    cpu = profiler.get_cpu_usage()
    assert isinstance(cpu, float)
    assert cpu >= 0.0

    mem = profiler.get_memory_usage()
    assert "rss_bytes" in mem
    assert "vms_bytes" in mem
    assert "percent" in mem
    assert mem["percent"] >= 0.0

    threads = profiler.get_thread_count()
    assert isinstance(threads, int)
    assert threads > 0

    tasks = profiler.get_async_tasks_count()
    assert isinstance(tasks, int)
    assert tasks >= 0


def test_connection_pool_profiler_fallbacks():
    pool_profiler = ConnectionPoolProfiler()
    db_status = pool_profiler.get_db_pool_status()
    assert db_status["active"] >= 0
    assert db_status["idle"] >= 0
    assert db_status["total"] >= 0

    redis_status = pool_profiler.get_redis_pool_status()
    assert redis_status["active"] >= 0
    assert redis_status["idle"] >= 0
    assert redis_status["total"] >= 0


def test_performance_validator():
    validator = PerformanceValidator()
    thresholds = SLOThresholds(
        max_p95_latency_ms=200.0,
        max_p99_latency_ms=500.0,
        max_cpu_pct=80.0,
        max_memory_pct=85.0,
    )

    # 1. Benchmark validation
    benchmarks = [
        BenchmarkResult(name="e2e_request", latency_ms=150.0, status="success"),
        BenchmarkResult(name="conversation", latency_ms=45.0, status="success"),
    ]
    errors = validator.validate_benchmark(benchmarks, thresholds)
    assert not errors

    # Exceeding threshold
    benchmarks_failed = [
        BenchmarkResult(name="e2e_request", latency_ms=250.0, status="success"),
    ]
    errors_failed = validator.validate_benchmark(benchmarks_failed, thresholds)
    assert len(errors_failed) == 1
    assert "exceeds the p95 SLO threshold" in errors_failed[0]

    # 2. Resource validation
    res_errors = validator.validate_resources(cpu_pct=90.0, memory_pct=70.0, thresholds=thresholds)
    assert len(res_errors) == 1
    assert "CPU utilization" in res_errors[0]

    # 3. Load test validation
    load_errors = validator.validate_load_test(
        success_rate=95.0,
        avg_latency_ms=250.0,
        throughput_rps=5.0,
        thresholds=thresholds,
    )
    assert len(load_errors) == 3


def test_performance_statistics():
    stats = PerformanceStatistics()
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    res = stats.calculate_percentiles(latencies)
    assert res["min"] == 10.0
    assert res["max"] == 100.0
    assert res["mean"] == 55.0
    assert res["median"] == 55.0
    assert res["p90"] == 91.0
    assert res["p95"] == 95.5
    assert res["p99"] == 99.1
    assert res["std_dev"] > 0.0
