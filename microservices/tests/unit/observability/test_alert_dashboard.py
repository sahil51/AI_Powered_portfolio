import pytest

from observability.alert_configuration import AlertConfiguration, AlertRule, AlertSeverity
from observability.dashboard_configuration import (
    DashboardConfiguration,
    DashboardPanel,
    DashboardPanelType,
)


class TestAlertConfiguration:
    @pytest.fixture
    def config(self):
        c = AlertConfiguration()
        c.load_defaults()
        return c

    def test_add_rule(self, config):
        rule = AlertRule(name="custom", description="Custom alert", severity=AlertSeverity.INFO, condition="test > 0")
        config.add_rule(rule)
        assert config.get_rule("custom") is rule

    def test_remove_rule(self, config):
        config.add_rule(AlertRule(name="temp", description="Temp", severity=AlertSeverity.INFO, condition="x"))
        config.remove_rule("temp")
        assert config.get_rule("temp") is None

    def test_get_rules(self, config):
        rules = config.get_rules()
        assert len(rules) >= 5
        assert any(r.name == "database_down" for r in rules)

    def test_load_defaults(self):
        config = AlertConfiguration()
        config.load_defaults()
        rules = config.get_rules()
        assert len(rules) == 9

    def test_clear(self, config):
        config.clear()
        assert len(config.get_rules()) == 0

    def test_alert_rule_to_dict(self):
        rule = AlertRule(name="test", description="desc", severity=AlertSeverity.CRITICAL, condition="x > 5", threshold=5.0)
        d = rule.to_dict()
        assert d["name"] == "test"
        assert d["severity"] == "critical"

    def test_to_dict(self, config):
        d = config.to_dict()
        assert isinstance(d, list)
        assert len(d) >= 5

    def test_get_default_rules(self):
        config = AlertConfiguration()
        rules = config.get_default_rules()
        assert len(rules) == 9

    def test_get_rule_nonexistent(self, config):
        assert config.get_rule("nonexistent") is None


class TestDashboardConfiguration:
    @pytest.fixture
    def config(self):
        c = DashboardConfiguration()
        c.load_defaults()
        return c

    def test_add_panel(self, config):
        panel = DashboardPanel(title="Test Panel", query="test_metric")
        config.add_panel(panel)
        assert len(config.get_panels()) >= 12

    def test_load_defaults(self):
        config = DashboardConfiguration()
        config.load_defaults()
        panels = config.get_panels()
        assert len(panels) == 12

    def test_clear(self, config):
        config.clear()
        assert len(config.get_panels()) == 0

    def test_panel_to_dict(self):
        panel = DashboardPanel(title="My Panel", description="desc", panel_type=DashboardPanelType.SINGLE_STAT, query="my_metric", unit="count", span=3)
        d = panel.to_dict()
        assert d["title"] == "My Panel"
        assert d["type"] == "single_stat"

    def test_to_dict(self, config):
        d = config.to_dict()
        assert isinstance(d, list)
        assert len(d) >= 12

    def test_export_grafana_json(self, config):
        grafana = config.export_grafana_json()
        assert "title" in grafana
        assert "panels" in grafana
        assert len(grafana["panels"]) >= 12

    def test_get_default_panels(self):
        config = DashboardConfiguration()
        panels = config.get_default_panels()
        assert len(panels) == 12
