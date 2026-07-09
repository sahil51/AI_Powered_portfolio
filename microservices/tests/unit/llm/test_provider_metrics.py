from application.ai.metrics import ModelMetrics, ProviderMetrics, ProviderMetricsCollector
from application.ai.models import Usage


class TestProviderMetrics:
    def test_defaults(self):
        metrics = ProviderMetrics(provider="test")
        assert metrics.provider == "test"
        assert metrics.total_requests == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.failure_rate == 0.0

    def test_success_rate(self):
        metrics = ProviderMetrics(provider="test", total_requests=10, successful_requests=8, failed_requests=2)
        assert metrics.success_rate == 0.8
        assert metrics.failure_rate == 0.2

    def test_merge(self):
        m1 = ProviderMetrics(provider="test", total_requests=5, successful_requests=4, total_cost=0.5)
        m2 = ProviderMetrics(provider="test", total_requests=3, successful_requests=3, total_cost=0.3)
        m1.merge(m2)
        assert m1.total_requests == 8
        assert m1.successful_requests == 7
        assert m1.total_cost == 0.8


class TestModelMetrics:
    def test_defaults(self):
        metrics = ModelMetrics(model="test-model")
        assert metrics.model == "test-model"
        assert metrics.requests == 0
        assert metrics.avg_latency_ms == 0.0

    def test_merge(self):
        m1 = ModelMetrics(model="m", requests=5, tokens=100, cost=0.5, latency_ms=50.0)
        m2 = ModelMetrics(model="m", requests=3, tokens=60, cost=0.3, latency_ms=30.0)
        m1.merge(m2)
        assert m1.requests == 8
        assert m1.tokens == 160
        assert m1.cost == 0.8


class TestProviderMetricsCollector:
    def setup_method(self):
        self.collector = ProviderMetricsCollector()

    def test_record_request_success(self):
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost=0.01)
        self.collector.record_request("litellm", "gemini/gemini-2.0-flash", True, 100.0, usage)
        metrics = self.collector.get_metrics("litellm")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.total_tokens == 30
        assert metrics.total_cost == 0.01
        assert metrics.total_latency_ms == 100.0
        assert "gemini/gemini-2.0-flash" in metrics.model_usage

    def test_record_request_failure(self):
        self.collector.record_request("litellm", "model", False, 50.0)
        metrics = self.collector.get_metrics("litellm")
        assert metrics.total_requests == 1
        assert metrics.failed_requests == 1
        assert "model" in metrics.model_usage
        assert metrics.model_usage["model"].errors == 1

    def test_record_retry(self):
        self.collector.record_retry("litellm")
        metrics = self.collector.get_metrics("litellm")
        assert metrics.retry_count == 1

    def test_record_fallback(self):
        self.collector.record_fallback("litellm")
        metrics = self.collector.get_metrics("litellm")
        assert metrics.fallback_count == 1

    def test_record_circuit_breaker_trip(self):
        self.collector.record_circuit_breaker_trip("litellm")
        metrics = self.collector.get_metrics("litellm")
        assert metrics.circuit_breaker_trips == 1

    def test_get_all_metrics(self):
        self.collector.record_request("p1", "m1", True, 10.0)
        self.collector.record_request("p2", "m2", True, 20.0)
        all_metrics = self.collector.get_metrics()
        assert len(all_metrics) == 2

    def test_reset(self):
        self.collector.record_request("litellm", "model", True, 10.0)
        self.collector.reset("litellm")
        metrics = self.collector.get_metrics("litellm")
        assert metrics.total_requests == 0

    def test_reset_all(self):
        self.collector.record_request("p1", "m1", True, 10.0)
        self.collector.reset()
        assert len(self.collector.get_metrics()) == 0
