from __future__ import annotations

from production.models import (
    ProductionChecklist,
    ReadinessReport,
    ValidationStatus,
)


class ReportRenderer:
    def render_checklist_markdown(self, checklist: ProductionChecklist) -> str:
        lines = ["# Production Readiness Checklist", ""]
        categories: dict[str, list] = {}
        for item in checklist.items:
            categories.setdefault(item.category, []).append(item)
        for category, items in categories.items():
            lines.append(f"## {category}")
            lines.append("")
            lines.append("| Item | Required | Status | Details |")
            lines.append("|------|----------|--------|---------|")
            for item in items:
                status_icon = self._status_icon(item.status)
                required = "Yes" if item.required else "No"
                lines.append(f"| {item.name} | {required} | {status_icon} | {item.details} |")
            lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total:** {checklist.total}")
        lines.append(f"- **Passed:** {checklist.passed}")
        lines.append(f"- **Failed:** {checklist.failed}")
        lines.append(f"- **Warnings:** {checklist.warning}")
        lines.append(f"- **Skipped:** {checklist.skipped}")
        lines.append(f"- **Pass Rate:** {checklist.pass_rate:.1%}")
        lines.append(f"- **Ready:** {'✅ YES' if checklist.ready else '❌ NO'}")
        return "\n".join(lines)

    def render_readiness_report(self, report: ReadinessReport) -> str:
        lines = [
            "# AI Platform Readiness Report",
            "",
            f"**Report ID:** {report.report_id}",
            f"**Timestamp:** {report.timestamp}",
            f"**Overall Ready:** {'✅ YES' if report.overall_ready else '❌ NO'}",
            "",
            "## Executive Summary",
            "",
            f"{report.summary}",
            "",
        ]
        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        sections = [
            ("Architecture Validation", report.architecture),
            ("Deployment Readiness", report.deployment),
            ("Backup Validation", report.backup),
            ("Recovery Validation", report.recovery),
            ("Configuration Validation", report.configuration),
            ("Environment Validation", report.environment),
            ("Infrastructure Validation", report.infrastructure),
            ("Dependency Validation", report.dependencies),
            ("Release Validation", report.release),
        ]
        for title, section in sections:
            if section is None:
                continue
            lines.append(f"## {title}")
            lines.append("")
            lines.append(f"**Status:** {'✅ PASSED' if section.passed else '❌ FAILED'}")
            lines.append(f"**Summary:** {section.summary}")
            lines.append("")
            if section.items:
                lines.append("| Check | Status | Severity | Message |")
                lines.append("|-------|--------|----------|---------|")
                for item in section.items:
                    status_icon = self._status_icon(item.status)
                    lines.append(f"| {item.name} | {status_icon} | {item.severity.value} | {item.message} |")
                lines.append("")
        if report.checklist:
            lines.append("## Production Checklist Summary")
            lines.append("")
            cl = report.checklist
            lines.append(f"- **Pass Rate:** {cl.pass_rate:.1%}")
            lines.append(f"- **Passed:** {cl.passed}/{cl.total}")
            lines.append(f"- **Failed:** {cl.failed}")
            lines.append("")
        verdict = "**GO FOR PRODUCTION** 🚀" if report.overall_ready else "**NO-GO** ❌ — Address failed items before proceeding"  # noqa: E501
        lines.append("## Final Verdict")
        lines.append("")
        lines.append(verdict)
        return "\n".join(lines)

    def _status_icon(self, status: ValidationStatus) -> str:
        return {
            ValidationStatus.PASSED: "✅",
            ValidationStatus.FAILED: "❌",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.SKIPPED: "⏭️",
            ValidationStatus.PENDING: "⏳",
        }.get(status, "❓")
