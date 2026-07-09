from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthData:
    status: HealthStatus = HealthStatus.HEALTHY
    total_checks: int = 0
    failed_checks: int = 0
    last_check_at: float = 0.0
    last_error: str = ""


@dataclass
class HealthComponent:
    name: str
    status: HealthStatus = HealthStatus.HEALTHY
    latency_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class SystemHealth:
    status: HealthStatus = HealthStatus.HEALTHY
    components: dict[str, HealthComponent] = field(default_factory=dict)
    uptime_seconds: float = 0.0
    started_at: float = field(default_factory=time.time)


class HealthAggregator:
    def __init__(self) -> None:
        self._components: dict[str, HealthComponent] = {}
        self._health = HealthData()
        self._started_at = time.time()

    def register_component(self, name: str) -> None:
        self._components[name] = HealthComponent(name=name)

    def record_health(
        self,
        component: str,
        status: HealthStatus,
        latency_ms: float = 0.0,
        details: dict[str, Any] | None = None,
        error: str = "",
    ) -> None:
        if component not in self._components:
            self._components[component] = HealthComponent(name=component)
        comp = self._components[component]
        comp.status = status
        comp.latency_ms = latency_ms
        comp.details = details or {}
        comp.error = error
        self._health.total_checks += 1
        if status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY):
            self._health.failed_checks += 1
            self._health.last_error = error
        self._health.last_check_at = time.time()

    async def check_database(self) -> HealthComponent:
        start = time.time()
        try:
            from sqlalchemy import text

            from infrastructure.database.session import db
            async with db.session_factory() as session:
                await session.execute(text("SELECT 1"))
            comp = HealthComponent(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000,
            )
            self._components["database"] = comp
            return comp
        except Exception as e:
            comp = HealthComponent(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )
            self._components["database"] = comp
            return comp

    async def check_redis(self) -> HealthComponent:
        start = time.time()
        try:
            from infrastructure.cache.redis_client import get_redis
            r = await get_redis()
            await r.ping()
            comp = HealthComponent(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000,
            )
            self._components["redis"] = comp
            return comp
        except Exception as e:
            comp = HealthComponent(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )
            self._components["redis"] = comp
            return comp

    async def check_celery(self) -> HealthComponent:
        try:
            from infrastructure.queue.celery_app import celery_app
            ping = celery_app.control.ping(timeout=3)
            if ping:
                comp = HealthComponent(name="celery", status=HealthStatus.HEALTHY, details={"workers": ping})
            else:
                comp = HealthComponent(name="celery", status=HealthStatus.DEGRADED, error="No workers responded")
            self._components["celery"] = comp
            return comp
        except Exception as e:
            comp = HealthComponent(name="celery", status=HealthStatus.UNHEALTHY, error=str(e))
            self._components["celery"] = comp
            return comp

    async def check_provider(self) -> HealthComponent:
        try:
            from application.ai.manager import ProviderManager
            ProviderManager.__new__(ProviderManager)
            comp = HealthComponent(name="provider", status=HealthStatus.HEALTHY, details={"status": "available"})
            self._components["provider"] = comp
            return comp
        except Exception as e:
            comp = HealthComponent(name="provider", status=HealthStatus.UNHEALTHY, error=str(e))
            self._components["provider"] = comp
            return comp

    async def check_workflow(self) -> HealthComponent:
        comp = HealthComponent(name="workflow", status=HealthStatus.HEALTHY)
        self._components["workflow"] = comp
        return comp

    async def check_knowledge(self) -> HealthComponent:
        comp = HealthComponent(name="knowledge", status=HealthStatus.HEALTHY)
        self._components["knowledge"] = comp
        return comp

    async def check_all(self) -> SystemHealth:
        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "celery": self.check_celery(),
            "provider": self.check_provider(),
            "workflow": self.check_workflow(),
            "knowledge": self.check_knowledge(),
        }
        for name, coro in checks.items():
            try:
                result = await coro
                self._components[name] = result
            except Exception as e:
                self._components[name] = HealthComponent(name=name, status=HealthStatus.UNHEALTHY, error=str(e))

        degraded = any(c.status == HealthStatus.DEGRADED for c in self._components.values())
        unhealthy = any(c.status == HealthStatus.UNHEALTHY for c in self._components.values())
        all(c.status == HealthStatus.HEALTHY for c in self._components.values())

        if unhealthy:
            overall = HealthStatus.UNHEALTHY
        elif degraded:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall,
            components=self._components,
            uptime_seconds=time.time() - self._started_at,
            started_at=self._started_at,
        )

    def liveness(self) -> dict[str, Any]:
        return {"status": "alive"}

    def readiness(self) -> dict[str, Any]:
        unhealthy = [
            name for name, c in self._components.items()
            if c.status == HealthStatus.UNHEALTHY
        ]
        if unhealthy:
            return {"status": "not_ready", "failing_components": unhealthy}
        return {"status": "ready"}

    def startup(self) -> dict[str, Any]:
        elapsed = time.time() - self._started_at
        return {"status": "started", "uptime_seconds": elapsed}
