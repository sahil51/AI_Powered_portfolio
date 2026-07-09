from fastapi import APIRouter

from application.di.container import container
from observability.manager import ObservabilityManager
from security.manager import SecurityManager

router = APIRouter(prefix="/security", tags=["Security"])


def _get_security_manager() -> SecurityManager:
    try:
        return container.resolve(SecurityManager)
    except Exception:
        from security.manager import SecurityManager as SM
        return SM()


def _get_observability_manager() -> ObservabilityManager:
    try:
        return container.resolve(ObservabilityManager)
    except Exception:
        from observability.manager import ObservabilityManager as OM
        return OM()


@router.get("/status")
async def security_status():
    mgr = _get_security_manager()
    return mgr.security_report()


@router.get("/audit")
async def audit_log(limit: int = 100):
    mgr = _get_security_manager()
    return mgr.audit_logger.audit_report(limit=limit)


@router.get("/resilience")
async def resilience_status():
    mgr = _get_security_manager()
    return mgr.resilience_report()


@router.get("/circuit-breakers")
async def circuit_breakers():
    mgr = _get_security_manager()
    return mgr.circuit_breaker_registry.get_all_states()


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    mgr = _get_security_manager()
    mgr.circuit_breaker_registry.reset(name)
    return {"status": "reset", "name": name}


@router.get("/observability/status")
async def observability_status():
    mgr = _get_observability_manager()
    return {
        "initialized": mgr.initialized,
        "telemetry": mgr.telemetry_configuration.to_dict(),
        "alert_rules": mgr.alert_configuration.to_dict(),
        "dashboard_panels": mgr.dashboard_configuration.to_dict(),
    }


@router.get("/observability/health")
async def observability_health():
    mgr = _get_observability_manager()
    return await mgr.health_report()


@router.get("/observability/metrics")
async def observability_metrics():
    mgr = _get_observability_manager()
    return mgr.metrics_report()


@router.get("/observability/traces")
async def observability_traces():
    mgr = _get_observability_manager()
    return mgr.tracing_report()
