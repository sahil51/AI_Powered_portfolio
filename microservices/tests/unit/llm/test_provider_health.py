
from application.ai.health import ProviderHealth, ProviderHealthChecker, ProviderHealthStatus
from tests.unit.llm.test_provider_registry import StubProvider


class TestProviderHealth:
    def test_health_status_enum(self):
        assert ProviderHealthStatus.HEALTHY.value == "healthy"
        assert ProviderHealthStatus.DEGRADED.value == "degraded"
        assert ProviderHealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_defaults(self):
        health = ProviderHealth(provider="test")
        assert health.provider == "test"
        assert health.status == ProviderHealthStatus.UNKNOWN
        assert not health.is_healthy

    def test_health_is_healthy(self):
        health = ProviderHealth(provider="test", status=ProviderHealthStatus.HEALTHY)
        assert health.is_healthy


class TestProviderHealthChecker:
    async def test_check_healthy(self):
        checker = ProviderHealthChecker()
        provider = StubProvider()
        health = await checker.check(provider)
        assert health.status == ProviderHealthStatus.HEALTHY
        assert health.latency_ms >= 0

    async def test_check_unhealthy(self):
        class UnhealthyProvider(StubProvider):
            async def health_check(self):
                return False

        checker = ProviderHealthChecker()
        provider = UnhealthyProvider()
        health = await checker.check(provider)
        assert health.status == ProviderHealthStatus.DEGRADED

    async def test_check_exception(self):
        class BrokenProvider(StubProvider):
            async def health_check(self):
                raise RuntimeError("broken")

        checker = ProviderHealthChecker()
        provider = BrokenProvider()
        health = await checker.check(provider)
        assert health.status == ProviderHealthStatus.UNHEALTHY
        assert health.error is not None

    async def test_get_cached(self):
        checker = ProviderHealthChecker()
        provider = StubProvider(name="cached")
        await checker.check(provider)
        cached = checker.get_cached("cached")
        assert cached is not None
        assert cached.provider == "cached"

    async def test_clear_cache(self):
        checker = ProviderHealthChecker()
        provider = StubProvider(name="clearable")
        await checker.check(provider)
        checker.clear_cache()
        assert checker.get_cached("clearable") is None

    async def test_check_all(self):
        checker = ProviderHealthChecker()
        healthy = StubProvider("healthy")

        class UnhealthyProvider(StubProvider):
            def __init__(self):
                super().__init__("unhealthy")

            async def health_check(self):
                return False

        unhealthy = UnhealthyProvider()
        results = await checker.check_all([healthy, unhealthy])
        assert len(results) == 2
        assert results[0].status == ProviderHealthStatus.HEALTHY
        assert results[1].status == ProviderHealthStatus.DEGRADED
