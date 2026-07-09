from production.models import (
    ArchitectureValidationResult,
    ChecklistItem,
    ConfigurationValidationResult,
    ProductionChecklist,
    ReadinessReport,
    ValidationItem,
    ValidationSeverity,
    ValidationStatus,
)
from production.reporting import ReportRenderer


class TestReportRendererChecklist:
    def test_render_checklist_empty(self):
        renderer = ReportRenderer()
        cl = ProductionChecklist()
        result = renderer.render_checklist_markdown(cl)
        assert "# Production Readiness Checklist" in result
        assert "## Summary" in result
        assert "Pass Rate:" in result
        assert "Ready:" in result

    def test_render_checklist_includes_items(self):
        renderer = ReportRenderer()
        items = [
            ChecklistItem(category="Config", name="Test Item", description="A test"),
        ]
        cl = ProductionChecklist(items=items, total=1)
        result = renderer.render_checklist_markdown(cl)
        assert "Test Item" in result
        assert "Config" in result
        assert "⏳" in result

    def test_render_checklist_shows_status_icons(self):
        renderer = ReportRenderer()
        items = [
            ChecklistItem(category="Cat", name="Passed", description="d", status=ValidationStatus.PASSED),
            ChecklistItem(category="Cat", name="Failed", description="d", status=ValidationStatus.FAILED),
            ChecklistItem(category="Cat", name="Warning", description="d", status=ValidationStatus.WARNING),
            ChecklistItem(category="Cat", name="Skipped", description="d", status=ValidationStatus.SKIPPED),
            ChecklistItem(category="Cat", name="Pending", description="d", status=ValidationStatus.PENDING),
        ]
        cl = ProductionChecklist(items=items, total=5)
        result = renderer.render_checklist_markdown(cl)
        assert "✅" in result
        assert "❌" in result
        assert "⚠️" in result
        assert "⏭️" in result
        assert "⏳" in result

    def test_render_checklist_summary_values(self):
        renderer = ReportRenderer()
        items = [
            ChecklistItem(category="A", name="x", description="d", status=ValidationStatus.PASSED),
            ChecklistItem(category="A", name="y", description="d", status=ValidationStatus.FAILED),
        ]
        cl = ProductionChecklist(items=items, total=2, passed=1, failed=1)
        result = renderer.render_checklist_markdown(cl)
        assert "**Total:** 2" in result
        assert "**Passed:** 1" in result
        assert "**Failed:** 1" in result
        assert "**Pass Rate:** 50.0%" in result

    def test_render_checklist_shows_ready_when_no_failures(self):
        renderer = ReportRenderer()
        cl = ProductionChecklist(failed=0)
        result = renderer.render_checklist_markdown(cl)
        assert "✅ YES" in result

    def test_render_checklist_shows_not_ready_when_failures(self):
        renderer = ReportRenderer()
        cl = ProductionChecklist(failed=1)
        result = renderer.render_checklist_markdown(cl)
        assert "❌ NO" in result

    def test_render_checklist_required_column(self):
        renderer = ReportRenderer()
        items = [
            ChecklistItem(category="A", name="Req", description="d", required=True),
            ChecklistItem(category="A", name="Opt", description="d", required=False),
        ]
        cl = ProductionChecklist(items=items, total=2)
        result = renderer.render_checklist_markdown(cl)
        assert "Yes" in result
        assert "No" in result


