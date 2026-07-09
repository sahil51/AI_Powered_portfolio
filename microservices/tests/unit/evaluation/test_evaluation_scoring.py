
from evaluation.models import Baseline, EvaluationOutput, EvaluationResult, EvaluationType, ScenarioType
from evaluation.scoring import Scorer


class TestScorer:
    def setup_method(self):
        self.scorer = Scorer()

    def _make_result(
        self,
        case_id="c1",
        score=1.0,
        predicted_intent="hello",
        predicted_entities=None,
        predicted_value="expected_val",
        predicted_workflow="wf",
        expected_intent="hello",
        expected_entities=None,
        expected_output="expected_val",
        expected_workflow="wf",
        weight=1.0,
    ):
        return EvaluationResult(
            case_id=case_id,
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(
                predicted_intent=predicted_intent,
                predicted_entities=predicted_entities or [],
                predicted_value=predicted_value,
                predicted_workflow=predicted_workflow,
            ),
            baseline=Baseline(
                expected_intent=expected_intent,
                expected_entities=expected_entities or [],
                expected_output=expected_output,
                expected_workflow=expected_workflow,
            ),
            passed=score >= 0.5,
            score=score,
            metrics={"weight": weight, "intent_match": 1.0},
        )

    def test_precision(self):
        assert self.scorer.precision(5, 0) == 1.0
        assert self.scorer.precision(5, 5) == 0.5
        assert self.scorer.precision(0, 0) == 0.0
        assert self.scorer.precision(0, 5) == 0.0

    def test_recall(self):
        assert self.scorer.recall(5, 0) == 1.0
        assert self.scorer.recall(5, 5) == 0.5
        assert self.scorer.recall(0, 0) == 0.0
        assert self.scorer.recall(0, 5) == 0.0

    def test_f1(self):
        assert self.scorer.f1(1.0, 1.0) == 1.0
        assert self.scorer.f1(0.5, 0.5) == 0.5
        assert self.scorer.f1(0.0, 0.0) == 0.0
        assert self.scorer.f1(0.0, 1.0) == 0.0

    def test_accuracy(self):
        assert self.scorer.accuracy(5, 10) == 0.5
        assert self.scorer.accuracy(10, 10) == 1.0
        assert self.scorer.accuracy(0, 10) == 0.0
        assert self.scorer.accuracy(0, 0) == 0.0

    def test_weighted_score_empty(self):
        assert self.scorer.weighted_score([]) == 0.0

    def test_weighted_score_equal_weights(self):
        results = [
            self._make_result("c1", score=1.0, weight=1.0),
            self._make_result("c2", score=0.5, weight=1.0),
        ]
        assert self.scorer.weighted_score(results) == 0.75

    def test_weighted_score_different_weights(self):
        results = [
            self._make_result("c1", score=1.0, weight=2.0),
            self._make_result("c2", score=0.5, weight=1.0),
        ]
        assert self.scorer.weighted_score(results) == (1.0 * 2.0 + 0.5 * 1.0) / 3.0

    def test_weighted_score_zero_total_weight(self):
        results = [
            self._make_result("c1", score=1.0, weight=0.0),
            self._make_result("c2", score=0.5, weight=0.0),
        ]
        assert self.scorer.weighted_score(results) == 0.0

    def test_overall_platform_score_empty(self):
        assert self.scorer.overall_platform_score([]) == 0.0

    def test_overall_platform_score(self):
        results = [
            self._make_result("c1", score=1.0),
            self._make_result("c2", score=0.5),
            self._make_result("c3", score=0.0),
        ]
        assert self.scorer.overall_platform_score(results) == 0.5

    def test_score_result_all_matches(self):
        result = self._make_result(
            expected_intent="hello",
            expected_entities=[{"type": "person", "value": "John"}],
            expected_output="expected_val",
            expected_workflow="wf",
        )
        score = self.scorer.score_result(result)
        assert score == 1.0

    def test_score_result_no_matches(self):
        result = self._make_result(
            predicted_intent="wrong",
            expected_intent="hello",
            predicted_entities=[],
            expected_entities=[{"type": "person", "value": "John"}],
            predicted_value="wrong_val",
            expected_output="expected_val",
            predicted_workflow="wrong_wf",
            expected_workflow="wf",
        )
        score = self.scorer.score_result(result)
        assert score == 0.0

    def test_score_result_partial_match(self):
        result = self._make_result(
            predicted_intent="hello",
            expected_intent="hello",
            predicted_entities=[{"type": "person", "value": "Jane"}],
            expected_entities=[{"type": "person", "value": "John"}],
            predicted_value="expected_val",
            expected_output="expected_val",
            predicted_workflow="wrong_wf",
            expected_workflow="wf",
        )
        score = self.scorer.score_result(result)
        assert 0.0 < score < 1.0
        assert score == 0.5

    def test_score_result_no_baseline(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(),
            baseline=Baseline(),
        )
        score = self.scorer.score_result(result)
        assert score == 0.0
