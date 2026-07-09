from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

from observability.models import MetricsData


def _safe_counter(name: str, description: str, labels: list[str] | None = None) -> Counter:
    try:
        return Counter(name, description, labels or [])
    except ValueError:
        from prometheus_client.registry import REGISTRY
        samples = [s for s in REGISTRY.collect() if s.name == name]
        if samples:
            return Counter(name, description, labels or [], registry=None)
        raise


def _safe_gauge(name: str, description: str, labels: list[str] | None = None) -> Gauge:
    try:
        return Gauge(name, description, labels or [])
    except ValueError:
        return Gauge(name, description, labels or [], registry=None)


def _safe_histogram(
    name: str, description: str,
    labels: list[str] | None = None,
    buckets: tuple | None = None,
) -> Histogram:
    try:
        if buckets:
            return Histogram(name, description, labels or [], buckets=buckets)
        return Histogram(name, description, labels or [])
    except ValueError:
        return Histogram(name, description, labels or [], registry=None)


_singleton_registry: "MetricsRegistry | None" = None


class MetricsRegistry:
    _initialized: bool = False

    def __new__(cls) -> "MetricsRegistry":
        global _singleton_registry
        if _singleton_registry is None:
            instance = super().__new__(cls)
            instance._initialized = False
            _singleton_registry = instance
        return _singleton_registry

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.http_requests = _safe_counter(
            "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"],
        )
        self.http_latency = _safe_histogram(
            "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
        self.conversation_operations = _safe_counter(
            "conversation_operations_total", "Conversation operations", ["operation", "status"],
        )
        self.conversation_latency = _safe_histogram(
            "conversation_duration_seconds", "Conversation operation latency", ["operation"],
        )
        self.memory_operations = _safe_counter(
            "memory_operations_total", "Memory operations", ["operation", "status"],
        )
        self.memory_latency = _safe_histogram(
            "memory_duration_seconds", "Memory operation latency", ["operation"],
        )
        self.knowledge_operations = _safe_counter(
            "knowledge_operations_total", "Knowledge operations", ["operation", "status"],
        )
        self.knowledge_latency = _safe_histogram(
            "knowledge_duration_seconds", "Knowledge operation latency", ["operation"],
        )
        self.retrieval_operations = _safe_counter(
            "retrieval_operations_total", "Retrieval operations", ["operation", "status"],
        )
        self.retrieval_latency = _safe_histogram(
            "retrieval_duration_seconds", "Retrieval operation latency", ["operation"],
        )
        self.embedding_operations = _safe_counter(
            "embedding_operations_total", "Embedding operations", ["operation", "status"],
        )
        self.embedding_latency = _safe_histogram(
            "embedding_duration_seconds", "Embedding operation latency", ["operation"],
        )
        self.prompt_operations = _safe_counter(
            "prompt_operations_total", "Prompt operations", ["operation", "status"],
        )
        self.prompt_latency = _safe_histogram(
            "prompt_duration_seconds", "Prompt operation latency", ["operation"],
        )
        self.provider_calls = _safe_counter(
            "provider_calls_total", "Provider calls", ["provider", "operation", "status"],
        )
        self.provider_latency = _safe_histogram(
            "provider_duration_seconds", "Provider call latency", ["provider", "operation"],
        )
        self.intent_operations = _safe_counter(
            "intent_operations_total", "Intent operations", ["operation", "status"],
        )
        self.intent_latency = _safe_histogram(
            "intent_duration_seconds", "Intent operation latency", ["operation"],
        )
        self.confirmation_operations = _safe_counter(
            "confirmation_operations_total", "Confirmation operations", ["operation", "status"],
        )
        self.confirmation_latency = _safe_histogram(
            "confirmation_duration_seconds", "Confirmation operation latency", ["operation"],
        )
        self.meeting_operations = _safe_counter(
            "meeting_operations_total", "Meeting operations", ["operation", "status"],
        )
        self.meeting_latency = _safe_histogram(
            "meeting_duration_seconds", "Meeting operation latency", ["operation"],
        )
        self.workflow_operations = _safe_counter(
            "workflow_operations_total", "Workflow operations", ["operation", "status"],
        )
        self.workflow_latency = _safe_histogram(
            "workflow_duration_seconds", "Workflow operation latency", ["operation"],
        )
        self.redis_operations = _safe_counter(
            "redis_operations_total", "Redis operations", ["operation", "status"],
        )
        self.redis_latency = _safe_histogram(
            "redis_duration_seconds", "Redis operation latency", ["operation"],
        )
        self.postgresql_operations = _safe_counter(
            "postgresql_operations_total", "PostgreSQL operations", ["operation", "status"],
        )
        self.postgresql_latency = _safe_histogram(
            "postgresql_duration_seconds", "PostgreSQL operation latency", ["operation"],
        )
        self.celery_tasks = _safe_counter(
            "celery_tasks_total", "Celery tasks", ["queue", "task", "status"],
        )
        self.celery_latency = _safe_histogram(
            "celery_duration_seconds", "Celery task latency", ["queue", "task"],
        )
        self.n8n_operations = _safe_counter(
            "n8n_operations_total", "n8n operations", ["operation", "status"],
        )
        self.n8n_latency = _safe_histogram(
            "n8n_duration_seconds", "n8n operation latency", ["operation"],
        )
        self.errors_total = _safe_counter(
            "errors_total", "Total errors", ["component", "error_type"],
        )
        self.retries_total = _safe_counter("retries_total", "Total retries", ["component"])
        self.tokens_used = _safe_counter("tokens_total", "Total tokens used", ["model", "type"])
        self.cost_total = _safe_counter("cost_total_usd", "Total cost in USD", ["model", "type"])
        self.active_workflows = _safe_gauge("obs_active_workflows", "Active workflow count")
        self.queue_depth = _safe_gauge("obs_queue_depth", "Queue depth", ["queue"])
        self.active_connections = _safe_gauge("obs_active_connections", "Active connections", ["connection_type"])

    def get_latest_metrics(self) -> bytes:
        return generate_latest()

    def snapshot(self) -> MetricsData:
        return MetricsData()

    def export_prometheus(self) -> bytes:
        return self.get_latest_metrics()
