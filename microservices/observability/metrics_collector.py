from __future__ import annotations

from observability.metrics_registry import MetricsRegistry
from observability.models import MetricsData


class MetricsCollector:
    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry
        self._data = MetricsData()

    def record_http_request(self, method: str, endpoint: str, status: int, latency_ms: float) -> None:
        self._registry.http_requests.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self._registry.http_latency.labels(method=method, endpoint=endpoint).observe(latency_ms / 1000.0)
        self._data.http_requests_total += 1
        if status >= 400:
            self._data.http_errors_total += 1
        self._data.http_latency_ms_total += latency_ms

    def record_conversation(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.conversation_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.conversation_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.conversation_total += 1

    def record_memory(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.memory_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.memory_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.memory_operations_total += 1

    def record_knowledge(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.knowledge_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.knowledge_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.knowledge_operations_total += 1

    def record_retrieval(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.retrieval_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.retrieval_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.retrieval_operations_total += 1

    def record_embedding(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.embedding_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.embedding_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.embedding_operations_total += 1

    def record_prompt(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.prompt_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.prompt_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.prompt_operations_total += 1

    def record_provider_call(self, provider: str, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.provider_calls.labels(provider=provider, operation=operation, status=status).inc()
        if latency_ms:
            self._registry.provider_latency.labels(provider=provider, operation=operation).observe(latency_ms / 1000.0)
        self._data.provider_calls_total += 1

    def record_intent(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.intent_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.intent_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.intent_operations_total += 1

    def record_confirmation(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.confirmation_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.confirmation_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.confirmation_operations_total += 1

    def record_meeting(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.meeting_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.meeting_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.meeting_operations_total += 1

    def record_workflow(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.workflow_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.workflow_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.workflow_operations_total += 1

    def record_redis(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.redis_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.redis_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.redis_operations_total += 1

    def record_postgresql(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.postgresql_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.postgresql_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.postgresql_operations_total += 1

    def record_celery_task(self, queue: str, task: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.celery_tasks.labels(queue=queue, task=task, status=status).inc()
        if latency_ms:
            self._registry.celery_latency.labels(queue=queue, task=task).observe(latency_ms / 1000.0)
        self._data.celery_tasks_total += 1

    def record_n8n(self, operation: str, status: str, latency_ms: float = 0.0) -> None:
        self._registry.n8n_operations.labels(operation=operation, status=status).inc()
        if latency_ms:
            self._registry.n8n_latency.labels(operation=operation).observe(latency_ms / 1000.0)
        self._data.n8n_operations_total += 1

    def record_error(self, component: str, error_type: str) -> None:
        self._registry.errors_total.labels(component=component, error_type=error_type).inc()
        self._data.errors_total += 1

    def record_retry(self, component: str) -> None:
        self._registry.retries_total.labels(component=component).inc()
        self._data.retries_total += 1

    def record_token_usage(self, model: str, token_type: str, count: int) -> None:
        self._registry.tokens_used.labels(model=model, type=token_type).inc(count)
        self._data.tokens_used_total += count

    def record_cost(self, model: str, cost_type: str, cost: float) -> None:
        self._registry.cost_total.labels(model=model, type=cost_type).inc(cost)
        self._data.cost_total += cost

    def set_active_workflows(self, count: int) -> None:
        self._registry.active_workflows.set(count)

    def set_queue_depth(self, queue: str, depth: int) -> None:
        self._registry.queue_depth.labels(queue=queue).set(depth)

    def set_active_connections(self, connection_type: str, count: int) -> None:
        self._registry.active_connections.labels(connection_type=connection_type).set(count)

    def get_metrics_data(self) -> MetricsData:
        return self._data

    def reset(self) -> None:
        self._data = MetricsData()
