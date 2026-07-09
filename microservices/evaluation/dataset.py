from __future__ import annotations

import csv
import json
import os
from typing import Any

import yaml

from evaluation.exceptions import (
    DatasetFormatError,
    DatasetLoadError,
    DatasetVersionError,
    GoldenDataNotFoundError,
    ScenarioLoadError,
)
from evaluation.models import (
    Baseline,
    DatasetFormat,
    EvaluationCase,
    EvaluationDataset,
    EvaluationScenario,
    EvaluationType,
    ScenarioType,
)


class GoldenDatasetLoader:
    def load(self, path: str) -> EvaluationDataset:
        if not os.path.exists(path):
            raise GoldenDataNotFoundError(f"Golden dataset not found: {path}")
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DatasetFormatError(f"Invalid JSON in golden dataset: {e}")
        return self._parse_dataset(data, DatasetFormat.GOLDEN)

    def _parse_dataset(self, data: dict[str, Any], fmt: DatasetFormat) -> EvaluationDataset:
        dataset = EvaluationDataset(
            dataset_id=data.get("dataset_id", "golden"),
            name=data.get("name", "Golden Dataset"),
            format=fmt,
            version=data.get("version", "1.0.0"),
        )
        for scenario_data in data.get("scenarios", []):
            scenario = self._parse_scenario(scenario_data)
            dataset.scenarios.append(scenario)
            dataset.cases.extend(scenario.cases)
        for case_data in data.get("cases", []):
            case = self._parse_case(case_data)
            dataset.cases.append(case)
        return dataset

    def _parse_scenario(self, data: dict[str, Any]) -> EvaluationScenario:
        scenario = EvaluationScenario(
            scenario_id=data.get("scenario_id", ""),
            scenario_type=ScenarioType(data.get("scenario_type", "single_turn")),
            name=data.get("name", ""),
            description=data.get("description", ""),
        )
        for case_data in data.get("cases", []):
            case = self._parse_case(case_data)
            scenario.cases.append(case)
        return scenario

    def _parse_case(self, data: dict[str, Any]) -> EvaluationCase:
        baseline_data = data.get("baseline", {})
        baseline = Baseline(
            golden_answer=baseline_data.get("golden_answer", ""),
            expected_output=baseline_data.get("expected_output", ""),
            expected_entities=baseline_data.get("expected_entities", []),
            expected_intent=baseline_data.get("expected_intent", ""),
            expected_workflow=baseline_data.get("expected_workflow", ""),
            expected_missing_fields=baseline_data.get("expected_missing_fields", []),
            expected_context=baseline_data.get("expected_context", {}),
        )
        return EvaluationCase(
            case_id=data.get("case_id", ""),
            evaluation_type=EvaluationType(data.get("evaluation_type", "intent_classification")),
            scenario_type=ScenarioType(data.get("scenario_type", "single_turn")),
            input=data.get("input", {}),
            baseline=baseline,
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            weight=data.get("weight", 1.0),
        )


class JsonDatasetLoader:
    def load(self, path: str) -> EvaluationDataset:
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DatasetFormatError(f"Invalid JSON dataset: {e}")
        loader = GoldenDatasetLoader()
        return loader._parse_dataset(data, DatasetFormat.JSON)


class YamlDatasetLoader:
    def load(self, path: str) -> EvaluationDataset:
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise DatasetFormatError(f"Invalid YAML dataset: {e}")
        loader = GoldenDatasetLoader()
        return loader._parse_dataset(data, DatasetFormat.YAML)


class CsvDatasetLoader:
    def load(self, path: str) -> EvaluationDataset:
        if not os.path.exists(path):
            raise DatasetLoadError(f"CSV dataset not found: {path}")
        cases: list[EvaluationCase] = []
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    case = self._row_to_case(row)
                    cases.append(case)
        except csv.Error as e:
            raise DatasetFormatError(f"Invalid CSV dataset: {e}")
        return EvaluationDataset(
            dataset_id=os.path.splitext(os.path.basename(path))[0],
            name=os.path.basename(path),
            format=DatasetFormat.CSV,
            cases=cases,
        )

    def _row_to_case(self, row: dict[str, str]) -> EvaluationCase:
        return EvaluationCase(
            case_id=row.get("case_id", ""),
            evaluation_type=EvaluationType(row.get("evaluation_type", "intent_classification")),
            scenario_type=ScenarioType(row.get("scenario_type", "single_turn")),
            input=json.loads(row.get("input", "{}")),
            baseline=Baseline(
                golden_answer=row.get("golden_answer", ""),
                expected_intent=row.get("expected_intent", ""),
                expected_workflow=row.get("expected_workflow", ""),
            ),
            weight=float(row.get("weight", "1.0")),
        )


