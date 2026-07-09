import time
from dataclasses import dataclass, field

from celery.utils.imports import import_from_cwd

from monitoring.logger import logger


@dataclass
class CeleryMetrics:
    active_tasks: int = 0
    scheduled_tasks: int = 0
    reserved_tasks: int = 0
    processed_total: int = 0
    failed_total: int = 0
    retry_total: int = 0
    worker_count: int = 0
    queue_depths: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class CeleryMonitor:
    def __init__(self) -> None:
        self._start_time = time.monotonic()

    async def collect_metrics(self) -> CeleryMetrics:
        metrics = CeleryMetrics()
        app = import_from_cwd("infrastructure.queue.celery_app:celery_app")

        try:
            inspector = app.control.inspect()
            stats = inspector.stats()
            if stats:
                metrics.worker_count = len(stats)
                for worker, worker_stats in stats.items():
                    metrics.active_tasks += worker_stats.get("active", 0)
                    metrics.scheduled_tasks += worker_stats.get("scheduled", 0)
                    metrics.reserved_tasks += worker_stats.get("reserved", 0)
                    metrics.processed_total += worker_stats.get("processed", 0)
                    metrics.failed_total += worker_stats.get("failed", 0)
                    metrics.retry_total += worker_stats.get("retries", 0)
        except Exception as e:
            metrics.errors.append(f"Inspection failed: {e}")

        try:
            queues = inspect_queues(app)
            metrics.queue_depths = queues
        except Exception as e:
            metrics.errors.append(f"Queue inspection failed: {e}")

        return metrics

    @property
    def uptime(self) -> float:
        return time.monotonic() - self._start_time


def inspect_queues(app) -> dict[str, int]:
    depths: dict[str, int] = {}
    try:
        with app.connection_or_acquire() as conn:
            client = conn.channel().client
            queue_names = [
                "default", "critical", "memory", "embeddings",
                "workflow", "notifications", "meetings", "maintenance",
            ]
            for qname in queue_names:
                key = f"celery@celery.{qname}"
                try:
                    depth = client.llen(key)
                    depths[qname] = depth
                except Exception:
                    depths[qname] = -1
    except Exception as e:
        logger.warning(f"Queue inspection failed: {e}")
    return depths


celery_monitor = CeleryMonitor()
