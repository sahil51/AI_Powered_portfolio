import pytest

from security.exceptions import RateLimitExceededError
from security.models import RateLimitScope
from security.rate_limit_manager import RateLimitManager, RateLimitRule


class TestRateLimitManager:
    @pytest.fixture
    def manager(self):
        mgr = RateLimitManager()
        mgr.add_rule(RateLimitRule(
            name="test",
            scope=RateLimitScope.USER,
            max_requests=3,
            window_seconds=60,
            burst_multiplier=2,
        ))
        return mgr

    def test_add_rule(self, manager):
        assert len(manager.get_rules()) == 1

    def test_remove_rule(self, manager):
        manager.remove_rule("test")
        assert len(manager.get_rules()) == 0

    def test_rate_limit_allowed(self, manager):
        for _ in range(3):
            result = manager.check_rate_limit(RateLimitScope.USER, "user-1")
            assert result["allowed"]

    def test_rate_limit_exceeded(self, manager):
        for _ in range(6):
            manager.check_rate_limit(RateLimitScope.USER, "user-2")
        result = manager.check_rate_limit(RateLimitScope.USER, "user-2")
        assert not result["allowed"]

    def test_validate_allowed(self, manager):
        manager.validate(RateLimitScope.USER, "user-3")

    def test_validate_exceeded(self, manager):
        for _ in range(7):
            try:
                manager.validate(RateLimitScope.USER, "user-4")
            except RateLimitExceededError:
                pass
        with pytest.raises(RateLimitExceededError):
            manager.validate(RateLimitScope.USER, "user-4")

    def test_different_identifiers(self, manager):
        for _ in range(3):
            manager.check_rate_limit(RateLimitScope.USER, "user-a")
        for _ in range(3):
            result = manager.check_rate_limit(RateLimitScope.USER, "user-b")
            assert result["allowed"]

    def test_anonymous_scope(self):
        mgr = RateLimitManager()
        mgr.add_rule(RateLimitRule(
            name="anon",
            scope=RateLimitScope.ANONYMOUS,
            max_requests=1,
            window_seconds=60,
        ))
        result1 = mgr.check_rate_limit(RateLimitScope.ANONYMOUS, "ip-1")
        assert result1["allowed"]
        result2 = mgr.check_rate_limit(RateLimitScope.ANONYMOUS, "ip-1")
        assert result2["allowed"]
        result3 = mgr.check_rate_limit(RateLimitScope.ANONYMOUS, "ip-1")
        assert result3["allowed"] is False

    def test_get_limits_for(self, manager):
        limits = manager.get_limits_for("user-test")
        assert len(limits) == 1
        assert limits[0]["scope"] == "user"

    def test_load_default_rules(self):
        mgr = RateLimitManager()
        mgr.load_default_rules()
        assert len(mgr.get_rules()) == 5

    def test_reset(self, manager):
        manager.check_rate_limit(RateLimitScope.USER, "user-r")
        manager.reset()
        result = manager.check_rate_limit(RateLimitScope.USER, "user-r")
        assert result["allowed"]
