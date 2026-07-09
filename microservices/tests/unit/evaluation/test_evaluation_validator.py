
from evaluation.models import (
    Baseline,
    EvaluationCase,
    EvaluationDataset,
    EvaluationOutput,
    EvaluationResult,
    EvaluationScenario,
    EvaluationType,
    ScenarioType,
)
from evaluation.validator import EvaluationValidator


class TestEvaluationValidator:
    def setup_method(self):
        self.validator = EvaluationValidator()

    def _make_case(self, case_id="c1", input_data=None, baseline=None):
        if input_data is None:
            input_data = {"query": "hello"}
        return EvaluationCase(
            case_id=case_id,
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input=input_data,
            baseline=baseline or Baseline(expected_intent="hi"),
        )

    def test_validate_dataset_valid(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Test",
            format="golden",
            cases=[self._make_case()],
        )
        errors = self.validator.validate_dataset(dataset)
        assert errors == []

    def test_validate_dataset_no_id(self):
        dataset = EvaluationDataset(
            dataset_id="",
            name="Test",
            format="golden",
        )
        errors = self.validator.validate_dataset(dataset)
        assert "Dataset ID is required" in errors

    def test_validate_dataset_no_name(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="",
            format="golden",
        )
        errors = self.validator.validate_dataset(dataset)
        assert "Dataset name is required" in errors

    def test_validate_dataset_duplicate_case_ids(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Test",
            format="golden",
            cases=[self._make_case("c1"), self._make_case("c1")],
        )
        errors = self.validator.validate_dataset(dataset)
        assert any("Duplicate case_id: c1" in e for e in errors)

    def test_validate_case_empty_id(self):
        case = self._make_case(case_id="")
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", cases=[case])
        errors = self.validator.validate_dataset(dataset)
        assert any("Case ID is required" in e for e in errors)

    def test_validate_case_empty_input(self):
        case = self._make_case(input_data={})
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", cases=[case])
        errors = self.validator.validate_dataset(dataset)
        assert any("Case input is required" in e for e in errors)

    def test_validate_baseline_empty(self):
        case = self._make_case(baseline=Baseline())
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", cases=[case])
        errors = self.validator.validate_dataset(dataset)
        assert any("Baseline must have at least one expected value" in e for e in errors)

    def test_validate_baseline_with_golden_answer(self):
        baseline = Baseline(golden_answer="yes")
        case = self._make_case(baseline=baseline)
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", cases=[case])
        errors = self.validator.validate_dataset(dataset)
        assert errors == []

    def test_validate_scenario_empty_id(self):
        scenario = EvaluationScenario(scenario_id="", scenario_type=ScenarioType.SINGLE_TURN, name="")
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", scenarios=[scenario])
        errors = self.validator.validate_dataset(dataset)
        assert any("Scenario ID is required" in e for e in errors)

    def test_validate_scenario_empty_name(self):
        scenario = EvaluationScenario(scenario_id="s1", scenario_type=ScenarioType.SINGLE_TURN, name="")
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden", scenarios=[scenario])
        errors = self.validator.validate_dataset(dataset)
        assert any("Scenario name is required" in e for e in errors)

    def test_validate_result_empty_case_id(self):
        result = EvaluationResult(
            case_id="",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(),
            baseline=Baseline(),
        )
        errors = self.validator.validate_result(result)
        assert "Result case_id is required" in errors

    def test_validate_result_valid(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(),
            baseline=Baseline(),
        )
        errors = self.validator.validate_result(result)
        assert errors == []

    def test_validate_run_configuration_empty_dataset(self):
        dataset = EvaluationDataset(dataset_id="ds-1", name="Test", format="golden")
        errors = self.validator.validate_run_configuration(dataset, 1)
        assert "Dataset has no cases or scenarios to evaluate" in errors

    def test_validate_run_configuration_no_evaluators(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Test",
            format="golden",
            cases=[self._make_case()],
        )
        errors = self.validator.validate_run_configuration(dataset, 0)
        assert "No evaluators registered" in errors

    def test_validate_run_configuration_valid(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Test",
            format="golden",
            cases=[self._make_case()],
        )
        errors = self.validator.validate_run_configuration(dataset, 5)
        assert errors == []

    def test_validate_baseline_match_intent_success(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(predicted_intent="hello"),
            baseline=Baseline(expected_intent="hello"),
        )
        assert self.validator.validate_baseline_match(result) is True

    def test_validate_baseline_match_intent_failure(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(predicted_intent="wrong"),
            baseline=Baseline(expected_intent="hello"),
        )
        assert self.validator.validate_baseline_match(result) is False

    def test_validate_baseline_match_workflow_success(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.WORKFLOW_REQUEST,
            scenario_type=ScenarioType.WORKFLOW_EXECUTION,
            output=EvaluationOutput(predicted_workflow="book"),
            baseline=Baseline(expected_workflow="book"),
        )
        assert self.validator.validate_baseline_match(result) is True

    def test_validate_baseline_match_workflow_failure(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.WORKFLOW_REQUEST,
            scenario_type=ScenarioType.WORKFLOW_EXECUTION,
            output=EvaluationOutput(predicted_workflow="cancel"),
            baseline=Baseline(expected_workflow="book"),
        )
        assert self.validator.validate_baseline_match(result) is False

    def test_validate_baseline_match_no_baseline(self):
        result = EvaluationResult(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(),
            baseline=Baseline(),
        )
        assert self.validator.validate_baseline_match(result) is True

    def test_validate_dataset_multiple_errors(self):
        dataset = EvaluationDataset(
            dataset_id="",
            name="",
            format="golden",
            cases=[
                self._make_case(case_id="", input_data={}, baseline=Baseline()),
                self._make_case(case_id="", input_data={}, baseline=Baseline()),
            ],
        )
        errors = self.validator.validate_dataset(dataset)
        assert len(errors) >= 4
