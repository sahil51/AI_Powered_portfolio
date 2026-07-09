from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from security.exceptions import RateLimitExceededError
from security.models import RateLimitScope


@dataclass
class RateLimitRule:
    scope: RateLimitScope
    max_requests: int
    window_seconds: int = 60
    burst_multiplier: int = 2
    name: str = ""


class RateLimitManager:
    def __init__(self) -> None:
        self._rules: list[RateLimitRule] = []
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def add_rule(self, rule: RateLimitRule) -> None:
        self._rules.append(rule)

    def remove_rule(self, name: str) -> None:
        self._rules = [r for r in self._rules if r.name != name]

    def get_rules(self) -> list[RateLimitRule]:
        return list(self._rules)

    def _make_key(self, scope: RateLimitScope, identifier: str) -> str:
        return f"{scope.value}:{identifier}"

    def _clean_expired(self, key: str, window: int) -> None:
        now = time.time()
        self._buckets[key] = [t for t in self._buckets[key] if now - t < window]

    def check_rate_limit(self, scope: RateLimitScope, identifier: str) -> dict[str, Any]:
        now = time.time()
        matching_rules = [r for r in self._rules if r.scope == scope]
        if not matching_rules:
            return {"allowed": True, "remaining": 0, "reset_at": 0}

        result = {"allowed": True, "rules_applied": 0, "remaining": 0, "reset_at": 0}
        for rule in matching_rules:
            key = self._make_key(scope, identifier)
            self._clean_expired(key, rule.window_seconds)
            current_count = len(self._buckets[key])
            burst_limit = rule.max_requests * rule.burst_multiplier
            window_start = now - (now % rule.window_seconds)
            reset_at = window_start + rule.window_seconds

            if current_count >= burst_limit:
                return {
                    "allowed": False,
                    "error": f"Rate limit exceeded for {scope.value}:{identifier}",
                    "limit": rule.max_requests,
                    "burst_limit": burst_limit,
                    "current": current_count,
                    "remaining": 0,
                    "reset_at": reset_at,
                }

            if current_count < rule.max_requests:
                self._buckets[key].append(now)
            else:
                self._buckets[key].append(now)

            result = {
                "allowed": True,
                "limit": rule.max_requests,
                "burst_limit": burst_limit,
                "current": current_count + 1,
                "remaining": max(0, burst_limit - current_count - 1),
                "reset_at": reset_at,  # type: ignore[dict-item]
            }

        return result

    def validate(
        self,
        scope: RateLimitScope,
        identifier: str,
    ) -> None:
        result = self.check_rate_limit(scope, identifier)
        if not result["allowed"]:
            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {identifier}",
                detail=result.get("error", ""),
            )

    def load_default_rules(self) -> None:
        self.add_rule(RateLimitRule(
            name="anonymous",
            scope=RateLimitScope.ANONYMOUS,
            max_requests=10,
            window_seconds=60,
        ))
        self.add_rule(RateLimitRule(
            name="authenticated",
            scope=RateLimitScope.AUTHENTICATED,
            max_requests=100,
            window_seconds=60,
        ))
        self.add_rule(RateLimitRule(
            name="per_user",
            scope=RateLimitScope.USER,
            max_requests=200,
            window_seconds=60,
        ))
        self.add_rule(RateLimitRule(
            name="per_tenant",
            scope=RateLimitScope.TENANT,
            max_requests=1000,
            window_seconds=60,
        ))
        self.add_rule(RateLimitRule(
            name="per_workflow",
            scope=RateLimitScope.WORKFLOW,
            max_requests=50,
            window_seconds=60,
        ))

    def get_limits_for(self, identifier: str) -> list[dict[str, Any]]:
        results = []
        for rule in self._rules:
            key = self._make_key(rule.scope, identifier)
            self._clean_expired(key, rule.window_seconds)
            current = len(self._buckets[key])
            results.append({
                "scope": rule.scope.value,
                "identifier": identifier,
                "limit": rule.max_requests,
                "burst_limit": rule.max_requests * rule.burst_multiplier,
                "current": current,
                "remaining": max(0, (rule.max_requests * rule.burst_multiplier) - current),
            })
        return results

    def reset(self) -> None:
        self._buckets.clear()
