import json

import pytest

from evaluation.exceptions import ReportGenerationError
from evaluation.models import (
    ComparisonResult,
    EvaluationComparison,
    EvaluationMetrics,
    EvaluationReport,
    EvaluationStatistics,
    EvaluationStatus,
    EvaluationType,
    ReportFormat,
)
from evaluation.reporting import ReportGenerator


class TestReportGenerator:
    def setup_method(self):
        self.generator = ReportGenerator()

    def _make_report(self, with_metrics=True, with_stats=True, with_results=True):
        report = EvaluationReport(
            report_id="rep-1",
            dataset_name="Test Dataset",
            timestamp=1000.0,
            status=EvaluationStatus.COMPLETED,
        )
        if with_metrics:
            report.metrics = EvaluationMetrics(
                evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
                intent_accuracy=0.95,
                entity_accuracy=0.85,
                knowledge_precision=0.9,
                knowledge_recall=0.8,
                hallucination_rate=0.02,
                latency_ms=150.0,
                token_usage=1000,
                workflow_success_rate=0.99,
            )
        if with_stats:
            report.statistics = EvaluationStatistics(
                total_cases=100,
                passed=90,
                failed=10,
                pass_rate=0.9,
                average_score=0.88,
                average_latency_ms=150.0,
            )
        if with_results:
            from evaluation.models import Baseline, EvaluationOutput, EvaluationResult, ScenarioType
            report.results = [
                EvaluationResult(
                    case_id="c1",
                    evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
                    scenario_type=ScenarioType.SINGLE_TURN,
                    output=EvaluationOutput(latency_ms=100.0),
                    baseline=Baseline(),
                    passed=True,
                    score=0.95,
                ),
                EvaluationResult(
                    case_id="c2",
                    evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
                    scenario_type=ScenarioType.SINGLE_TURN,
                    output=EvaluationOutput(latency_ms=200.0),
                    baseline=Baseline(),
                    passed=False,
                    score=0.3,
                    errors=["error occurred"],
                ),
            ]
        return report

    def test_generate_unsupported_format(self):
        report = self._make_report()
        with pytest.raises(ReportGenerationError):
            self.generator.generate(report, "unknown")

    def test_generate_json(self):
        report = self._make_report()
        output = self.generator.generate(report, ReportFormat.JSON)
        data = json.loads(output)
        assert data["report_id"] == "rep-1"
        assert data["dataset_name"] == "Test Dataset"
        assert data["status"] == "completed"
        assert data["result_count"] == 2
        assert data["metrics"] is not None
        assert data["statistics"] is not None

    def test_generate_json_no_metrics_no_stats(self):
        report = self._make_report(with_metrics=False, with_stats=False)
        output = self.generator.generate(report, ReportFormat.JSON)
        data = json.loads(output)
        assert data["metrics"] is None
        assert data["statistics"] is None

    def test_generate_markdown(self):
        report = self._make_report()
        output = self.generator.generate(report, ReportFormat.MARKDOWN)
        assert "# Evaluation Report: Test Dataset" in output
        assert "**Report ID:** rep-1" in output
        assert "**Status:** completed" in output
        assert "## Statistics" in output
        assert "| Total Cases | 100 |" in output
        assert "## Metrics" in output
        assert "| Intent Accuracy | 0.9500 |" in output
        assert "## Results" in output
        assert "**c1** [PASS] Score: 0.9500" in output
        assert "**c2** [FAIL] Score: 0.3000" in output

    def test_generate_markdown_no_metrics_no_stats(self):
        report = self._make_report(with_metrics=False, with_stats=False)
        output = self.generator.generate(report, ReportFormat.MARKDOWN)
        assert "## Statistics" not in output
        assert "## Metrics" not in output
        assert "## Results" in output

    def test_generate_html(self):
        report = self._make_report()
        output = self.generator.generate(report, ReportFormat.HTML)
        assert "<!DOCTYPE html>" in output
        assert "<h1>Evaluation Report: Test Dataset</h1>" in output
        assert "Status: completed" in output
        assert "<h2>Statistics</h2>" in output
        assert "<h2>Metrics</h2>" in output
        assert "PASS" in output
        assert "FAIL" in output

    def test_generate_csv(self):
        report = self._make_report()
        output = self.generator.generate(report, ReportFormat.CSV)
        lines = output.strip().splitlines()
        assert len(lines) == 3
        assert lines[0] == "case_id,evaluation_type,scenario_type,passed,score,latency_ms,error"
        assert lines[1].startswith("c1,intent_classification,single_turn,True,0.95,100.0,")
        assert lines[2].startswith("c2,intent_classification,single_turn,False,0.3,200.0,error occurred")

    def test_generate_comparison_unsupported_format(self):
        comparison = EvaluationComparison(baseline_label="v1", comparison_label="v2")
        with pytest.raises(ReportGenerationError):
            self.generator.generate_comparison(comparison, ReportFormat.CSV)

    def test_generate_comparison_json(self):
        comparison = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
            overall_improvement=0.15,
            results=[
                ComparisonResult(
                    label="accuracy",
                    scores={"baseline": 0.8, "comparison": 0.9},
                    improvement=0.125,
                ),
            ],
        )
        output = self.generator.generate_comparison(comparison, ReportFormat.JSON)
        data = json.loads(output)
        assert data["baseline"] == "v1"
        assert data["comparison"] == "v2"
        assert data["overall_improvement"] == 0.15
        assert len(data["results"]) == 1
        assert data["results"][0]["label"] == "accuracy"

    def test_generate_comparison_markdown(self):
        comparison = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
            overall_improvement=0.15,
            results=[
                ComparisonResult(
                    label="accuracy",
                    scores={"baseline": 0.8, "comparison": 0.9},
                    improvement=0.125,
                ),
            ],
        )
        output = self.generator.generate_comparison(comparison, ReportFormat.MARKDOWN)
        assert "# Comparison: v1 vs v2" in output
        assert "**Overall Improvement:** +15.00%" in output
        assert "accuracy" in output

    def test_generate_trend_json(self):
        comparison = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
            results=[
                ComparisonResult(label="accuracy", scores={"baseline": 0.8, "comparison": 0.9}),
            ],
        )
        output = self.generator.generate_comparison(comparison, ReportFormat.TREND)
        data = json.loads(output)
        assert data["type"] == "trend"
        assert len(data["data_points"]) == 1

    def test_generate_regression_json(self):
        comparison = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
            results=[
                ComparisonResult(label="accuracy", scores={"baseline": 0.9, "comparison": 0.8}, improvement=-0.1),
                ComparisonResult(label="latency", scores={"baseline": 0.5, "comparison": 0.7}, improvement=0.2),
            ],
        )
        output = self.generator.generate_comparison(comparison, ReportFormat.REGRESSION)
        data = json.loads(output)
        assert data["type"] == "regression"
        assert data["regression_count"] == 1
        assert data["total_metrics"] == 2
        assert data["regressions"][0]["label"] == "accuracy"

    def test_generate_comparison_no_results(self):
        comparison = EvaluationComparison(baseline_label="v1", comparison_label="v2")
        output = self.generator.generate_comparison(comparison, ReportFormat.JSON)
        data = json.loads(output)
        assert data["results"] == []

    def test_generate_markdown_no_results(self):
        report = self._make_report(with_results=False)
        output = self.generator.generate(report, ReportFormat.MARKDOWN)
        assert "## Results" in output
