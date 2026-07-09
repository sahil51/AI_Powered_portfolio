from __future__ import annotations

import contextvars
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings


@dataclass
class SpanContext:
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    baggage: dict[str, str] = field(default_factory=dict)


_current_span: contextvars.ContextVar[SpanContext | None] = contextvars.ContextVar("current_span", default=None)


class TracingManager:
    def __init__(self, service_name: str = "ai_assistant") -> None:
        self._service_name = service_name
        self._enabled = settings.environment != "development" or settings.langsmith_tracing
        self._spans: list[dict[str, Any]] = []

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start_trace(self, operation_name: str, baggage: dict[str, str] | None = None) -> SpanContext:
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        ctx = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            baggage=baggage or {},
        )
        _current_span.set(ctx)
        if self._enabled:
            self._spans.append({
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": "",
                "operation_name": operation_name,
                "start_time": time.time(),
                "attributes": {},
            })
        return ctx

    def start_span(self, operation_name: str) -> SpanContext:
        parent = _current_span.get()
        trace_id = parent.trace_id if parent else str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_span_id = parent.span_id if parent else ""
        ctx = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=parent.baggage if parent else {},
        )
        _current_span.set(ctx)
        if self._enabled:
            self._spans.append({
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "operation_name": operation_name,
                "start_time": time.time(),
                "attributes": {},
            })
        return ctx

    def end_span(self, status: str = "ok", attributes: dict[str, Any] | None = None) -> None:
        current = _current_span.get()
        if current and self._enabled:
            for span in self._spans:
                if span["span_id"] == current.span_id:
                    span["end_time"] = time.time()
                    span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
                    span["status"] = status
                    if attributes:
                        span["attributes"].update(attributes)
                    break

    def inject_headers(self, headers: dict[str, str]) -> dict[str, str]:
        current = _current_span.get()
        if current:
            headers["X-Trace-ID"] = current.trace_id
            headers["X-Span-ID"] = current.span_id
        return headers

    def extract_from_headers(self, headers: dict[str, str]) -> SpanContext | None:
        trace_id = headers.get("X-Trace-ID", "")
        span_id = headers.get("X-Span-ID", "")
        if trace_id and span_id:
            ctx = SpanContext(trace_id=trace_id, span_id=span_id)
            _current_span.set(ctx)
            return ctx
        return None

    def get_current_span(self) -> SpanContext | None:
        return _current_span.get()

    def add_span_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        current = _current_span.get()
        if current and self._enabled:
            for span in self._spans:
                if span["span_id"] == current.span_id:
                    span.setdefault("events", []).append({
                        "name": name,
                        "timestamp": time.time(),
                        "attributes": attributes or {},
                    })
                    break

    def get_spans(self) -> list[dict[str, Any]]:
        return list(self._spans)

    def clear(self) -> None:
        self._spans.clear()
        _current_span.set(None)


def trace(operation_name: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = TracingManager()
            name = operation_name or func.__name__
            tracer.start_span(name)
            try:
                result = await func(*args, **kwargs)
                tracer.end_span("ok")
                return result
            except Exception as e:
                tracer.end_span("error", {"error": str(e)})
                raise
        return wrapper
    return decorator
