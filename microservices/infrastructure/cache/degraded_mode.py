import time
from enum import IntEnum

from monitoring.logger import logger


class RedisDegradationTier(IntEnum):
    NORMAL = 1
    PARTIALLY_DEGRADED = 2
    FULLY_UNAVAILABLE = 3


_current_tier: RedisDegradationTier = RedisDegradationTier.NORMAL
_last_degraded_at: float | None = None
_recovery_attempts: int = 0
_recovery_threshold: int = 3
_recovery_cooldown: float = 30.0


def get_current_tier() -> RedisDegradationTier:
    return _current_tier


def set_redis_tier(tier: RedisDegradationTier) -> None:
    global _current_tier, _last_degraded_at, _recovery_attempts
    if tier != _current_tier:
        logger.warning(f"Redis degradation tier changed: {_current_tier.name} -> {tier.name}")
        if tier > _current_tier:
            _last_degraded_at = time.time()
            _recovery_attempts = 0
        _current_tier = tier


def is_redis_normal() -> bool:
    return _current_tier == RedisDegradationTier.NORMAL


def is_redis_degraded() -> bool:
    return _current_tier >= RedisDegradationTier.PARTIALLY_DEGRADED


def is_redis_unavailable() -> bool:
    return _current_tier == RedisDegradationTier.FULLY_UNAVAILABLE


def record_recovery_attempt() -> bool:
    global _recovery_attempts
    _recovery_attempts += 1
    if _recovery_attempts >= _recovery_threshold:
        _recovery_attempts = 0
        return True
    return False


def should_attempt_recovery() -> bool:
    if _last_degraded_at is None:
        return True
    return (time.time() - _last_degraded_at) >= _recovery_cooldown


def reset_degradation() -> None:
    global _current_tier, _last_degraded_at, _recovery_attempts
    _current_tier = RedisDegradationTier.NORMAL
    _last_degraded_at = None
    _recovery_attempts = 0
    logger.info("Redis degradation reset to NORMAL")


DEGRADED_MESSAGES = {
    "scheduling": "Scheduling is temporarily unavailable. Please try again later.",
    "rate_limit": "Service is under high load. Please slow down.",
    "memory": "I'm having trouble recalling previous conversations right now.",
    "general": "Some features are temporarily degraded. Please try again shortly.",
}


def get_degraded_message(service: str = "general") -> str:
    return DEGRADED_MESSAGES.get(service, DEGRADED_MESSAGES["general"])


class FallbackStrategy:
    CACHE_FALLBACK = "cache_fallback"
    LOCAL_FALLBACK = "local_fallback"
    GRACEFUL_DEGRADE = "graceful_degrade"
    REJECT = "reject"


def get_fallback_strategy(service: str = "general") -> str:
    if is_redis_unavailable():
        return FallbackStrategy.REJECT if service in ("idempotency", "locking") else FallbackStrategy.LOCAL_FALLBACK
    if is_redis_degraded():
        return FallbackStrategy.GRACEFUL_DEGRADE
    return FallbackStrategy.CACHE_FALLBACK
