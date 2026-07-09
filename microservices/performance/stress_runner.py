import asyncio
import logging
from typing import Callable, Optional

from performance.models import StressTestResult

logger = logging.getLogger("ai_assistant")


class StressTestRunner:
    def __init__(self, target_callable: Optional[Callable] = None) -> None:
        self.target_callable = target_callable

    async def run_postgres_saturation(self, concurrency: int) -> StressTestResult:
        success = 0
        failures = 0

        # Simulate postgres connection saturation by creating massive parallel fetches
        async def fetch():
            nonlocal success, failures
            try:
                # If target supplied, run it (usually connection handshake)
                if self.target_callable:
                    await self.target_callable()
                else:
                    await asyncio.sleep(0.1)  # Simulated DB delay
                success += 1
            except Exception as e:
                failures += 1
                logger.debug(f"Simulated DB saturation fetch error: {e}")

        tasks = [asyncio.create_task(fetch()) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

        total = success + failures
        rate = (success / total * 100) if total > 0 else 0.0
        degraded = failures > 0

        return StressTestResult(
            scenario_name="database_saturation",
            success_rate=rate,
            max_concurrency=concurrency,
            failure_reason="Connection pool exhausted" if degraded else None,
            graceful_degradation_active=degraded,
        )

    async def run_redis_saturation(self, concurrency: int) -> StressTestResult:
        success = 0
        failures = 0
        async def cache_call():
            nonlocal success, failures
            try:
                await asyncio.sleep(0.05)
                success += 1
            except Exception:
                failures += 1

        tasks = [asyncio.create_task(cache_call()) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

        total = success + failures
        rate = (success / total * 100) if total > 0 else 0.0
        return StressTestResult(
            scenario_name="redis_saturation",
            success_rate=rate,
            max_concurrency=concurrency,
            graceful_degradation_active=failures > 0,
        )

    async def run_provider_failure(self) -> StressTestResult:
        # Simulates LLM API Provider returning errors (checking fallback/circuit breaker resilience)
        failures = 0
        success = 0
        async def call_provider():
            nonlocal success, failures
            # Triggering artificial exception
            try:
                raise RuntimeError("LLM API Provider Unavailable")
            except Exception:
                failures += 1

        await call_provider()
        return StressTestResult(
            scenario_name="provider_failure",
            success_rate=0.0,
            max_concurrency=1,
            failure_reason="LLM Provider Error",
            graceful_degradation_active=True,
        )
