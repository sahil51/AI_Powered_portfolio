import logging

from prometheus_client import REGISTRY, Gauge

logger = logging.getLogger("ai_assistant")


class PerformanceMetrics:
    def __init__(self, registry=None) -> None:
        self.registry = registry or REGISTRY
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        try:
            self.latency_seconds = Gauge(
                "assistant_perf_latency_seconds",
                "Execution latency in seconds per component",
                ["component", "operation"],
                registry=self.registry,
            )
            self.cpu_usage = Gauge(
                "assistant_cpu_usage_ratio",
                "CPU usage ratio",
                registry=self.registry,
            )
            self.memory_usage = Gauge(
                "assistant_memory_usage_bytes",
                "Memory usage in bytes",
                registry=self.registry,
            )
            self.pool_active = Gauge(
                "assistant_conn_pool_active",
                "Active connections in pool",
                ["pool_type"],
                registry=self.registry,
            )
            self.pool_idle = Gauge(
                "assistant_conn_pool_idle",
                "Idle connections in pool",
                ["pool_type"],
                registry=self.registry,
            )
            self.async_tasks = Gauge(
                "assistant_async_tasks_active",
                "Number of active asyncio tasks",
                registry=self.registry,
            )
            self.thread_count = Gauge(
                "assistant_thread_count",
                "Active OS thread count",
                registry=self.registry,
            )
            self.queue_depth = Gauge(
                "assistant_queue_depth",
                "Celery task queue depth",
                ["queue_name"],
                registry=self.registry,
            )
        except ValueError:
            # Metrics already registered
            self.latency_seconds = self.registry._names_to_collectors.get("assistant_perf_latency_seconds")
            self.cpu_usage = self.registry._names_to_collectors.get("assistant_cpu_usage_ratio")
            self.memory_usage = self.registry._names_to_collectors.get("assistant_memory_usage_bytes")
            self.pool_active = self.registry._names_to_collectors.get("assistant_conn_pool_active")
            self.pool_idle = self.registry._names_to_collectors.get("assistant_conn_pool_idle")
            self.async_tasks = self.registry._names_to_collectors.get("assistant_async_tasks_active")
            self.thread_count = self.registry._names_to_collectors.get("assistant_thread_count")
            self.queue_depth = self.registry._names_to_collectors.get("assistant_queue_depth")

    def record_latency(self, component: str, operation: str, duration_seconds: float) -> None:
        if self.latency_seconds:
            self.latency_seconds.labels(component=component, operation=operation).set(duration_seconds)

    def record_resources(self, cpu_ratio: float, memory_bytes: float, threads: int, tasks: int) -> None:
        if self.cpu_usage:
            self.cpu_usage.set(cpu_ratio)
        if self.memory_usage:
            self.memory_usage.set(memory_bytes)
        if self.thread_count:
            self.thread_count.set(threads)
        if self.async_tasks:
            self.async_tasks.set(tasks)

    def record_pool(self, pool_type: str, active: int, idle: int) -> None:
        if self.pool_active:
            self.pool_active.labels(pool_type=pool_type).set(active)
        if self.pool_idle:
            self.pool_idle.labels(pool_type=pool_type).set(idle)

    def record_queue_depth(self, queue_name: str, depth: int) -> None:
        if self.queue_depth:
            self.queue_depth.labels(queue_name=queue_name).set(depth)
