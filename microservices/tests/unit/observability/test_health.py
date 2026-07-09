import pytest

from observability.health_aggregator import HealthAggregator, HealthComponent, HealthStatus, SystemHealth


class TestHealthAggregator:
    @pytest.fixture
    def aggregator(self):
        return HealthAggregator()

    def test_initialization(self, aggregator):
        assert aggregator.liveness()["status"] == "alive"

    def test_register_component(self, aggregator):
        aggregator.register_component("test_service")
        assert "test_service" in aggregator._components

    def test_record_health_healthy(self, aggregator):
        aggregator.record_health("database", HealthStatus.HEALTHY, latency_ms=5.0)
        assert aggregator._components["database"].status == HealthStatus.HEALTHY
        assert aggregator._components["database"].latency_ms == 5.0

    def test_record_health_unhealthy(self, aggregator):
        aggregator.record_health("redis", HealthStatus.UNHEALTHY, error="Connection refused")
        assert aggregator._components["redis"].status == HealthStatus.UNHEALTHY

    def test_liveness(self, aggregator):
        assert aggregator.liveness() == {"status": "alive"}

    def test_readiness_all_healthy(self, aggregator):
        aggregator.record_health("db", HealthStatus.HEALTHY)
        aggregator.record_health("redis", HealthStatus.HEALTHY)
        assert aggregator.readiness()["status"] == "ready"

    def test_readiness_unhealthy(self, aggregator):
        aggregator.record_health("db", HealthStatus.UNHEALTHY, error="down")
        result = aggregator.readiness()
        assert result["status"] == "not_ready"
        assert "db" in result["failing_components"]

    def test_startup(self, aggregator):
        result = aggregator.startup()
        assert result["status"] == "started"
        assert result["uptime_seconds"] >= 0

    def test_check_all_aggregates(self, aggregator):
        result = aggregator.liveness()
        assert result["status"] == "alive"


class TestHealthComponent:
    def test_component_defaults(self):
        comp = HealthComponent(name="test")
        assert comp.status == HealthStatus.HEALTHY
        assert comp.latency_ms == 0.0
        assert comp.error == ""

    def test_component_with_values(self):
        comp = HealthComponent(
            name="db",
            status=HealthStatus.DEGRADED,
            latency_ms=100.0,
            details={"response_time": "slow"},
            error="timeout",
        )
        assert comp.name == "db"
        assert comp.status == HealthStatus.DEGRADED
        assert comp.latency_ms == 100.0


class TestSystemHealth:
    def test_system_health_defaults(self):
        system = SystemHealth()
        assert system.status == HealthStatus.HEALTHY
        assert system.uptime_seconds >= 0
