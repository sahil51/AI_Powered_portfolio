from production.checklist import ProductionChecklistBuilder
from production.models import ChecklistItem, ProductionChecklist, ValidationStatus


class TestProductionChecklistBuilder:
    def test_build_returns_production_checklist(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        assert isinstance(result, ProductionChecklist)

    def test_build_has_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        assert len(result.items) > 0
        assert result.total == len(result.items)

    def test_build_items_are_checklist_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        for item in result.items:
            assert isinstance(item, ChecklistItem)

    def test_build_all_items_have_required_fields(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        for item in result.items:
            assert item.category
            assert item.name
            assert item.description

    def test_build_items_default_to_pending(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        for item in result.items:
            assert item.status == ValidationStatus.PENDING

    def test_build_has_configuration_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        config_items = [i for i in result.items if i.category == "Configuration"]
        assert len(config_items) > 0
        names = {i.name for i in config_items}
        assert "Database URL" in names
        assert "Redis URL" in names
        assert "JWT Secret" in names
        assert "AI Providers" in names
        assert "Embedding Provider" in names

    def test_build_has_security_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        security_items = [i for i in result.items if i.category == "Security"]
        assert len(security_items) > 0
        names = {i.name for i in security_items}
        assert "Rate Limiting" in names
        assert "JWT Validation" in names
        assert "CORS" in names
        assert "Security Headers" in names

    def test_build_has_database_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        db_items = [i for i in result.items if i.category == "Database"]
        assert len(db_items) > 0

    def test_build_has_release_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        release_items = [i for i in result.items if i.category == "Release"]
        assert len(release_items) > 0
        names = {i.name for i in release_items}
        assert "Version Tag" in names
        assert "Tests Passing" in names
        assert "Lint Passing" in names
        assert "Type Checks Passing" in names

    def test_build_has_required_and_optional(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        required = [i for i in result.items if i.required]
        optional = [i for i in result.items if not i.required]
        assert len(required) > 0
        assert len(optional) > 0
        optional_names = {i.name for i in optional}
        assert "Monitoring" in optional_names
        assert "Fallback Providers" in optional_names
        assert "Changelog" in optional_names

    def test_build_has_disaster_recovery_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        dr_items = [i for i in result.items if i.category == "Disaster Recovery"]
        assert len(dr_items) > 0
        names = {i.name for i in dr_items}
        assert "RTO" in names
        assert "RPO" in names
        assert "Graceful Degradation" in names

    def test_build_has_backup_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        backup_items = [i for i in result.items if i.category == "Backup"]
        assert len(backup_items) > 0

    def test_build_has_monitoring_items(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        monitoring_items = [i for i in result.items if i.category == "Monitoring"]
        assert len(monitoring_items) > 0

    def test_build_categories_are_distinct(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        categories = {i.category for i in result.items}
        assert "Configuration" in categories
        assert "Secrets" in categories
        assert "Database" in categories
        assert "Redis" in categories
        assert "Security" in categories
        assert "Release" in categories

    def test_build_item_integrity(self):
        builder = ProductionChecklistBuilder()
        result = builder.build()
        for item in result.items:
            assert isinstance(item.required, bool)
            assert item.category
            assert item.name
