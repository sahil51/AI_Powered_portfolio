from __future__ import annotations

import csv
import io
import json
from typing import Any

from evaluation.exceptions import ReportGenerationError
from evaluation.models import (
    EvaluationComparison,
    EvaluationReport,
    ReportFormat,
)


class ReportGenerator:
    def generate(self, report: EvaluationReport, fmt: ReportFormat) -> str:
        generators = {
            ReportFormat.JSON: self._generate_json,
            ReportFormat.MARKDOWN: self._generate_markdown,
            ReportFormat.HTML: self._generate_html,
            ReportFormat.CSV: self._generate_csv,
        }
        generator = generators.get(fmt)
        if generator is None:
            raise ReportGenerationError(f"Unsupported report format: {fmt}")
        return generator(report)

    def generate_comparison(self, comparison: EvaluationComparison, fmt: ReportFormat) -> str:
        generators = {
            ReportFormat.JSON: self._comparison_json,
            ReportFormat.MARKDOWN: self._comparison_markdown,
            ReportFormat.TREND: self._trend_json,
            ReportFormat.REGRESSION: self._regression_json,
        }
        generator = generators.get(fmt)
        if generator is None:
            raise ReportGenerationError(f"Unsupported comparison format: {fmt}")
        return generator(comparison)

    def _generate_json(self, report: EvaluationReport) -> str:
        data = self._report_to_dict(report)
        return json.dumps(data, indent=2, default=str)

    def _generate_markdown(self, report: EvaluationReport) -> str:
        lines = [f"# Evaluation Report: {report.dataset_name}", ""]
        lines.append(f"**Report ID:** {report.report_id}")
        lines.append(f"**Status:** {report.status.value}")
        lines.append(f"**Timestamp:** {report.timestamp}")
        lines.append("")
        if report.statistics:
            s = report.statistics
            lines.append("## Statistics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Total Cases | {s.total_cases} |")
            lines.append(f"| Passed | {s.passed} |")
            lines.append(f"| Failed | {s.failed} |")
            lines.append(f"| Pass Rate | {s.pass_rate:.2%} |")
            lines.append(f"| Average Score | {s.average_score:.4f} |")
            lines.append(f"| Average Latency | {s.average_latency_ms:.2f} ms |")
            lines.append("")
        if report.metrics:
            m = report.metrics
            lines.append("## Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Intent Accuracy | {m.intent_accuracy:.4f} |")
            lines.append(f"| Entity Accuracy | {m.entity_accuracy:.4f} |")
            lines.append(f"| Knowledge Precision | {m.knowledge_precision:.4f} |")
            lines.append(f"| Knowledge Recall | {m.knowledge_recall:.4f} |")
            lines.append(f"| Hallucination Rate | {m.hallucination_rate:.4f} |")
            lines.append(f"| Latency | {m.latency_ms:.2f} ms |")
            lines.append(f"| Token Usage | {m.token_usage} |")
            lines.append(f"| Workflow Success Rate | {m.workflow_success_rate:.4f} |")
            lines.append("")
        lines.append("## Results")
        lines.append("")
        for r in report.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"- **{r.case_id}** [{status}] Score: {r.score:.4f}")
        return "\n".join(lines)

    def _generate_html(self, report: EvaluationReport) -> str:
        self._report_to_dict(report)
        html = "<!DOCTYPE html><html><head><title>Evaluation Report</title>"
        html += "<style>body{font-family:sans-serif;margin:2em}"
        html += "table{border-collapse:collapse;width:100%}"
        html += "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
        html += "th{background-color:#f5f5f5}</style></head><body>"
        html += f"<h1>Evaluation Report: {report.dataset_name}</h1>"
        html += f"<p>Status: {report.status.value} | ID: {report.report_id}</p>"
        if report.statistics:
            s = report.statistics
            html += "<h2>Statistics</h2><table>"
            html += "<tr><th>Metric</th><th>Value</th></tr>"
            html += f"<tr><td>Total Cases</td><td>{s.total_cases}</td></tr>"
            html += f"<tr><td>Pass Rate</td><td>{s.pass_rate:.2%}</td></tr>"
            html += f"<tr><td>Average Score</td><td>{s.average_score:.4f}</td></tr>"
            html += "</table>"
        if report.metrics:
            m = report.metrics
            html += "<h2>Metrics</h2><table>"
            html += "<tr><th>Metric</th><th>Value</th></tr>"
            html += f"<tr><td>Intent Accuracy</td><td>{m.intent_accuracy:.4f}</td></tr>"
            html += f"<tr><td>Entity Accuracy</td><td>{m.entity_accuracy:.4f}</td></tr>"
            html += f"<tr><td>Hallucination Rate</td><td>{m.hallucination_rate:.4f}</td></tr>"
            html += "</table>"
        html += "<h2>Results</h2><table><tr><th>Case</th><th>Status</th><th>Score</th></tr>"
        for r in report.results:
            status = "PASS" if r.passed else "FAIL"
            html += f"<tr><td>{r.case_id}</td><td>{status}</td><td>{r.score:.4f}</td></tr>"
        html += "</table></body></html>"
        return html

    def _generate_csv(self, report: EvaluationReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["case_id", "evaluation_type", "scenario_type", "passed", "score", "latency_ms", "error"])
        for r in report.results:
            writer.writerow([
                r.case_id, r.evaluation_type.value, r.scenario_type.value,
                r.passed, r.score, r.output.latency_ms, "; ".join(r.errors),
            ])
        return output.getvalue()

    def _comparison_json(self, comparison: EvaluationComparison) -> str:
        data = {
            "baseline": comparison.baseline_label,
            "comparison": comparison.comparison_label,
            "overall_improvement": comparison.overall_improvement,
            "results": [
                {
                    "label": r.label,
                    "scores": r.scores,
                    "metrics": r.metrics,
                    "improvement": r.improvement,
                }
                for r in comparison.results
            ],
        }
        return json.dumps(data, indent=2, default=str)

    def _comparison_markdown(self, comparison: EvaluationComparison) -> str:
        lines = [
            f"# Comparison: {comparison.baseline_label} vs {comparison.comparison_label}",
            "",
            f"**Overall Improvement:** {comparison.overall_improvement:+.2%}",
            "",
            "| Metric | Baseline | Comparison | Improvement |",
            "|--------|----------|------------|-------------|",
        ]
        for r in comparison.results:
            baseline_val = r.scores.get("baseline", 0)
            comparison_val = r.scores.get("comparison", 0)
            imp = r.improvement
            lines.append(f"| {r.label} | {baseline_val:.4f} | {comparison_val:.4f} | {imp:+.2%} |")
        return "\n".join(lines)

    def _trend_json(self, comparison: EvaluationComparison) -> str:
        data = {
            "type": "trend",
            "baseline": comparison.baseline_label,
            "comparison": comparison.comparison_label,
            "data_points": [
                {"label": r.label, "values": r.scores}
                for r in comparison.results
            ],
        }
        return json.dumps(data, indent=2, default=str)

    def _regression_json(self, comparison: EvaluationComparison) -> str:
        regressions = [r for r in comparison.results if r.improvement < 0]
        data = {
            "type": "regression",
            "baseline": comparison.baseline_label,
            "comparison": comparison.comparison_label,
            "regression_count": len(regressions),
            "total_metrics": len(comparison.results),
            "regressions": [
                {
                    "label": r.label,
                    "baseline_score": r.scores.get("baseline", 0),
                    "current_score": r.scores.get("comparison", 0),
                    "change": r.improvement,
                }
                for r in regressions
            ],
        }
        return json.dumps(data, indent=2, default=str)

    def _report_to_dict(self, report: EvaluationReport) -> dict[str, Any]:
        return {
            "report_id": report.report_id,
            "dataset_name": report.dataset_name,
            "timestamp": report.timestamp,
            "status": report.status.value,
            "metrics": report.metrics.__dict__ if report.metrics else None,
            "statistics": report.statistics.__dict__ if report.statistics else None,
            "result_count": len(report.results),
            "errors": report.errors,
        }
