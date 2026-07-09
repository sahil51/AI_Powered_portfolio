from performance.models import BenchmarkResult, SLOThresholds


class PerformanceValidator:
    def validate_benchmark(self, results: list[BenchmarkResult], thresholds: SLOThresholds) -> list[str]:
        errors = []
        for res in results:
            if res.status != "success":
                errors.append(f"Benchmark '{res.name}' failed with error: {res.error}")
                continue

            # Compare against latency thresholds
            # Check p95/p99 (for E2E request, or general component benchmark limit)
            # Typically component benchmarks should be well under the p95 limit.
            if res.name == "e2e_request" and res.latency_ms > thresholds.max_p95_latency_ms:
                errors.append(
                    f"E2E request latency ({res.latency_ms:.2f}ms) "
                    f"exceeds the p95 SLO threshold ({thresholds.max_p95_latency_ms}ms)"
                )
            elif res.name != "e2e_request" and res.latency_ms > (thresholds.max_p95_latency_ms / 2):
                errors.append(
                    f"Component '{res.name}' latency ({res.latency_ms:.2f}ms) "
                    f"exceeds component SLO limit ({thresholds.max_p95_latency_ms / 2}ms)"
                )
        return errors

    def validate_resources(self, cpu_pct: float, memory_pct: float, thresholds: SLOThresholds) -> list[str]:
        errors = []
        if cpu_pct > thresholds.max_cpu_pct:
            errors.append(f"CPU utilization ({cpu_pct:.1f}%) exceeds the SLO limit ({thresholds.max_cpu_pct}%)")
        if memory_pct > thresholds.max_memory_pct:
            errors.append(f"Memory footprint ({memory_pct:.1f}%) exceeds the SLO limit ({thresholds.max_memory_pct}%)")
        return errors

    def validate_load_test(
        self,
        success_rate: float,
        avg_latency_ms: float,
        throughput_rps: float,
        thresholds: SLOThresholds,
    ) -> list[str]:
        errors = []
        expected_success = 100.0 - thresholds.max_error_rate_pct
        if success_rate < expected_success:
            errors.append(
                f"Load test success rate ({success_rate:.2f}%) is below SLO minimum ({expected_success:.2f}%)"
            )
        if avg_latency_ms > thresholds.max_p95_latency_ms:
            errors.append(
                f"Load test average latency ({avg_latency_ms:.2f}ms) "
                f"exceeds the SLO threshold ({thresholds.max_p95_latency_ms}ms)"
            )
        if throughput_rps < thresholds.min_throughput_rps:
            errors.append(
                f"Load test throughput ({throughput_rps:.2f} rps) "
                f"falls short of SLO requirement ({thresholds.min_throughput_rps} rps)"
            )
        return errors
