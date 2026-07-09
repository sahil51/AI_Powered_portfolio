import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import redis.asyncio as aioredis

from infrastructure.cache.degraded_mode import is_redis_degraded, is_redis_unavailable
from infrastructure.cache.key_builder import default_key_builder
from monitoring.logger import logger


@dataclass
class LockStats:
    acquired: int = 0
    released: int = 0
    failed: int = 0
    extended: int = 0
    contention: int = 0
    wait_time: float = 0.0
    hold_time: float = 0.0


class DistributedLock:
    def __init__(
        self,
        redis: aioredis.Redis,
        resource: str,
        ttl: int = 30,
        retry_delay: float = 0.1,
        max_retries: int = 3,
    ) -> None:
        self._redis = redis
        self._resource = resource
        self._lock_key = default_key_builder.lock(resource)
        self._ttl = ttl
        self._retry_delay = retry_delay
        self._max_retries = max_retries
        self._owner_id = str(uuid.uuid4())
        self._acquired = False
        self._acquired_at: float | None = None
        self._renewal_task: asyncio.Task[None] | None = None

    async def acquire(self, blocking: bool = True) -> bool:
        if is_redis_unavailable():
            return False

        if self._acquired:
            return True

        if blocking:
            return await self._acquire_with_retry()
        return await self._try_acquire()

    async def _try_acquire(self) -> bool:
        try:
            acquired = await self._redis.set(
                self._lock_key,
                self._owner_id,
                nx=True,
                ex=self._ttl,
            )
            if acquired:
                self._acquired = True
                self._acquired_at = time.monotonic()
                self._start_renewal()
            return bool(acquired)
        except Exception as e:
            logger.warning(f"Lock acquire failed for {self._resource}: {e}")
            return False

    async def _acquire_with_retry(self) -> bool:
        for attempt in range(self._max_retries):
            if await self._try_acquire():
                return True
            LockStats.contention += 1  # type: ignore[attr-defined]
            if attempt < self._max_retries - 1:
                await asyncio.sleep(self._retry_delay * (2**attempt))
        return False

    async def release(self) -> None:
        if not self._acquired:
            return

        self._stop_renewal()

        try:
            lock_value = await self._redis.get(self._lock_key)
            if lock_value and lock_value.decode() if isinstance(lock_value, bytes) else lock_value == self._owner_id:
                await self._redis.delete(self._lock_key)
        except Exception as e:
            logger.warning(f"Lock release error for {self._resource}: {e}")
        finally:
            self._acquired = False
            self._acquired_at = None

    async def safe_release(self) -> None:
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            await self._redis.eval(lua_script, 1, self._lock_key, str(self._owner_id))  # type: ignore[misc]
        except Exception as e:
            logger.warning(f"Safe lock release error for {self._resource}: {e}")
        finally:
            self._acquired = False
            self._acquired_at = None

    async def extend(self, extra_ttl: int | None = None) -> bool:
        if not self._acquired:
            return False

        ttl = extra_ttl or self._ttl
        try:
            lock_value = await self._redis.get(self._lock_key)
            if lock_value and (lock_value.decode() if isinstance(lock_value, bytes) else lock_value) == self._owner_id:
                await self._redis.expire(self._lock_key, ttl)
                return True
            return False
        except Exception as e:
            logger.warning(f"Lock extend error for {self._resource}: {e}")
            return False

    async def _renew_loop(self) -> None:
        while self._acquired:
            await asyncio.sleep(self._ttl / 2)
            if self._acquired:
                await self.extend()

    def _start_renewal(self) -> None:
        if self._renewal_task is None or self._renewal_task.done():
            self._renewal_task = asyncio.create_task(self._renew_loop())

    def _stop_renewal(self) -> None:
        if self._renewal_task and not self._renewal_task.done():
            self._renewal_task.cancel()

    @property
    def acquired(self) -> bool:
        return self._acquired

    @property
    def resource(self) -> str:
        return self._resource

    @property
    def owner_id(self) -> str:
        return self._owner_id


@asynccontextmanager
async def lock(
    redis: aioredis.Redis,
    resource: str,
    ttl: int = 30,
    retry_delay: float = 0.1,
    max_retries: int = 3,
) -> AsyncIterator[DistributedLock]:
    lock_instance = DistributedLock(redis, resource, ttl, retry_delay, max_retries)
    try:
        await lock_instance.acquire(blocking=True)
        yield lock_instance
    finally:
        await lock_instance.safe_release()


_conversation_locks: dict[str, DistributedLock] = {}


async def acquire_conversation_lock(
    redis: aioredis.Redis, conversation_id: str, ttl: int = 30
) -> DistributedLock | None:
    if is_redis_degraded():
        return None
    lock_instance = DistributedLock(redis, f"conversation:{conversation_id}", ttl=ttl)
    acquired = await lock_instance.acquire(blocking=True)
    if acquired:
        _conversation_locks[conversation_id] = lock_instance
    return lock_instance if acquired else None


async def release_conversation_lock(conversation_id: str) -> None:
    lock_instance = _conversation_locks.pop(conversation_id, None)
    if lock_instance:
        await lock_instance.safe_release()
