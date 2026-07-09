import asyncio
import json
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio.sentinel import Sentinel

from config.settings import settings
from monitoring.logger import logger

redis_pool: Optional[aioredis.Redis] = None
sentinel_client: Optional[Sentinel] = None


async def get_redis() -> aioredis.Redis:
    global redis_pool, sentinel_client
    if redis_pool is not None:
        return redis_pool

    if settings.redis_sentinel_enabled:
        sentinel_hosts = []
        for hostport in settings.redis_sentinel_hosts:
            parts = hostport.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 26379
            sentinel_hosts.append((host, port))

        sentinel_client = Sentinel(
            sentinel_hosts,
            sentinel_kwargs={"password": settings.redis_sentinel_password} if settings.redis_sentinel_password else {},
            socket_timeout=5,
        )
        redis_pool = sentinel_client.master_for(
            settings.redis_sentinel_master,
            db=0,
            password=settings.redis_sentinel_password or None,
            decode_responses=True,
        )
        logger.info(f"Redis Sentinel connected: master={settings.redis_sentinel_master}, hosts={settings.redis_sentinel_hosts}")
    else:
        redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return redis_pool


async def get_redis_sentinel_slave() -> Optional[aioredis.Redis]:
    if settings.redis_sentinel_enabled and sentinel_client is not None:
        return sentinel_client.slave_for(
            settings.redis_sentinel_master,
            db=0,
            password=settings.redis_sentinel_password or None,
            decode_responses=True,
        )
    return None


class CacheService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        serialized = json.dumps(value, default=str)
        await self.redis.setex(key, ttl, serialized)

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key) > 0

    async def acquire_lock(self, lock_key: str, ttl: int = 30) -> bool:
        result = await self.redis.set(lock_key, "locked", nx=True, ex=ttl)
        return result is not None

    async def release_lock(self, lock_key: str) -> None:
        await self.redis.delete(lock_key)

    async def acquire_lock_with_retry(
        self, lock_key: str, ttl: int = 30, max_retries: int = 3, retry_delay: float = 0.1
    ) -> bool:
        for attempt in range(max_retries):
            acquired = await self.acquire_lock(lock_key, ttl)
            if acquired:
                return True
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))
        return False

    async def check_idempotency(self, idempotency_key: str, ttl: int = 300) -> Optional[Any]:
        key = f"idempotency:{idempotency_key}"
        existing = await self.get(key)
        if existing:
            return existing
        return None

    async def set_idempotency(self, idempotency_key: str, response: Any, ttl: int = 300) -> None:
        key = f"idempotency:{idempotency_key}"
        await self.set(key, response, ttl)

    async def conversation_lock_key(self, conversation_id: str) -> str:
        return f"lock:conversation:{conversation_id}"

    async def acquire_conversation_lock(self, conversation_id: str, ttl: int = 30) -> bool:
        return await self.acquire_lock_with_retry(
            f"lock:conversation:{conversation_id}", ttl=ttl, max_retries=3, retry_delay=0.1
        )

    async def release_conversation_lock(self, conversation_id: str) -> None:
        await self.release_lock(f"lock:conversation:{conversation_id}")
