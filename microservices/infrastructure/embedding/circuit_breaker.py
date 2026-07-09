from __future__ import annotations

import time


class EmbeddingCircuitBreaker:
    def __init__(self, threshold: int = 5, reset_seconds: int = 60) -> None:
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._state: dict[str, dict] = {}

    def _get_provider_state(self, provider: str) -> dict:
        if provider not in self._state:
            self._state[provider] = {"failures": 0, "last_failure": 0.0, "last_success": 0.0}
        return self._state[provider]

    def is_open(self, provider: str) -> bool:
        state = self._get_provider_state(provider)
        if state["failures"] >= self._threshold:
            if time.time() - state["last_failure"] > self._reset_seconds:
                state["failures"] = 0
                return False
            return True
        return False

    def record_failure(self, provider: str) -> None:
        state = self._get_provider_state(provider)
        state["failures"] += 1
        state["last_failure"] = time.time()

    def record_success(self, provider: str) -> None:
        state = self._get_provider_state(provider)
        state["failures"] = 0
        state["last_success"] = time.time()
