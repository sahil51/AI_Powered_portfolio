import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram

conversation_counter = Counter("conversations_total", "Total conversations processed")
message_counter = Counter("messages_total", "Total messages processed", ["intent"])
llm_requests = Counter("llm_requests_total", "Total LLM requests", ["model", "status"])
llm_latency = Histogram("llm_request_duration_seconds", "LLM request latency", ["model"])
tool_executions = Counter("tool_executions_total", "Total tool executions", ["tool", "status"])
workflow_states = Gauge("active_workflows", "Active workflow count")
task_queue_size = Gauge("celery_queue_size", "Celery task queue size", ["queue"])


def track_llm_call(model: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                llm_requests.labels(model=model, status="success").inc()
                return result
            except Exception:
                llm_requests.labels(model=model, status="error").inc()
                raise
            finally:
                llm_latency.labels(model=model).observe(time.time() - start)

        return wrapper

    return decorator
