from __future__ import annotations

import asyncio
import time
from typing import Any

from evaluation.exceptions import EvaluationExecutionError
from evaluation.metrics import MetricsComputer
from evaluation.models import (
    EvaluationCase,
    EvaluationDataset,
    EvaluationOutput,
    EvaluationReport,
    EvaluationResult,
    EvaluationRunConfiguration,
    EvaluationStatus,
    ReportFormat,
)
from evaluation.registry import EvaluationRegistry
from evaluation.reporting import ReportGenerator
from evaluation.scoring import Scorer


class EvaluationRunner:
    def __init__(
        self,
        registry: EvaluationRegistry,
        scorer: Scorer | None = None,
        metrics_computer: MetricsComputer | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        self._registry = registry
        self._scorer = scorer or Scorer()
        self._metrics_computer = metrics_computer or MetricsComputer()
        self._report_generator = report_generator or ReportGenerator()

    async def run(
        self,
        dataset: EvaluationDataset,
        config: EvaluationRunConfiguration | None = None,
    ) -> EvaluationReport:
        cfg = config or EvaluationRunConfiguration()
        cases = self._filter_cases(dataset, cfg)
        if not cases:
            raise EvaluationExecutionError("No cases match the run configuration")

        report = EvaluationReport(
            report_id=f"eval_{int(time.time())}",
            dataset_name=dataset.name,
            timestamp=time.time(),
            status=EvaluationStatus.RUNNING,
        )

        try:
            if cfg.parallel:
                results = await self._run_parallel(cases, cfg)
            else:
                results = await self._run_sequential(cases, cfg)
        except Exception as e:
            report.status = EvaluationStatus.FAILED
            report.errors.append(str(e))
            return report

        report.results = results
        report.metrics = self._metrics_computer.compute_metrics(results)
        report.statistics = self._metrics_computer.compute_statistics(results)

        passed = sum(1 for r in results if r.passed)
        all_passed = len(results) > 0 and passed == len(results)
        partial = passed > 0 and passed < len(results)
        if all_passed:
            report.status = EvaluationStatus.COMPLETED
        elif partial:
            report.status = EvaluationStatus.PARTIAL
        else:
            report.status = EvaluationStatus.FAILED

        return report

    async def compare(
        self,
        baseline_report: EvaluationReport,
        comparison_report: EvaluationReport,
    ) -> dict[str, Any]:
        from evaluation.models import ComparisonResult, EvaluationComparison

        if not baseline_report.metrics or not comparison_report.metrics:
            raise EvaluationExecutionError("Both reports must have computed metrics")

        results: list = []
        baseline_metrics = baseline_report.metrics.__dict__
        comparison_metrics = comparison_report.metrics.__dict__

        for key in baseline_metrics:
            b_val = baseline_metrics[key]
            c_val = comparison_metrics.get(key, 0)
            if isinstance(b_val, (int, float)) and key != "evaluation_type":
                improvement = c_val - b_val
                if isinstance(b_val, float) and b_val > 0:
                    improvement = (c_val - b_val) / abs(b_val)
                results.append(ComparisonResult(
                    label=key,
                    scores={"baseline": float(b_val), "comparison": float(c_val)},
                    improvement=float(improvement),
                ))

        overall_imp = 0.0
        numeric_results = [r for r in results if isinstance(r.improvement, (int, float))]
        if numeric_results:
            overall_imp = sum(r.improvement for r in numeric_results) / len(numeric_results)

        comparison = EvaluationComparison(
            baseline_label=baseline_report.report_id,
            comparison_label=comparison_report.report_id,
            results=results,
            overall_improvement=overall_imp,
        )
        return {
            "comparison": comparison,
            "json": self._report_generator.generate_comparison(comparison, ReportFormat.JSON),
            "markdown": self._report_generator.generate_comparison(comparison, ReportFormat.MARKDOWN),
        }

    def generate_report(self, report: EvaluationReport, fmt: ReportFormat) -> str:
        return self._report_generator.generate(report, fmt)

    async def _run_sequential(
        self,
        cases: list[EvaluationCase],
        config: EvaluationRunConfiguration,
    ) -> list[EvaluationResult]:
        results: list[EvaluationResult] = []
        for case in cases:
            result = await self._evaluate_case(case, config)
            results.append(result)
            if config.fail_fast and result.errors:
                break
        return results

    async def _run_parallel(
        self,
        cases: list[EvaluationCase],
        config: EvaluationRunConfiguration,
    ) -> list[EvaluationResult]:
        tasks = [self._evaluate_case(case, config) for case in cases]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _evaluate_case(
        self,
        case: EvaluationCase,
        config: EvaluationRunConfiguration,
    ) -> EvaluationResult:
        start = time.time()
        try:
            evaluator = self._registry.get(case.evaluation_type)
            output = await evaluator(case)
        except Exception as e:
            output = EvaluationOutput(error=str(e))
            return EvaluationResult(
                case_id=case.case_id,
                evaluation_type=case.evaluation_type,
                scenario_type=case.scenario_type,
                output=output,
                baseline=case.baseline,
                passed=False,
                score=0.0,
                errors=[str(e)],
                timestamp=time.time(),
            )

        score = self._scorer.score_result(
            EvaluationResult(
                case_id=case.case_id,
                evaluation_type=case.evaluation_type,
                scenario_type=case.scenario_type,
                output=output,
                baseline=case.baseline,
            )
        )

        result = EvaluationResult(
            case_id=case.case_id,
            evaluation_type=case.evaluation_type,
            scenario_type=case.scenario_type,
            output=output,
            baseline=case.baseline,
            passed=score >= 0.5,
            score=score,
            timestamp=time.time(),
        )
        result.metrics = self._compute_case_metrics(case, output, score, start)
        return result

    def _compute_case_metrics(
        self,
        case: EvaluationCase,
        output: EvaluationOutput,
        score: float,
        start: float,
    ) -> dict[str, float]:
        metrics: dict[str, float] = {
            "score": score,
            "latency_ms": (time.time() - start) * 1000,
            "weight": case.weight,
        }
        intent_match = 1.0 if (
            case.baseline.expected_intent
            and output.predicted_intent.strip().lower() == case.baseline.expected_intent.strip().lower()
        ) else 0.0
        metrics["intent_match"] = intent_match
        if case.baseline.expected_entities and output.predicted_entities:
            expected_set = {(e.get("type", ""), e.get("value", "")) for e in case.baseline.expected_entities}
            predicted_set = {(e.get("type", ""), e.get("value", "")) for e in output.predicted_entities}
            if expected_set:
                intersection = expected_set & predicted_set
                metrics["entity_accuracy"] = len(intersection) / len(expected_set)
                metrics["entity_count"] = float(len(output.predicted_entities))
        if output.latency_ms > 0:
            metrics["computed_latency"] = output.latency_ms
        if output.error:
            metrics["error"] = 1.0
        return metrics

    def _filter_cases(
        self,
        dataset: EvaluationDataset,
        config: EvaluationRunConfiguration,
    ) -> list[EvaluationCase]:
        cases = list(dataset.cases)
        if config.evaluation_types:
            cases = [c for c in cases if c.evaluation_type in config.evaluation_types]
        if config.scenario_types:
            cases = [c for c in cases if c.scenario_type in config.scenario_types]
        if config.dataset_ids and dataset.dataset_id not in config.dataset_ids:
            cases = []
        if config.max_cases > 0:
            cases = cases[:config.max_cases]
        return cases
