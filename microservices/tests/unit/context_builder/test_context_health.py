from application.context_builder.health import ContextHealth, ContextHealthStatus


class TestContextHealth:
    def test_default_healthy(self):
        health = ContextHealth()
        assert health.status == ContextHealthStatus.HEALTHY

    def test_unhealthy(self):
        health = ContextHealth(status=ContextHealthStatus.UNHEALTHY, errors=["Something failed"])
        assert health.status == ContextHealthStatus.UNHEALTHY
        assert len(health.errors) == 1
