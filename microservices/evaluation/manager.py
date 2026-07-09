from __future__ import annotations

from typing import Any

from evaluation.dataset import DatasetLoaderFactory, GoldenDatasetLoader, ScenarioLoader
from evaluation.evaluators import register_default_evaluators
from evaluation.exceptions import EvaluationConfigurationError
from evaluation.health import EvaluationHealthChecker
from evaluation.metrics import MetricsComputer
from evaluation.models import (
    DatasetFormat,
    EvaluationDataset,
    EvaluationReport,
    EvaluationRunConfiguration,
    ReportFormat,
    ScenarioType,
)
from evaluation.registry import EvaluationRegistry
from evaluation.reporting import ReportGenerator
from evaluation.runner import EvaluationRunner
from evaluation.scoring import Scorer
from evaluation.validator import EvaluationValidator
from monitoring.logger import logger


class EvaluationManager:
    def __init__(self) -> None:
        self._initialized = False
        self._registry = EvaluationRegistry()
        self._dataset_loader = DatasetLoaderFactory()
        self._golden_loader = GoldenDatasetLoader()
        self._scenario_loader = ScenarioLoader()
        self._scorer = Scorer()
        self._metrics_computer = MetricsComputer()
        self._report_generator = ReportGenerator()
        self._validator = EvaluationValidator()
        self._health_checker = EvaluationHealthChecker()
        self._runner: EvaluationRunner | None = None
        self._loaded_datasets: dict[str, EvaluationDataset] = {}
        self._last_report: EvaluationReport | None = None
        self._reports: list[EvaluationReport] = []

    @property
    def registry(self) -> EvaluationRegistry:
        return self._registry

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def runner(self) -> EvaluationRunner:
        if self._runner is None:
            raise EvaluationConfigurationError("EvaluationManager not initialized")
        return self._runner

    @property
    def health_checker(self) -> EvaluationHealthChecker:
        return self._health_checker

    @property
    def validator(self) -> EvaluationValidator:
        return self._validator

    @property
    def last_report(self) -> EvaluationReport | None:
        return self._last_report

    async def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Initializing evaluation manager")
        register_default_evaluators(self._registry)
        self._runner = EvaluationRunner(
            registry=self._registry,
            scorer=self._scorer,
            metrics_computer=self._metrics_computer,
            report_generator=self._report_generator,
        )
        self._health_checker.set_evaluators_registered(self._registry.count())
        self._initialized = True
        logger.info(f"Evaluation manager initialized with {self._registry.count()} evaluators")

    async def shutdown(self) -> None:
        if not self._initialized:
            return
        logger.info("Shutting down evaluation manager")
        self._registry.clear()
        self._loaded_datasets.clear()
        self._reports.clear()
        self._last_report = None
        self._runner = None
        self._health_checker.reset()
        self._initialized = False
        logger.info("Evaluation manager shut down")

    def load_dataset(self, path: str, fmt: DatasetFormat = DatasetFormat.GOLDEN, **kwargs: Any) -> EvaluationDataset:
        dataset = self._dataset_loader.load_dataset(path, fmt, **kwargs)
        errors = self._validator.validate_dataset(dataset)
        if errors:
            logger.warning(f"Dataset {path} has validation errors: {errors}")
        self._loaded_datasets[dataset.dataset_id] = dataset
        self._health_checker.set_datasets_loaded(len(self._loaded_datasets))
        logger.info(f"Loaded dataset '{dataset.name}' with {len(dataset.cases)} cases")
        return dataset

    def load_golden_dataset(self, path: str) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.GOLDEN)

    def load_json_dataset(self, path: str) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.JSON)

    def load_yaml_dataset(self, path: str) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.YAML)

    def load_csv_dataset(self, path: str) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.CSV)

    def load_versioned_dataset(self, path: str, version: str) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.VERSIONED, version=version)

    def load_scenario_dataset(self, path: str, scenario_type: ScenarioType | None = None) -> EvaluationDataset:
        return self.load_dataset(path, DatasetFormat.SCENARIO, scenario_type=scenario_type)

    def load_regression_dataset(self, previous_run_path: str, current_dataset_path: str) -> EvaluationDataset:
        return self._dataset_loader.load_dataset(
            current_dataset_path,
            DatasetFormat.REGRESSION,
            previous_run_path=previous_run_path,
        )

    def get_dataset(self, dataset_id: str) -> EvaluationDataset | None:
        return self._loaded_datasets.get(dataset_id)

    def get_datasets(self) -> dict[str, EvaluationDataset]:
        return dict(self._loaded_datasets)

    async def run_evaluation(
        self,
        dataset: EvaluationDataset,
        config: EvaluationRunConfiguration | None = None,
    ) -> EvaluationReport:
        logger.info(f"Running evaluation on dataset '{dataset.name}'")
        report = await self.runner.run(dataset, config)
        self._last_report = report
        self._reports.append(report)
        self._health_checker.record_run(report.status)
        pass_rate = report.statistics.pass_rate if report.statistics else 0.0
        logger.info(f"Evaluation completed: {report.status.value} ({pass_rate:.2%} pass rate)")
        return report

    async def run_evaluation_on_dataset(
        self,
        dataset_id: str,
        config: EvaluationRunConfiguration | None = None,
    ) -> EvaluationReport:
        dataset = self.get_dataset(dataset_id)
        if dataset is None:
            raise EvaluationConfigurationError(f"Dataset {dataset_id} not found")
        return await self.run_evaluation(dataset, config)

    async def compare_reports(self, report1: EvaluationReport, report2: EvaluationReport) -> dict[str, Any]:
        return await self.runner.compare(report1, report2)

    def generate_report(self, report: EvaluationReport, fmt: ReportFormat) -> str:
        return self.runner.generate_report(report, fmt)

    def health_report(self) -> dict[str, Any]:
        return self._health_checker.check()

    def evaluation_report(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "evaluators_registered": self._registry.count(),
            "datasets_loaded": len(self._loaded_datasets),
            "datasets": {k: {"name": v.name, "cases": len(v.cases), "format": v.format.value} for k, v in self._loaded_datasets.items()},  # noqa: E501
            "reports_run": len(self._reports),
            "last_report_status": self._last_report.status.value if self._last_report else None,
            "health": self._health_checker.check(),
        }
