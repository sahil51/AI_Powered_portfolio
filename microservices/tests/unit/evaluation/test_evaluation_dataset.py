import json
import os
import tempfile

import pytest
import yaml

from evaluation.dataset import (
    CsvDatasetLoader,
    DatasetLoaderFactory,
    GoldenDatasetLoader,
    JsonDatasetLoader,
    RegressionDatasetLoader,
    ScenarioDatasetLoader,
    ScenarioLoader,
    VersionedDatasetLoader,
    YamlDatasetLoader,
)
from evaluation.exceptions import (
    DatasetFormatError,
    DatasetLoadError,
    DatasetVersionError,
    GoldenDataNotFoundError,
    ScenarioLoadError,
)
from evaluation.models import DatasetFormat, EvaluationType, ScenarioType


class TestGoldenDatasetLoader:
    def setup_method(self):
        self.loader = GoldenDatasetLoader()

    def test_load_file_not_found(self):
        with pytest.raises(GoldenDataNotFoundError):
            self.loader.load("nonexistent.json")

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            path = f.name
        try:
            with pytest.raises(DatasetFormatError):
                self.loader.load(path)
        finally:
            os.unlink(path)

    def test_load_valid_golden(self):
        data = {
            "dataset_id": "golden_test",
            "name": "Golden Test",
            "cases": [
                {
                    "case_id": "c1",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {"query": "hello"},
                    "baseline": {"expected_intent": "greeting"},
                }
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.loader.load(path)
            assert dataset.dataset_id == "golden_test"
            assert len(dataset.cases) == 1
            assert dataset.cases[0].case_id == "c1"
            assert dataset.cases[0].evaluation_type == EvaluationType.INTENT_CLASSIFICATION
        finally:
            os.unlink(path)

    def test_load_with_scenarios(self):
        data = {
            "dataset_id": "scenario_test",
            "name": "Scenario Test",
            "scenarios": [
                {
                    "scenario_id": "s1",
                    "scenario_type": "single_turn",
                    "name": "Basic",
                    "cases": [
                        {
                            "case_id": "c1",
                            "evaluation_type": "intent_classification",
                            "scenario_type": "single_turn",
                            "input": {"query": "hi"},
                            "baseline": {"expected_intent": "greeting"},
                        }
                    ],
                }
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.loader.load(path)
            assert len(dataset.scenarios) == 1
            assert len(dataset.cases) == 1
            assert dataset.scenarios[0].scenario_id == "s1"
        finally:
            os.unlink(path)

    def test_parse_case_unknown_type_raises_error(self):
        loader = GoldenDatasetLoader()
        with pytest.raises(ValueError):
            loader._parse_case({
                "case_id": "c1",
                "evaluation_type": "unknown_type",
                "scenario_type": "single_turn",
                "input": {},
                "baseline": {},
            })

    def test_empty_cases_and_scenarios(self):
        data = {"dataset_id": "empty", "name": "Empty"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.loader.load(path)
            assert len(dataset.cases) == 0
            assert len(dataset.scenarios) == 0
        finally:
            os.unlink(path)


class TestJsonDatasetLoader:
    def test_load_valid(self):
        data = {"dataset_id": "json_test", "name": "JSON Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = JsonDatasetLoader()
            dataset = loader.load(path)
            assert dataset.dataset_id == "json_test"
            assert dataset.format == DatasetFormat.JSON
        finally:
            os.unlink(path)

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json")
            path = f.name
        try:
            loader = JsonDatasetLoader()
            with pytest.raises(DatasetFormatError):
                loader.load(path)
        finally:
            os.unlink(path)


class TestYamlDatasetLoader:
    def test_load_valid(self):
        data = {"dataset_id": "yaml_test", "name": "YAML Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = f.name
        try:
            loader = YamlDatasetLoader()
            dataset = loader.load(path)
            assert dataset.dataset_id == "yaml_test"
            assert dataset.format == DatasetFormat.YAML
        finally:
            os.unlink(path)

    def test_load_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(": invalid yaml :")
            path = f.name
        try:
            loader = YamlDatasetLoader()
            with pytest.raises(DatasetFormatError):
                loader.load(path)
        finally:
            os.unlink(path)


class TestCsvDatasetLoader:
    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("case_id,evaluation_type,scenario_type,input,golden_answer,expected_intent,weight\n")
            f.write("c1,intent_classification,single_turn,\"{\"\"query\"\": \"\"hi\"\"}\",hello,greeting,1.0\n")
            path = f.name
        try:
            loader = CsvDatasetLoader()
            dataset = loader.load(path)
            assert len(dataset.cases) == 1
            assert dataset.cases[0].case_id == "c1"
            assert dataset.cases[0].evaluation_type == EvaluationType.INTENT_CLASSIFICATION
        finally:
            os.unlink(path)

    def test_load_file_not_found(self):
        loader = CsvDatasetLoader()
        with pytest.raises(DatasetLoadError):
            loader.load("nonexistent.csv")

    def test_load_invalid_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("case_id\nc1\nc2")
            path = f.name
        try:
            loader = CsvDatasetLoader()
            dataset = loader.load(path)
            assert len(dataset.cases) == 2
        finally:
            os.unlink(path)


class TestVersionedDatasetLoader:
    def test_load_without_version(self):
        data = {"dataset_id": "ver_test", "name": "Version Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = VersionedDatasetLoader()
            dataset = loader.load(path)
            assert dataset.dataset_id == "ver_test"
        finally:
            os.unlink(path)

    def test_load_with_nonexistent_version(self):
        data = {"dataset_id": "ver_test", "name": "Version Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = VersionedDatasetLoader()
            with pytest.raises(DatasetVersionError):
                loader.load(path, version="v99")
        finally:
            os.unlink(path)

    def test_load_with_existing_version(self):
        dir_path = tempfile.mkdtemp()
        base_path = os.path.join(dir_path, "dataset.json")
        version_path = os.path.join(dir_path, "dataset_v2.json")
        base_data = {"dataset_id": "base", "name": "Base", "cases": []}
        version_data = {
            "dataset_id": "base",
            "name": "Base",
            "cases": [{
                "case_id": "v2_case",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {},
                "baseline": {},
            }],
        }
        with open(base_path, "w") as f:
            json.dump(base_data, f)
        with open(version_path, "w") as f:
            json.dump(version_data, f)
        try:
            loader = VersionedDatasetLoader()
            dataset = loader.load(base_path, version="v2")
            assert dataset.version == "v2"
            assert len(dataset.cases) == 1
            assert dataset.cases[0].case_id == "v2_case"
        finally:
            os.unlink(base_path)
            os.unlink(version_path)
            os.rmdir(dir_path)


class TestScenarioDatasetLoader:
    def test_load_without_filter(self):
        data = {
            "dataset_id": "sc_test",
            "name": "Scenario Test",
            "cases": [
                {
                    "case_id": "c1",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {},
                    "baseline": {},
                },
                {
                    "case_id": "c2",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "multi_turn",
                    "input": {},
                    "baseline": {},
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = ScenarioDatasetLoader()
            dataset = loader.load(path)
            assert len(dataset.cases) == 2
        finally:
            os.unlink(path)

    def test_load_with_filter(self):
        data = {
            "dataset_id": "sc_test",
            "name": "Scenario Test",
            "cases": [
                {
                    "case_id": "c1",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {},
                    "baseline": {},
                },
                {
                    "case_id": "c2",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "multi_turn",
                    "input": {},
                    "baseline": {},
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = ScenarioDatasetLoader()
            dataset = loader.load(path, scenario_type=ScenarioType.SINGLE_TURN)
            assert len(dataset.cases) == 1
            assert dataset.cases[0].case_id == "c1"
        finally:
            os.unlink(path)


class TestRegressionDatasetLoader:
    def test_load_regression(self):
        dir_path = tempfile.mkdtemp()
        prev_path = os.path.join(dir_path, "prev.json")
        curr_path = os.path.join(dir_path, "curr.json")
        prev_data = {
            "dataset_id": "prev",
            "name": "Previous",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {},
                "baseline": {},
            }],
        }
        curr_data = {
            "dataset_id": "curr",
            "name": "Current",
            "cases": [
                {
                    "case_id": "c1",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {},
                    "baseline": {},
                },
                {
                    "case_id": "c2",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {},
                    "baseline": {},
                },
            ],
        }
        with open(prev_path, "w") as f:
            json.dump(prev_data, f)
        with open(curr_path, "w") as f:
            json.dump(curr_data, f)
        try:
            loader = RegressionDatasetLoader()
            dataset = loader.load(prev_path, curr_path)
            assert len(dataset.cases) == 2
            assert dataset.format == DatasetFormat.REGRESSION
        finally:
            os.unlink(prev_path)
            os.unlink(curr_path)
            os.rmdir(dir_path)


class TestScenarioLoader:
    def test_load_scenario_no_path(self):
        loader = ScenarioLoader()
        with pytest.raises(ScenarioLoadError):
            loader.load_scenario(ScenarioType.SINGLE_TURN)

    def test_load_scenario_from_path(self):
        data = {
            "dataset_id": "test",
            "name": "Test",
            "scenarios": [{
                "scenario_id": "s1",
                "scenario_type": "single_turn",
                "name": "Basic",
                "cases": [],
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = ScenarioLoader()
            scenario = loader.load_scenario(ScenarioType.SINGLE_TURN, path)
            assert scenario.scenario_id == "s1"
        finally:
            os.unlink(path)

    def test_load_scenario_fallback_from_dir(self):
        dir_path = tempfile.mkdtemp()
        file_path = os.path.join(dir_path, "single_turn.json")
        data = {
            "dataset_id": "test",
            "name": "Test",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {},
                "baseline": {},
            }],
        }
        with open(file_path, "w") as f:
            json.dump(data, f)
        try:
            loader = ScenarioLoader()
            loader.set_scenario_dir(dir_path)
            scenario = loader.load_scenario(ScenarioType.SINGLE_TURN)
            assert scenario.scenario_id == "single_turn_scenario"
            assert len(scenario.cases) == 1
        finally:
            os.unlink(file_path)
            os.rmdir(dir_path)

    def test_load_all_scenarios(self):
        dir_path = tempfile.mkdtemp()
        file1 = os.path.join(dir_path, "s1.json")
        file2 = os.path.join(dir_path, "s2.json")
        data1 = {
            "dataset_id": "ds1",
            "name": "DS1",
            "scenarios": [{"scenario_id": "s1", "scenario_type": "single_turn", "name": "Basic", "cases": []}],
        }
        data2 = {
            "dataset_id": "ds2",
            "name": "DS2",
            "scenarios": [{"scenario_id": "s2", "scenario_type": "multi_turn", "name": "Multi", "cases": []}],
        }
        with open(file1, "w") as f:
            json.dump(data1, f)
        with open(file2, "w") as f:
            json.dump(data2, f)
        try:
            loader = ScenarioLoader()
            scenarios = loader.load_all_scenarios(dir_path)
            assert len(scenarios) == 2
        finally:
            os.unlink(file1)
            os.unlink(file2)
            os.rmdir(dir_path)

    def test_load_all_scenarios_directory_not_found(self):
        loader = ScenarioLoader()
        with pytest.raises(ScenarioLoadError):
            loader.load_all_scenarios("nonexistent_dir")


class TestDatasetLoaderFactory:
    def test_get_loader_golden(self):
        factory = DatasetLoaderFactory()
        loader = factory.get_loader(DatasetFormat.GOLDEN)
        assert isinstance(loader, GoldenDatasetLoader)

    def test_get_loader_json(self):
        factory = DatasetLoaderFactory()
        loader = factory.get_loader(DatasetFormat.JSON)
        assert isinstance(loader, JsonDatasetLoader)

    def test_get_loader_yaml(self):
        factory = DatasetLoaderFactory()
        loader = factory.get_loader(DatasetFormat.YAML)
        assert isinstance(loader, YamlDatasetLoader)

    def test_get_loader_csv(self):
        factory = DatasetLoaderFactory()
        loader = factory.get_loader(DatasetFormat.CSV)
        assert isinstance(loader, CsvDatasetLoader)

    def test_get_loader_unsupported(self):
        factory = DatasetLoaderFactory()
        with pytest.raises(DatasetFormatError):
            factory.get_loader("unsupported")

    def test_load_dataset_golden(self):
        data = {"dataset_id": "factory_test", "name": "Factory Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            factory = DatasetLoaderFactory()
            dataset = factory.load_dataset(path, DatasetFormat.GOLDEN)
            assert dataset.dataset_id == "factory_test"
        finally:
            os.unlink(path)

    def test_load_dataset_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("case_id,evaluation_type,scenario_type,input,golden_answer,expected_intent\n")
            f.write("c1,intent_classification,single_turn,{},hello,greeting\n")
            path = f.name
        try:
            factory = DatasetLoaderFactory()
            dataset = factory.load_dataset(path, DatasetFormat.CSV)
            assert len(dataset.cases) == 1
        finally:
            os.unlink(path)
