import time
from dataclasses import dataclass

import redis.asyncio as aioredis

from infrastructure.cache.degraded_mode import is_redis_degraded
from infrastructure.cache.key_builder import default_key_builder
from monitoring.logger import logger


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: float
    limit: int
    retry_after: float = 0.0


class SlidingWindowRateLimiter:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def check(self, identifier: str, limit: int, window: int = 60) -> RateLimitResult:
        key = default_key_builder.rate_limit(identifier, f"{window}s")
        now = time.time()
        window_start = now - window

        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local window = tonumber(ARGV[4])

        redis.call("ZREMRANGEBYSCORE", key, 0, window_start)
        local count = redis.call("ZCARD", key)

        if count < limit then
            redis.call("ZADD", key, now, now)
            redis.call("EXPIRE", key, window)
            return {1, limit - count - 1, now + window}
        else
            local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
            local reset_at = tonumber(oldest[2]) + window
            local retry_after = reset_at - now
            return {0, 0, reset_at, retry_after}
        end
        """

        try:
            result = await self._redis.eval(  # type: ignore[misc]
                lua_script, 1, key,
                str(now), str(window_start), str(limit), str(window),
            )
            allowed = bool(result[0])
            return RateLimitResult(
                allowed=allowed,
                remaining=int(result[1]) if len(result) > 1 else 0,
                reset_at=float(result[2]) if len(result) > 2 else now + window,
                limit=limit,
                retry_after=float(result[3]) if len(result) > 3 and result[3] else 0.0,
            )
        except Exception as e:
            logger.warning(f"Rate limiter error for {identifier}: {e}")
            if is_redis_degraded():
                return RateLimitResult(allowed=True, remaining=1, reset_at=now + window, limit=limit)
            return RateLimitResult(allowed=False, remaining=0, reset_at=now + window, limit=limit)


class TokenBucketRateLimiter:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def check(self, identifier: str, capacity: int, refill_rate: float, refill_time: int = 60) -> RateLimitResult:
        key = default_key_builder.rate_limit(identifier, f"bucket_{refill_time}s")
        now = time.time()

        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])

        local bucket = redis.call("HMGET", key, "tokens", "last_refill")
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now

        local elapsed = now - last_refill
        tokens = math.min(capacity, tokens + elapsed * refill_rate)

        if tokens >= 1 then
            redis.call("HMSET", key, "tokens", tokens - 1, "last_refill", now)
            redis.call("EXPIRE", key, 60)
            return {1, math.floor(tokens - 1), now + 60}
        else
            local refill_needed = (1 - tokens) / refill_rate
            return {0, 0, now + refill_needed}
        end
        """

        try:
            result = await self._redis.eval(  # type: ignore[misc]
                lua_script, 1, key,
                str(now), str(capacity), str(refill_rate),
            )
            allowed = bool(result[0])
            return RateLimitResult(
                allowed=allowed,
                remaining=int(result[1]) if len(result) > 1 else 0,
                reset_at=float(result[2]) if len(result) > 2 else now + refill_time,
                limit=capacity,
                retry_after=float(result[3]) if len(result) > 3 and result[3] else 0.0,
            )
        except Exception as e:
            logger.warning(f"Token bucket error for {identifier}: {e}")
            if is_redis_degraded():
                return RateLimitResult(allowed=True, remaining=1, reset_at=now + refill_time, limit=capacity)
            return RateLimitResult(allowed=False, remaining=0, reset_at=now + refill_time, limit=capacity)


class DistributedRateLimiter:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._sliding_window = SlidingWindowRateLimiter(redis)
        self._token_bucket = TokenBucketRateLimiter(redis)

    async def check_user(self, user_id: str, limit: int = 60, window: int = 60) -> RateLimitResult:
        return await self._sliding_window.check(f"user:{user_id}", limit, window)

    async def check_anonymous(self, ip: str, limit: int = 30, window: int = 60) -> RateLimitResult:
        return await self._sliding_window.check(f"anon:{ip}", limit, window)

    async def check_burst(self, identifier: str, burst_limit: int = 5, burst_window: int = 10) -> RateLimitResult:
        return await self._sliding_window.check(f"burst:{identifier}", burst_limit, burst_window)

    async def check_token_bucket(
        self, identifier: str, capacity: int = 100, refill_rate: float = 1.0
    ) -> RateLimitResult:
        return await self._token_bucket.check(identifier, capacity, refill_rate)
