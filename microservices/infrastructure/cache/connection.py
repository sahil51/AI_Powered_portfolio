import asyncio
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio.sentinel import Sentinel

from infrastructure.cache.config import RedisConfig, redis_config
from infrastructure.cache.degraded_mode import RedisDegradationTier, set_redis_tier
from monitoring.logger import logger


class RedisConnectionManager:
    def __init__(self, config: RedisConfig | None = None) -> None:
        self._config = config or redis_config
        self._client: aioredis.Redis | None = None
        self._sentinel: Sentinel | None = None
        self._pool: aioredis.ConnectionPool | None = None
        self._connected = False
        self._connection_attempts = 0
        self._reconnecting = False

    async def initialize(self) -> aioredis.Redis:
        if self._client is not None:
            return self._client

        self._connection_attempts = 0
        return await self._connect()

    async def _connect(self) -> aioredis.Redis:
        self._connection_attempts += 1

        if self._config.sentinel_enabled:
            self._client = await self._connect_sentinel()
        else:
            self._client = await self._connect_standalone()

        await self._verify_connection(self._client)
        self._connected = True
        self._connection_attempts = 0
        set_redis_tier(RedisDegradationTier.NORMAL)
        logger.info(f"Redis connected: {'sentinel' if self._config.sentinel_enabled else 'standalone'}")
        return self._client

    async def _connect_standalone(self) -> aioredis.Redis:
        self._pool = aioredis.ConnectionPool.from_url(
            self._config.url,
            encoding="utf-8",
            decode_responses=self._config.decode_responses,
            max_connections=self._config.pool_size,
            socket_connect_timeout=self._config.socket_connect_timeout,
            socket_timeout=self._config.socket_timeout,
            retry_on_timeout=self._config.retry_on_timeout,
            health_check_interval=self._config.health_check_interval,
        )
        return aioredis.Redis.from_pool(self._pool)

    async def _connect_sentinel(self) -> aioredis.Redis:
        sentinel_hosts = []
        for hostport in self._config.sentinel_hosts:
            parts = hostport.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 26379
            sentinel_hosts.append((host, port))

        sentinel_kwargs: dict[str, Any] = {}
        if self._config.sentinel_password:
            sentinel_kwargs["password"] = self._config.sentinel_password

        self._sentinel = Sentinel(
            sentinel_hosts,
            sentinel_kwargs=sentinel_kwargs,
            socket_timeout=self._config.socket_timeout,
        )

        return self._sentinel.master_for(
            self._config.sentinel_master,
            db=0,
            password=self._config.sentinel_password or None,
            decode_responses=self._config.decode_responses,
        )

    async def _verify_connection(self, client: aioredis.Redis) -> None:
        for attempt in range(1, self._config.max_retries + 1):
            try:
                await client.ping()
                return
            except Exception as e:
                logger.warning(f"Redis ping attempt {attempt}/{self._config.max_retries} failed: {e}")
                if attempt < self._config.max_retries:
                    await asyncio.sleep(self._config.retry_delay * attempt)
        raise ConnectionError(f"Redis connection failed after {self._config.max_retries} attempts")

    async def reconnect(self) -> aioredis.Redis:
        if self._reconnecting:
            if self._client:
                return self._client
            raise ConnectionError("Redis reconnection already in progress")

        self._reconnecting = True
        try:
            await self.shutdown()
            return await self._connect()
        finally:
            self._reconnecting = False

    async def shutdown(self) -> None:
        try:
            if self._client:
                await self._client.close()
        except Exception as e:
            logger.warning(f"Redis client close error: {e}")

        try:
            if self._pool:
                await self._pool.disconnect()
        except Exception as e:
            logger.warning(f"Redis pool disconnect error: {e}")

        self._client = None
        self._sentinel = None
        self._pool = None
        self._connected = False
        logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.ping()
            if not self._connected:
                self._connected = True
                set_redis_tier(RedisDegradationTier.NORMAL)
            return True
        except Exception:
            if self._connected:
                logger.warning("Redis health check failed")
                set_redis_tier(RedisDegradationTier.PARTIALLY_DEGRADED)
            self._connected = False
            return False

    def get_sentinel_slave(self):
        if self._config.sentinel_enabled and self._sentinel is not None:
            return self._sentinel.slave_for(
                self._config.sentinel_master,
                db=0,
                password=self._config.sentinel_password or None,
                decode_responses=self._config.decode_responses,
            )
        return None

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def pool(self) -> aioredis.ConnectionPool | None:
        return self._pool

    @property
    def config(self) -> RedisConfig:
        return self._config


redis_manager = RedisConnectionManager()
