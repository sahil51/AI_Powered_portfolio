from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from monitoring.health import HealthChecker
from observability.health_aggregator import HealthAggregator

router = APIRouter(tags=["Health"])

_aggregator: HealthAggregator | None = None


def _get_aggregator() -> HealthAggregator:
    global _aggregator
    if _aggregator is None:
        from application.di.container import container
        from observability.manager import ObservabilityManager

        try:
            mgr = container.resolve(ObservabilityManager)
            _aggregator = mgr.health_aggregator
        except Exception:
            _aggregator = HealthAggregator()
    return _aggregator


@router.get("/health")
async def health_check():
    return await HealthChecker.check_all()


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    aggregator = _get_aggregator()
    return aggregator.readiness()


@router.get("/health/startup")
async def startup():
    aggregator = _get_aggregator()
    return aggregator.startup()


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    from application.di.container import container
    from observability.manager import ObservabilityManager

    try:
        mgr = container.resolve(ObservabilityManager)
        return mgr.metrics_registry.export_prometheus()
    except Exception:
        return PlainTextResponse("# Metrics not available", status_code=503)


@router.get("/health/system")
async def system_health():
    aggregator = _get_aggregator()
    system = await aggregator.check_all()
    return {
        "status": system.status.value,
        "uptime_seconds": system.uptime_seconds,
        "components": {
            name: {
                "status": comp.status.value,
                "latency_ms": comp.latency_ms,
                "error": comp.error,
            }
            for name, comp in system.components.items()
        },
    }
