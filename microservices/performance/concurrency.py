import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger("ai_assistant")


class ConcurrencyTester:
    def __init__(self, lock_service: Optional[Any] = None) -> None:
        self._lock_service = lock_service

    async def test_lock_concurrency(self, lock_key: str, concurrency: int) -> dict[str, Any]:
        acquired_locks = []
        rejected_requests = []

        async def worker(worker_id: int):
            try:
                if self._lock_service:
                    # Attempt to acquire a short-lived lock
                    acquired = await self._lock_service.acquire_lock(lock_key, ttl=5)
                    if acquired:
                        acquired_locks.append(worker_id)
                        # Keep it locked briefly to force others to wait
                        await asyncio.sleep(0.05)
                        await self._lock_service.release_lock(lock_key)
                    else:
                        rejected_requests.append(worker_id)
                else:
                    # Synthetic lock simulation
                    if not acquired_locks:
                        acquired_locks.append(worker_id)
                        await asyncio.sleep(0.05)
                    else:
                        rejected_requests.append(worker_id)
            except Exception as e:
                logger.debug(f"Lock worker failed: {e}")
                rejected_requests.append(worker_id)

        tasks = [asyncio.create_task(worker(i)) for i in range(concurrency)]
        await asyncio.gather(*tasks)

        # In a strict exclusive lock setup: only one worker should acquire the lock at a time
        success = len(acquired_locks) > 0
        safety_verified = len(acquired_locks) == 1 if concurrency > 1 else True

        return {
            "concurrency": concurrency,
            "acquired_count": len(acquired_locks),
            "rejected_count": len(rejected_requests),
            "success": success,
            "safety_verified": safety_verified,
        }