class TestReportRendererReadiness:
    def test_render_readiness_empty_report(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="test-1")
        result = renderer.render_readiness_report(report)
        assert "# AI Platform Readiness Report" in result
        assert "test-1" in result
        assert "**Overall Ready:**" in result
        assert "**NO-GO**" in result

    def test_render_readiness_shows_verdict_ready(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", overall_ready=True)
        result = renderer.render_readiness_report(report)
        assert "**GO FOR PRODUCTION** 🚀" in result

    def test_render_readiness_shows_verdict_not_ready(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", overall_ready=False)
        result = renderer.render_readiness_report(report)
        assert "**NO-GO**" in result

    def test_render_readiness_includes_sections(self):
        renderer = ReportRenderer()
        arch = ArchitectureValidationResult(validator_name="A", passed=True)
        config = ConfigurationValidationResult(validator_name="C", passed=False)
        report = ReadinessReport(report_id="r1", architecture=arch, configuration=config)
        result = renderer.render_readiness_report(report)
        assert "## Architecture Validation" in result
        assert "## Configuration Validation" in result
        assert "✅ PASSED" in result
        assert "❌ FAILED" in result

    def test_render_readiness_includes_section_items(self):
        renderer = ReportRenderer()
        items = [
            ValidationItem(name="check1", status=ValidationStatus.PASSED, severity=ValidationSeverity.HIGH, message="ok"),
            ValidationItem(name="check2", status=ValidationStatus.FAILED, severity=ValidationSeverity.CRITICAL, message="fail"),
        ]
        arch = ArchitectureValidationResult(validator_name="A", passed=True, items=items)
        report = ReadinessReport(report_id="r1", architecture=arch)
        result = renderer.render_readiness_report(report)
        assert "check1" in result
        assert "check2" in result
        assert "critical" in result
        assert "high" in result

    def test_render_readiness_skips_none_sections(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", architecture=None, deployment=None)
        result = renderer.render_readiness_report(report)
        assert "## Architecture Validation" not in result
        assert "## Deployment Readiness" not in result

    def test_render_readiness_includes_recommendations(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", recommendations=["Fix things", "Improve stuff"])
        result = renderer.render_readiness_report(report)
        assert "## Recommendations" in result
        assert "1. Fix things" in result
        assert "2. Improve stuff" in result

    def test_render_readiness_no_recommendations(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1")
        result = renderer.render_readiness_report(report)
        assert "## Recommendations" not in result

    def test_render_readiness_includes_checklist_summary(self):
        renderer = ReportRenderer()
        cl = ProductionChecklist(passed=3, failed=1, total=4)
        report = ReadinessReport(report_id="r1", checklist=cl)
        result = renderer.render_readiness_report(report)
        assert "## Production Checklist Summary" in result
        assert "Pass Rate:" in result
        assert "Passed:" in result
        assert "Failed:" in result

    def test_render_readiness_checklist_summary_pass_rate(self):
        renderer = ReportRenderer()
        cl = ProductionChecklist(passed=3, failed=1, total=4)
        report = ReadinessReport(report_id="r1", checklist=cl)
        result = renderer.render_readiness_report(report)
        assert "75.0%" in result

    def test_render_readiness_no_checklist_summary(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", checklist=None)
        result = renderer.render_readiness_report(report)
        assert "## Production Checklist Summary" not in result

    def test_render_readiness_includes_summary_text(self):
        renderer = ReportRenderer()
        report = ReadinessReport(report_id="r1", summary="All good")
        result = renderer.render_readiness_report(report)
        assert "All good" in result

    def test_render_readiness_empty_section_items_does_not_render_table(self):
        renderer = ReportRenderer()
        arch = ArchitectureValidationResult(validator_name="A", passed=True, items=[])
        report = ReadinessReport(report_id="r1", architecture=arch)
        result = renderer.render_readiness_report(report)
        lines = result.splitlines()
        table_header = [l for l in lines if "Check | Status | Severity | Message" in l]
        assert len(table_header) == 0


class TestReportRendererStatusIcons:
    def test_status_icon_passed(self):
        renderer = ReportRenderer()
        assert renderer._status_icon(ValidationStatus.PASSED) == "✅"

    def test_status_icon_failed(self):
        renderer = ReportRenderer()
        assert renderer._status_icon(ValidationStatus.FAILED) == "❌"

    def test_status_icon_warning(self):
        renderer = ReportRenderer()
        assert renderer._status_icon(ValidationStatus.WARNING) == "⚠️"

    def test_status_icon_skipped(self):
        renderer = ReportRenderer()
        assert renderer._status_icon(ValidationStatus.SKIPPED) == "⏭️"

    def test_status_icon_pending(self):
        renderer = ReportRenderer()
        assert renderer._status_icon(ValidationStatus.PENDING) == "⏳"

    def test_status_icon_unknown(self):
        renderer = ReportRenderer()
        assert renderer._status_icon("unknown") == "❓"
