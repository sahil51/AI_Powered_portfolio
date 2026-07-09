import asyncio
import logging
import time
from typing import Any, Callable, Optional

from performance.models import LoadTestConfig

logger = logging.getLogger("ai_assistant")


class LoadTestRunner:
    def __init__(self, target_callable: Optional[Callable] = None) -> None:
        self.target_callable = target_callable

    async def run_load_test(self, config: LoadTestConfig) -> dict[str, Any]:
        start_time = time.time()
        latencies = []
        success_count = 0
        failure_count = 0

        # Async workload generator helper
        async def worker():
            nonlocal success_count, failure_count
            t0 = time.time()
            try:
                if self.target_callable:
                    await self.target_callable()
                else:
                    # Synthetic endpoint call simulation
                    await asyncio.sleep(0.05)
                success_count += 1
            except Exception as e:
                failure_count += 1
                logger.debug(f"Load test worker request failed: {e}")
            latencies.append((time.time() - t0) * 1000)

        # Simulating concurrent users over the duration
        end_time = start_time + config.duration_seconds
        while time.time() < end_time:
            tasks = [asyncio.create_task(worker()) for _ in range(config.concurrent_users)]
            await asyncio.gather(*tasks)
            # Sleep slightly to control requests per second spike
            await asyncio.sleep(0.1)

        total_duration = time.time() - start_time
        total_requests = success_count + failure_count
        throughput = total_requests / total_duration if total_duration > 0 else 0.0
        success_rate = (success_count / total_requests * 100.0) if total_requests > 0 else 0.0

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        sorted_lats = sorted(latencies)
        p95_latency = sorted_lats[int(len(sorted_lats) * 0.95)] if sorted_lats else 0.0
        p99_latency = sorted_lats[int(len(sorted_lats) * 0.99)] if sorted_lats else 0.0

        return {
            "duration_seconds": total_duration,
            "total_requests": total_requests,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_rate,
            "throughput_rps": throughput,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
        }
