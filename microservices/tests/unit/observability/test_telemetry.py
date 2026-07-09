
from observability.telemetry_configuration import SamplingStrategy, TelemetryConfiguration


class TestTelemetryConfiguration:
    def test_default_values(self):
        config = TelemetryConfiguration()
        assert config.tracing_enabled is True
        assert config.metrics_enabled is True
        assert config.logging_enabled is True

    def test_sampling_strategy_default(self):
        config = TelemetryConfiguration()
        assert config.sampling_strategy == SamplingStrategy.ALWAYS

    def test_sampling_rate(self):
        config = TelemetryConfiguration(sampling_rate=0.5, sampling_strategy=SamplingStrategy.PROBABILISTIC)
        assert config.sampling_rate == 0.5

    def test_trace_batch_size(self):
        config = TelemetryConfiguration(max_trace_batch_size=200)
        assert config.max_trace_batch_size == 200

    def test_export_interval(self):
        config = TelemetryConfiguration(export_interval_seconds=30)
        assert config.export_interval_seconds == 30

    def test_prometheus_config(self):
        config = TelemetryConfiguration(prometheus_enabled=True, prometheus_port=9090)
        assert config.prometheus_port == 9090

    def test_sentry_config(self):
        config = TelemetryConfiguration(sentry_enabled=True, sentry_dsn="https://key@sentry.io/project")
        assert config.sentry_dsn == "https://key@sentry.io/project"

    def test_to_dict(self):
        config = TelemetryConfiguration()
        d = config.to_dict()
        assert "service_name" in d
        assert "tracing_enabled" in d

    def test_baggage_keys(self):
        config = TelemetryConfiguration(baggage_keys=["user_id", "tenant_id", "conversation_id"])
        assert len(config.baggage_keys) == 3

    def test_custom_attributes(self):
        config = TelemetryConfiguration(attributes={"deployment": "staging"})
        assert config.attributes["deployment"] == "staging"
