from dataclasses import dataclass, field

from celery.utils.imports import import_from_cwd

from monitoring.logger import logger


@dataclass
class CeleryHealthStatus:
    worker_alive: bool = False
    queues_ok: bool = False
    broker_connected: bool = False
    active_tasks: int = 0
    scheduled_tasks: int = 0
    reserved_tasks: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.broker_connected and not self.errors


async def check_celery_health() -> CeleryHealthStatus:
    status = CeleryHealthStatus()
    app = import_from_cwd("infrastructure.queue.celery_app:celery_app")

    try:
        inspector = app.control.inspect()
        stats = inspector.stats()
        if stats:
            status.worker_alive = True
            for worker, worker_stats in stats.items():
                status.active_tasks += worker_stats.get("active", 0)
                status.scheduled_tasks += worker_stats.get("scheduled", 0)
                status.reserved_tasks += worker_stats.get("reserved", 0)
        else:
            status.errors.append("No workers responded to inspection")
    except Exception as e:
        status.errors.append(f"Inspection failed: {e}")

    try:
        conn = app.connection_or_acquire()
        conn.ensure_connection(max_retries=1)
        status.broker_connected = True
        conn.release()
    except Exception as e:
        status.errors.append(f"Broker connection failed: {e}")

    return status


async def get_queue_depth(queue_name: str = "default") -> int:
    app = import_from_cwd("infrastructure.queue.celery_app:celery_app")
    try:
        with app.connection_or_acquire() as conn:
            try:
                client = conn.channel().client
                queue_key = f"celery@celery.{queue_name}"
                return client.llen(queue_key)
            except Exception:
                return 0
    except Exception as e:
        logger.warning(f"Queue depth check failed for {queue_name}: {e}")
        return -1
