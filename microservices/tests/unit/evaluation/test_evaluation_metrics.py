import pytest

from evaluation.exceptions import MetricComputationError
from evaluation.metrics import MetricsComputer
from evaluation.models import (
    Baseline,
    EvaluationOutput,
    EvaluationResult,
    EvaluationType,
    MetricType,
    ScenarioType,
)


class TestMetricsComputer:
    def setup_method(self):
        self.computer = MetricsComputer()

    def _make_result(
        self,
        case_id="c1",
        passed=True,
        score=1.0,
        latency_ms=100.0,
        token_count=10,
        eval_type=EvaluationType.INTENT_CLASSIFICATION,
        scenario_type=ScenarioType.SINGLE_TURN,
        metrics=None,
    ):
        return EvaluationResult(
            case_id=case_id,
            evaluation_type=eval_type,
            scenario_type=scenario_type,
            output=EvaluationOutput(
                latency_ms=latency_ms,
                token_count=token_count,
                predicted_intent="hello",
                predicted_entities=[],
            ),
            baseline=Baseline(expected_intent="hello"),
            passed=passed,
            score=score,
            metrics=metrics or {"intent_match": 1.0, "entity_count": 0, "recall": 1.0, "precision": 1.0, "mrr": 1.0, "ndcg": 1.0, "context_quality": 1.0, "prompt_quality": 1.0, "workflow_success": 1.0},
        )

    def test_compute_metrics_empty(self):
        metrics = self.computer.compute_metrics([])
        assert metrics.evaluation_type == EvaluationType.INTENT_CLASSIFICATION
        assert metrics.intent_accuracy == 0.0

    def test_compute_metrics_single_pass(self):
        results = [self._make_result()]
        metrics = self.computer.compute_metrics(results)
        assert metrics.intent_accuracy == 1.0
        assert metrics.confirmation_accuracy == 1.0
        assert metrics.hallucination_rate == 0.0
        assert metrics.latency_ms == 100.0
        assert metrics.token_usage == 10

    def test_compute_metrics_single_fail(self):
        results = [self._make_result(passed=False, score=0.0, metrics={"intent_match": 0.0})]
        metrics = self.computer.compute_metrics(results)
        assert metrics.intent_accuracy == 0.0
        assert metrics.confirmation_accuracy == 0.0
        assert metrics.failure_rate == 1.0

    def test_compute_metrics_mixed(self):
        results = [
            self._make_result("c1", passed=True, score=1.0, metrics={"intent_match": 1.0, "entity_count": 1, "entity_accuracy": 1.0}),
            self._make_result("c2", passed=False, score=0.0, metrics={"intent_match": 0.0, "entity_count": 0}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.intent_accuracy == 0.5
        assert metrics.confirmation_accuracy == 0.5
        assert metrics.hallucination_rate == 0.0
        assert metrics.failure_rate == 0.5

    def test_compute_metrics_with_entity_accuracy(self):
        results = [
            self._make_result(metrics={"entity_count": 1, "entity_accuracy": 0.8}),
            self._make_result(metrics={"entity_count": 1, "entity_accuracy": 0.6}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.entity_accuracy == 1.0

    def test_compute_metrics_with_recall_precision(self):
        results = [
            self._make_result(metrics={"recall": 0.9, "precision": 0.8, "mrr": 0.7, "ndcg": 0.6, "context_quality": 0.5, "prompt_quality": 0.4}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.memory_recall == 0.9
        assert metrics.knowledge_precision == 0.8
        assert metrics.knowledge_recall == 0.9
        assert metrics.mrr == 0.7
        assert metrics.ndcg == 0.6
        assert metrics.context_quality == 0.5
        assert metrics.prompt_quality == 0.4

    def test_compute_metrics_with_hallucination(self):
        results = [
            self._make_result(metrics={"hallucinated": 1}),
            self._make_result(metrics={"hallucinated": 0}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.hallucination_rate == 0.5

    def test_compute_metrics_with_workflow_success(self):
        results = [
            self._make_result(metrics={"workflow_success": 1}),
            self._make_result(metrics={"workflow_success": 0}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.workflow_success_rate == 0.5

    def test_compute_metrics_with_retries(self):
        results = [
            self._make_result(metrics={"retry_count": 1}),
            self._make_result(metrics={}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.retry_rate == 0.5

    def test_compute_metrics_with_cost(self):
        results = [
            self._make_result(eval_type=EvaluationType.KNOWLEDGE_RETRIEVAL, metrics={"cost": 0.5}),
        ]
        metrics = self.computer.compute_metrics(results)
        assert metrics.embedding_cost == 0.0
        assert metrics.provider_cost == 0.5

    def test_compute_statistics_empty(self):
        stats = self.computer.compute_statistics([])
        assert stats.total_cases == 0

    def test_compute_statistics_single(self):
        results = [self._make_result(score=0.8)]
        stats = self.computer.compute_statistics(results)
        assert stats.total_cases == 1
        assert stats.passed == 1
        assert stats.failed == 0
        assert stats.pass_rate == 1.0
        assert stats.average_score == 0.8
        assert stats.min_score == 0.8
        assert stats.max_score == 0.8
        assert stats.median_score == 0.8

    def test_compute_statistics_multiple(self):
        results = [
            self._make_result("c1", passed=True, score=0.9),
            self._make_result("c2", passed=True, score=0.7),
            self._make_result("c3", passed=False, score=0.2),
        ]
        stats = self.computer.compute_statistics(results)
        assert stats.total_cases == 3
        assert stats.passed == 2
        assert stats.failed == 1
        assert stats.pass_rate == 2 / 3
        assert stats.average_score == (0.9 + 0.7 + 0.2) / 3
        assert stats.min_score == 0.2
        assert stats.max_score == 0.9
        assert stats.median_score == 0.7
        assert stats.std_dev > 0

    def test_compute_statistics_per_type(self):
        results = [
            self._make_result(eval_type=EvaluationType.INTENT_CLASSIFICATION, score=0.9),
            self._make_result(eval_type=EvaluationType.INTENT_CLASSIFICATION, score=0.7),
            self._make_result(eval_type=EvaluationType.ENTITY_EXTRACTION, score=0.5),
        ]
        stats = self.computer.compute_statistics(results)
        assert "intent_classification" in stats.per_type
        assert "entity_extraction" in stats.per_type
        assert stats.per_type["intent_classification"] == 0.8
        assert stats.per_type["entity_extraction"] == 0.5

    def test_compute_statistics_per_scenario(self):
        results = [
            self._make_result(scenario_type=ScenarioType.SINGLE_TURN, score=0.9),
            self._make_result(scenario_type=ScenarioType.MULTI_TURN, score=0.5),
        ]
        stats = self.computer.compute_statistics(results)
        assert "single_turn" in stats.per_scenario
        assert "multi_turn" in stats.per_scenario
        assert stats.per_scenario["single_turn"] == 0.9

    def test_compute_statistics_p95_p99(self):
        results = [self._make_result(f"c{i}", score=i / 20) for i in range(1, 21)]
        stats = self.computer.compute_statistics(results)
        assert stats.p95_score >= stats.p99_score
        assert stats.p95_score > 0
        assert stats.p99_score > 0

    def test_compute_metric_specific_type(self):
        results = [self._make_result()]
        value = self.computer.compute_metric(MetricType.INTENT_ACCURACY, results)
        assert value == 1.0

    def test_compute_metric_unknown(self):
        results = [self._make_result()]
        with pytest.raises(MetricComputationError):
            self.computer.compute_metric("unknown_type", results)

    def test_compute_metric_token_usage(self):
        results = [self._make_result(token_count=50)]
        value = self.computer.compute_metric(MetricType.TOKEN_USAGE, results)
        assert value == 50.0
