import pytest

from observability.health_aggregator import HealthStatus
from observability.manager import ObservabilityManager


class TestObservabilityIntegration:
    @pytest.fixture
    async def manager(self):
        mgr = ObservabilityManager()
        await mgr.initialize()
        yield mgr
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_full_observability_pipeline(self, manager):
        manager.metrics_collector.record_http_request("GET", "/test", 200, 5.0)
        manager.metrics_collector.record_conversation("create", "success", 100.0)
        manager.metrics_collector.record_provider_call("gemini", "chat", "success", 500.0)
        manager.metrics_collector.record_token_usage("gemini", "output", 150)
        manager.metrics_collector.record_error("database", "timeout")
        manager.metrics_collector.record_retry("embedding")

        trace_ctx = manager.tracing_manager.start_trace("integration_test")
        child_span = manager.tracing_manager.start_span("sub_op")
        manager.tracing_manager.add_span_event("milestone", {"step": "1"})
        manager.tracing_manager.end_span("ok")
        manager.tracing_manager.end_span("ok")

        system = await manager.health_aggregator.check_all()
        assert system.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)

        metrics_data = manager.metrics_collector.get_metrics_data()
        assert metrics_data.http_requests_total >= 1
        assert metrics_data.conversation_total >= 1

        spans = manager.tracing_manager.get_spans()
        assert len(spans) >= 2

    @pytest.mark.asyncio
    async def test_health_aggregator_with_multiple_checks(self, manager):
        aggregator = manager.health_aggregator
        aggregator.record_health("component-a", HealthStatus.HEALTHY, latency_ms=5.0)
        aggregator.record_health("component-b", HealthStatus.DEGRADED, latency_ms=200.0, details={"slow": True})
        aggregator.record_health("component-c", HealthStatus.UNHEALTHY, error="timeout")

        system = await aggregator.check_all()
        assert system.status == HealthStatus.UNHEALTHY

        readiness = aggregator.readiness()
        assert "component-c" in readiness.get("failing_components", [])

    def test_metrics_registry_prometheus_output(self, manager):
        output = manager.metrics_registry.export_prometheus()
        assert isinstance(output, bytes)
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_observability_report(self, manager):
        health = await manager.health_report()
        assert "status" in health
        assert "components" in health

        metrics = manager.metrics_report()
        assert isinstance(metrics, dict)

        stats = manager.statistics_report()
        assert isinstance(stats, dict)

    def test_alert_configuration_defaults(self, manager):
        rules = manager.alert_configuration.get_rules()
        assert len(rules) == 9

    def test_dashboard_configuration_defaults(self, manager):
        panels = manager.dashboard_configuration.get_panels()
        assert len(panels) == 12

    def test_telemetry_configuration(self, manager):
        config = manager.telemetry_configuration
        assert config.service_name is not None
        assert config.environment is not None
