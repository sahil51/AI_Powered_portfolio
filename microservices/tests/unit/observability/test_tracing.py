import pytest

from observability.tracing_manager import TracingManager, trace


class TestTracingManager:
    @pytest.fixture
    def tracer(self):
        return TracingManager(service_name="test")

    def test_start_trace(self, tracer):
        ctx = tracer.start_trace("test_operation")
        assert ctx.trace_id is not None
        assert ctx.span_id is not None
        assert ctx.parent_span_id == ""

    def test_start_span_with_parent(self, tracer):
        parent = tracer.start_trace("parent_op")
        child = tracer.start_span("child_op")
        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id

    def test_end_span(self, tracer):
        tracer.start_trace("op")
        tracer.end_span("ok", {"key": "value"})
        spans = tracer.get_spans()
        assert len(spans) == 1
        assert spans[0]["status"] == "ok"
        assert spans[0]["duration_ms"] >= 0

    def test_inject_headers(self, tracer):
        tracer.start_trace("op")
        headers = tracer.inject_headers({})
        assert "X-Trace-ID" in headers
        assert "X-Span-ID" in headers

    def test_extract_from_headers(self, tracer):
        headers = {"X-Trace-ID": "trace-1", "X-Span-ID": "span-1"}
        ctx = tracer.extract_from_headers(headers)
        assert ctx is not None
        assert ctx.trace_id == "trace-1"
        assert ctx.span_id == "span-1"

    def test_add_span_event(self, tracer):
        tracer.start_trace("op")
        tracer.add_span_event("custom_event", {"detail": "test"})
        spans = tracer.get_spans()
        assert len(spans[0].get("events", [])) == 1

    def test_get_current_span(self, tracer):
        tracer.start_trace("op")
        current = tracer.get_current_span()
        assert current is not None

    def test_clear(self, tracer):
        tracer.start_trace("op")
        tracer.clear()
        assert len(tracer.get_spans()) == 0

    def test_tracing_disabled_no_spans(self, tracer):
        tracer._enabled = False
        tracer.start_trace("op")
        assert len(tracer.get_spans()) == 0


@pytest.mark.asyncio
async def test_trace_decorator():
    @trace("custom_operation")
    async def sample_func():
        return "done"

    result = await sample_func()
    assert result == "done"


@pytest.mark.asyncio
async def test_trace_decorator_error():
    @trace()
    async def failing_func():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        await failing_func()
