import pytest

from observability.metrics_collector import MetricsCollector
from observability.metrics_registry import MetricsRegistry
from observability.statistics_collector import StatisticsCollector


class TestMetricsRegistry:
    @pytest.fixture
    def registry(self):
        return MetricsRegistry()

    def test_initialization(self, registry):
        assert registry.http_requests is not None
        assert registry.conversation_operations is not None
        assert registry.memory_operations is not None

    def test_prometheus_export(self, registry):
        data = registry.export_prometheus()
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_latest_metrics(self, registry):
        data = registry.get_latest_metrics()
        assert isinstance(data, bytes)

    def test_snapshot(self, registry):
        snap = registry.snapshot()
        assert hasattr(snap, "http_requests_total")


class TestMetricsCollector:
    @pytest.fixture
    def collector(self):
        return MetricsCollector(MetricsRegistry())

    def test_record_http_request(self, collector):
        collector.record_http_request("GET", "/health", 200, 10.0)
        data = collector.get_metrics_data()
        assert data.http_requests_total == 1
        assert data.http_latency_ms_total == 10.0

    def test_record_http_error(self, collector):
        collector.record_http_request("POST", "/api", 500, 5.0)
        data = collector.get_metrics_data()
        assert data.http_errors_total == 1

    def test_record_conversation(self, collector):
        collector.record_conversation("create", "success", 15.0)
        data = collector.get_metrics_data()
        assert data.conversation_total == 1

    def test_record_memory(self, collector):
        collector.record_memory("read", "success", 5.0)
        data = collector.get_metrics_data()
        assert data.memory_operations_total == 1

    def test_record_knowledge(self, collector):
        collector.record_knowledge("search", "success", 20.0)
        data = collector.get_metrics_data()
        assert data.knowledge_operations_total == 1

    def test_record_retrieval(self, collector):
        collector.record_retrieval("hybrid_search", "success", 30.0)
        data = collector.get_metrics_data()
        assert data.retrieval_operations_total == 1

    def test_record_embedding(self, collector):
        collector.record_embedding("generate", "success", 100.0)
        data = collector.get_metrics_data()
        assert data.embedding_operations_total == 1

    def test_record_provider_call(self, collector):
        collector.record_provider_call("gemini", "chat", "success", 200.0)
        data = collector.get_metrics_data()
        assert data.provider_calls_total == 1

    def test_record_error(self, collector):
        collector.record_error("database", "connection_error")
        data = collector.get_metrics_data()
        assert data.errors_total == 1

    def test_record_retry(self, collector):
        collector.record_retry("embedding")
        data = collector.get_metrics_data()
        assert data.retries_total == 1

    def test_token_usage(self, collector):
        collector.record_token_usage("gemini", "input", 500)
        data = collector.get_metrics_data()
        assert data.tokens_used_total == 500

    def test_cost(self, collector):
        collector.record_cost("gemini", "input", 0.0025)
        data = collector.get_metrics_data()
        assert data.cost_total == 0.0025

    def test_workflow_metrics(self, collector):
        collector.record_workflow("execute", "success", 50.0)
        data = collector.get_metrics_data()
        assert data.workflow_operations_total == 1

    def test_redis_metrics(self, collector):
        collector.record_redis("get", "success", 1.0)
        data = collector.get_metrics_data()
        assert data.redis_operations_total == 1

    def test_postgresql_metrics(self, collector):
        collector.record_postgresql("query", "success", 5.0)
        data = collector.get_metrics_data()
        assert data.postgresql_operations_total == 1

    def test_celery_metrics(self, collector):
        collector.record_celery_task("default", "process", "success", 1000.0)
        data = collector.get_metrics_data()
        assert data.celery_tasks_total == 1

    def test_n8n_metrics(self, collector):
        collector.record_n8n("webhook", "success", 300.0)
        data = collector.get_metrics_data()
        assert data.n8n_operations_total == 1

    def test_gauge_metrics(self, collector):
        collector.set_active_workflows(5)
        collector.set_queue_depth("celery", 10)
        collector.set_active_connections("websocket", 3)
        data = collector.get_metrics_data()
        assert data is not None

    def test_reset(self, collector):
        collector.record_http_request("GET", "/", 200, 1.0)
        collector.reset()
        data = collector.get_metrics_data()
        assert data.http_requests_total == 0


class TestStatisticsCollector:
    @pytest.fixture
    def stats(self):
        return StatisticsCollector()

    def test_latency_recording(self, stats):
        stats.record_latency("search", 10.0)
        stats.record_latency("search", 20.0)
        stats.record_latency("search", 30.0)
        result = stats.get_latency_stats("search")
        assert result["count"] == 3
        assert result["min"] == 10.0
        assert result["max"] == 30.0
        assert result["avg"] == 20.0

    def test_counter(self, stats):
        stats.increment("requests")
        stats.increment("requests", 5)
        assert stats.get_counter("requests") == 6

    def test_gauge(self, stats):
        stats.set_gauge("connections", 42.0)
        assert stats.get_gauge("connections") == 42.0

    def test_snapshot(self, stats):
        stats.increment("ops", 10)
        stats.record_latency("latency", 5.0)
        snap = stats.snapshot()
        assert snap["ops"] == 10
        assert "latency" in snap

    def test_reset(self, stats):
        stats.increment("ops", 100)
        stats.reset()
        assert stats.get_counter("ops") == 0
