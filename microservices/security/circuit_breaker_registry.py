from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: float = 0.0
    last_success_at: float = 0.0
    failure_threshold: int = 5
    success_threshold: int = 3
    reset_timeout_seconds: float = 60.0
    half_open_max_calls: int = 3
    half_open_calls: int = 0


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def register(self, name: str, failure_threshold: int = 5, reset_timeout_seconds: float = 60.0) -> CircuitBreaker:
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            reset_timeout_seconds=reset_timeout_seconds,
        )
        self._breakers[name] = breaker
        return breaker

    def get(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def get_or_create(self, name: str) -> CircuitBreaker:
        breaker = self._breakers.get(name)
        if breaker is None:
            breaker = self.register(name)
        return breaker

    def record_success(self, name: str) -> None:
        breaker = self.get_or_create(name)
        breaker.success_count += 1
        breaker.last_success_at = time.time()
        if breaker.state == CircuitState.HALF_OPEN:
            breaker.half_open_calls += 1
            if breaker.half_open_calls >= breaker.half_open_max_calls and breaker.success_count >= breaker.success_threshold:  # noqa: E501
                breaker.state = CircuitState.CLOSED
                breaker.failure_count = 0
                breaker.half_open_calls = 0
        elif breaker.state == CircuitState.CLOSED:
            breaker.failure_count = 0

    def record_failure(self, name: str) -> None:
        breaker = self.get_or_create(name)
        breaker.failure_count += 1
        breaker.last_failure_at = time.time()
        if breaker.state == CircuitState.CLOSED:
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitState.OPEN
        elif breaker.state == CircuitState.HALF_OPEN:
            breaker.state = CircuitState.OPEN
            breaker.failure_count = 0

    def is_available(self, name: str) -> bool:
        breaker = self._breakers.get(name)
        if breaker is None:
            return True
        if breaker.state == CircuitState.CLOSED:
            return True
        if breaker.state == CircuitState.OPEN:
            elapsed = time.time() - breaker.last_failure_at
            if elapsed >= breaker.reset_timeout_seconds:
                breaker.state = CircuitState.HALF_OPEN
                breaker.half_open_calls = 0
                breaker.success_count = 0
                return True
            return False
        if breaker.state == CircuitState.HALF_OPEN:
            if breaker.half_open_calls < breaker.half_open_max_calls:
                return True
            return False
        return True

    def get_state(self, name: str) -> CircuitState:
        breaker = self._breakers.get(name)
        if breaker is None:
            return CircuitState.CLOSED
        return breaker.state

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count,
                "failure_threshold": breaker.failure_threshold,
                "success_threshold": breaker.success_threshold,
                "reset_timeout_seconds": breaker.reset_timeout_seconds,
                "last_failure_at": breaker.last_failure_at,
                "last_success_at": breaker.last_success_at,
            }
            for name, breaker in self._breakers.items()
        }

    def reset(self, name: str) -> None:
        breaker = self._breakers.get(name)
        if breaker:
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.success_count = 0
            breaker.half_open_calls = 0

    def reset_all(self) -> None:
        for name in list(self._breakers.keys()):
            self.reset(name)

    def unregister(self, name: str) -> None:
        self._breakers.pop(name, None)
