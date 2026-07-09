import json

import pytest

from evaluation.exceptions import EvaluationExecutionError
from evaluation.metrics import MetricsComputer
from evaluation.models import (
    Baseline,
    DatasetFormat,
    EvaluationCase,
    EvaluationDataset,
    EvaluationOutput,
    EvaluationReport,
    EvaluationRunConfiguration,
    EvaluationStatus,
    EvaluationType,
    ReportFormat,
    ScenarioType,
)
from evaluation.registry import EvaluationRegistry
from evaluation.reporting import ReportGenerator
from evaluation.runner import EvaluationRunner
from evaluation.scoring import Scorer


class TestEvaluationRunner:
    def setup_method(self):
        self.registry = EvaluationRegistry()
        self.scorer = Scorer()
        self.metrics_computer = MetricsComputer()
        self.report_generator = ReportGenerator()
        self.runner = EvaluationRunner(
            registry=self.registry,
            scorer=self.scorer,
            metrics_computer=self.metrics_computer,
            report_generator=self.report_generator,
        )

    def _make_case(self, case_id="c1", eval_type=EvaluationType.INTENT_CLASSIFICATION, scenario_type=ScenarioType.SINGLE_TURN, input_data=None, baseline=None):
        return EvaluationCase(
            case_id=case_id,
            evaluation_type=eval_type,
            scenario_type=scenario_type,
            input=input_data or {"query": "hello"},
            baseline=baseline or Baseline(expected_intent="hello"),
        )

    def _make_dataset(self, cases=None):
        return EvaluationDataset(
            dataset_id="ds-1",
            name="Test Dataset",
            format=DatasetFormat.GOLDEN,
            cases=cases or [],
        )

    def _register_dummy_evaluator(self, eval_type=EvaluationType.INTENT_CLASSIFICATION):
        async def evaluator(case):
            return EvaluationOutput(
                predicted_intent=case.input.get("query", ""),
                confidence=1.0,
                latency_ms=10.0,
            )

        self.registry.register(eval_type, evaluator)

    @pytest.mark.asyncio
    async def test_run_no_cases(self):
        dataset = self._make_dataset()
        with pytest.raises(EvaluationExecutionError, match="No cases match the run configuration"):
            await self.runner.run(dataset)

    @pytest.mark.asyncio
    async def test_run_single_case(self):
        self._register_dummy_evaluator()
        dataset = self._make_dataset(cases=[self._make_case()])
        report = await self.runner.run(dataset)
        assert report.status == EvaluationStatus.COMPLETED
        assert len(report.results) == 1
        assert report.results[0].passed is True
        assert report.metrics is not None
        assert report.statistics is not None
        assert report.statistics.total_cases == 1

    @pytest.mark.asyncio
    async def test_run_all_failed(self):
        async def failing_evaluator(case):
            raise ValueError("Evaluator failed")

        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, failing_evaluator)
        dataset = self._make_dataset(cases=[self._make_case()])
        report = await self.runner.run(dataset)
        assert report.status == EvaluationStatus.FAILED
        assert report.results[0].passed is False
        assert report.results[0].score == 0.0
        assert "Evaluator failed" in report.results[0].errors[0]

    @pytest.mark.asyncio
    async def test_run_partial(self):
        self._register_dummy_evaluator()
        case1 = self._make_case(case_id="c1", input_data={"query": "hello"})
        case2 = self._make_case(case_id="c2", input_data={"query": "wrong"}, baseline=Baseline(expected_intent="different"))
        dataset = self._make_dataset(cases=[case1, case2])
        report = await self.runner.run(dataset)
        assert report.status == EvaluationStatus.PARTIAL
        assert report.results[0].passed is True
        assert report.results[1].passed is False

    @pytest.mark.asyncio
    async def test_run_with_fail_fast(self):
        async def sometimes_fails(case):
            if case.case_id == "c2":
                raise ValueError("Fail fast error")
            return EvaluationOutput(predicted_intent="hello", confidence=1.0, latency_ms=5.0)

        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, sometimes_fails)
        case1 = self._make_case(case_id="c1")
        case2 = self._make_case(case_id="c2")
        case3 = self._make_case(case_id="c3")
        dataset = self._make_dataset(cases=[case1, case2, case3])
        config = EvaluationRunConfiguration(fail_fast=True)
        report = await self.runner.run(dataset, config)
        assert len(report.results) == 2

    @pytest.mark.asyncio
    async def test_run_parallel(self):
        self._register_dummy_evaluator()
        cases = [self._make_case(case_id=f"c{i}") for i in range(5)]
        dataset = self._make_dataset(cases=cases)
        config = EvaluationRunConfiguration(parallel=True)
        report = await self.runner.run(dataset, config)
        assert report.status == EvaluationStatus.COMPLETED
        assert len(report.results) == 5

    @pytest.mark.asyncio
    async def test_run_with_filter_evaluation_types(self):
        self._register_dummy_evaluator(EvaluationType.INTENT_CLASSIFICATION)
        self._register_dummy_evaluator(EvaluationType.ENTITY_EXTRACTION)
        case1 = self._make_case(case_id="c1", eval_type=EvaluationType.INTENT_CLASSIFICATION)
        case2 = self._make_case(case_id="c2", eval_type=EvaluationType.ENTITY_EXTRACTION)
        dataset = self._make_dataset(cases=[case1, case2])
        config = EvaluationRunConfiguration(evaluation_types=[EvaluationType.INTENT_CLASSIFICATION])
        report = await self.runner.run(dataset, config)
        assert len(report.results) == 1
        assert report.results[0].case_id == "c1"

    @pytest.mark.asyncio
    async def test_run_with_filter_scenario_types(self):
        self._register_dummy_evaluator()
        case1 = self._make_case(case_id="c1", scenario_type=ScenarioType.SINGLE_TURN)
        case2 = self._make_case(case_id="c2", scenario_type=ScenarioType.MULTI_TURN)
        dataset = self._make_dataset(cases=[case1, case2])
        config = EvaluationRunConfiguration(scenario_types=[ScenarioType.MULTI_TURN])
        report = await self.runner.run(dataset, config)
        assert len(report.results) == 1
        assert report.results[0].case_id == "c2"

    @pytest.mark.asyncio
    async def test_run_with_max_cases(self):
        self._register_dummy_evaluator()
        cases = [self._make_case(case_id=f"c{i}") for i in range(10)]
        dataset = self._make_dataset(cases=cases)
        config = EvaluationRunConfiguration(max_cases=3)
        report = await self.runner.run(dataset, config)
        assert len(report.results) == 3

    @pytest.mark.asyncio
    async def test_run_with_dataset_id_filter(self):
        self._register_dummy_evaluator()
        case = self._make_case()
        dataset = self._make_dataset(cases=[case])
        config = EvaluationRunConfiguration(dataset_ids=["other-dataset"])
        with pytest.raises(EvaluationExecutionError, match="No cases match the run configuration"):
            await self.runner.run(dataset, config)

    @pytest.mark.asyncio
    async def test_compare_both_reports_have_metrics(self):
        self._register_dummy_evaluator()
        dataset = self._make_dataset(cases=[self._make_case()])
        baseline_report = await self.runner.run(dataset)
        comparison_report = await self.runner.run(dataset)
        result = await self.runner.compare(baseline_report, comparison_report)
        assert "comparison" in result
        assert "json" in result
        assert "markdown" in result
        assert result["comparison"].overall_improvement == 0.0

    @pytest.mark.asyncio
    async def test_compare_no_metrics(self):
        report1 = EvaluationReport(report_id="r1", dataset_name="ds1")
        report2 = EvaluationReport(report_id="r2", dataset_name="ds2")
        with pytest.raises(EvaluationExecutionError, match="Both reports must have computed metrics"):
            await self.runner.compare(report1, report2)

    def test_generate_report(self):
        report = EvaluationReport(report_id="r1", dataset_name="ds1")
        output = self.runner.generate_report(report, ReportFormat.JSON)
        data = json.loads(output)
        assert data["report_id"] == "r1"