class VersionedDatasetLoader:
    def __init__(self) -> None:
        self._inner = GoldenDatasetLoader()

    def load(self, path: str, version: str = "") -> EvaluationDataset:
        dataset = self._inner.load(path)
        base_dir = os.path.dirname(path)
        base_name = os.path.splitext(os.path.basename(path))[0]
        version_file = f"{base_name}_{version}.json" if version else ""
        version_path = os.path.join(base_dir, version_file) if version_file else ""
        if version and os.path.exists(version_path):
            version_data = self._inner.load(version_path)
            dataset.cases.extend(version_data.cases)
            dataset.version = version
        elif version:
            raise DatasetVersionError(f"Version {version} not found for dataset {path}")
        return dataset


class ScenarioDatasetLoader:
    def __init__(self) -> None:
        self._inner = GoldenDatasetLoader()

    def load(self, path: str, scenario_type: ScenarioType | None = None) -> EvaluationDataset:
        dataset = self._inner.load(path)
        if scenario_type:
            filtered_cases = [c for c in dataset.cases if c.scenario_type == scenario_type]
            dataset.cases = filtered_cases
            dataset.scenarios = [s for s in dataset.scenarios if s.scenario_type == scenario_type]
        return dataset


class RegressionDatasetLoader:
    def __init__(self) -> None:
        self._inner = GoldenDatasetLoader()

    def load(self, previous_run_path: str, current_dataset_path: str) -> EvaluationDataset:
        prev = self._inner.load(previous_run_path)
        curr = self._inner.load(current_dataset_path)
        prev_ids = {c.case_id for c in prev.cases}
        regression_cases = [c for c in curr.cases if c.case_id in prev_ids]
        new_cases = [c for c in curr.cases if c.case_id not in prev_ids]
        dataset = EvaluationDataset(
            dataset_id="regression",
            name="Regression Dataset",
            format=DatasetFormat.REGRESSION,
        )
        dataset.cases = regression_cases + new_cases
        return dataset


class ScenarioLoader:
    def __init__(self) -> None:
        self._golden_loader = GoldenDatasetLoader()
        self._scenario_dir: str = ""

    def set_scenario_dir(self, directory: str) -> None:
        self._scenario_dir = directory

    def load_scenario(self, scenario_type: ScenarioType, path: str = "") -> EvaluationScenario:
        if not path and self._scenario_dir:
            path = os.path.join(self._scenario_dir, f"{scenario_type.value}.json")
        if not os.path.exists(path):
            raise ScenarioLoadError(f"Scenario file not found: {path}")
        dataset = self._golden_loader.load(path)
        matching = [s for s in dataset.scenarios if s.scenario_type == scenario_type]
        if matching:
            return matching[0]
        scenario = EvaluationScenario(
            scenario_id=f"{scenario_type.value}_scenario",
            scenario_type=scenario_type,
            name=scenario_type.value.replace("_", " ").title(),
        )
        scenario.cases = [c for c in dataset.cases if c.scenario_type == scenario_type]
        return scenario

    def load_all_scenarios(self, directory: str = "") -> list[EvaluationScenario]:
        base = directory or self._scenario_dir
        if not base or not os.path.isdir(base):
            raise ScenarioLoadError(f"Scenario directory not found: {base}")
        scenarios: list[EvaluationScenario] = []
        for fname in os.listdir(base):
            if fname.endswith(".json"):
                fpath = os.path.join(base, fname)
                try:
                    dataset = self._golden_loader.load(fpath)
                    scenarios.extend(dataset.scenarios)
                except Exception:
                    continue
        return scenarios


class DatasetLoaderFactory:
    def __init__(self) -> None:
        self._golden = GoldenDatasetLoader()
        self._json = JsonDatasetLoader()
        self._yaml = YamlDatasetLoader()
        self._csv = CsvDatasetLoader()
        self._versioned = VersionedDatasetLoader()
        self._scenario = ScenarioDatasetLoader()
        self._regression = RegressionDatasetLoader()

    def get_loader(self, fmt: DatasetFormat):
        loaders = {
            DatasetFormat.GOLDEN: self._golden,
            DatasetFormat.JSON: self._json,
            DatasetFormat.YAML: self._yaml,
            DatasetFormat.CSV: self._csv,
            DatasetFormat.VERSIONED: self._versioned,
            DatasetFormat.SCENARIO: self._scenario,
            DatasetFormat.REGRESSION: self._regression,
        }
        loader = loaders.get(fmt)
        if loader is None:
            raise DatasetFormatError(f"Unsupported dataset format: {fmt}")
        return loader

    def load_dataset(self, path: str, fmt: DatasetFormat = DatasetFormat.GOLDEN, **kwargs: Any) -> EvaluationDataset:
        loader = self.get_loader(fmt)
        if fmt == DatasetFormat.VERSIONED:
            return loader.load(path, version=kwargs.get("version", ""))
        if fmt == DatasetFormat.SCENARIO:
            return loader.load(path, scenario_type=kwargs.get("scenario_type"))
        if fmt == DatasetFormat.REGRESSION:
            return loader.load(kwargs.get("previous_run_path", ""), path)
        return loader.load(path)
