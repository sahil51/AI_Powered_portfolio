from __future__ import annotations

from evaluation.models import (
    Baseline,
    EvaluationCase,
    EvaluationDataset,
    EvaluationResult,
    EvaluationScenario,
)


class EvaluationValidator:
    def validate_dataset(self, dataset: EvaluationDataset) -> list[str]:
        errors: list[str] = []
        if not dataset.dataset_id:
            errors.append("Dataset ID is required")
        if not dataset.name:
            errors.append("Dataset name is required")
        seen_ids: set[str] = set()
        for case in dataset.cases:
            case_errors = self._validate_case(case)
            for err in case_errors:
                errors.append(f"Case {case.case_id}: {err}")
            if case.case_id in seen_ids:
                errors.append(f"Duplicate case_id: {case.case_id}")
            seen_ids.add(case.case_id)
        for scenario in dataset.scenarios:
            scenario_errors = self._validate_scenario(scenario)
            for err in scenario_errors:
                errors.append(f"Scenario {scenario.scenario_id}: {err}")
        return errors

    def _validate_case(self, case: EvaluationCase) -> list[str]:
        errors: list[str] = []
        if not case.case_id:
            errors.append("Case ID is required")
        if not case.input:
            errors.append("Case input is required")
        errors.extend(self._validate_baseline(case.baseline))
        return errors

    def _validate_scenario(self, scenario: EvaluationScenario) -> list[str]:
        errors: list[str] = []
        if not scenario.scenario_id:
            errors.append("Scenario ID is required")
        if not scenario.name:
            errors.append("Scenario name is required")
        return errors

    def _validate_baseline(self, baseline: Baseline) -> list[str]:
        errors: list[str] = []
        has_any = bool(
            baseline.golden_answer or baseline.expected_output
            or baseline.expected_entities or baseline.expected_intent
            or baseline.expected_workflow or baseline.expected_context
        )
        if not has_any:
            errors.append("Baseline must have at least one expected value")
        return errors

    def validate_result(self, result: EvaluationResult) -> list[str]:
        errors: list[str] = []
        if not result.case_id:
            errors.append("Result case_id is required")
        return errors

    def validate_run_configuration(self, dataset: EvaluationDataset, evaluator_count: int) -> list[str]:
        errors: list[str] = []
        if not dataset.cases and not dataset.scenarios:
            errors.append("Dataset has no cases or scenarios to evaluate")
        if evaluator_count == 0:
            errors.append("No evaluators registered")
        return errors

    def validate_baseline_match(self, result: EvaluationResult) -> bool:
        baseline = result.baseline
        output = result.output
        if baseline.expected_intent and output.predicted_intent:
            if output.predicted_intent.strip().lower() != baseline.expected_intent.strip().lower():
                return False
        if baseline.expected_workflow and output.predicted_workflow:
            if output.predicted_workflow.strip().lower() != baseline.expected_workflow.strip().lower():
                return False
        return True
