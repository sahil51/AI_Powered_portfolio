import json
import os
import tempfile

import pytest

from evaluation.exceptions import EvaluationConfigurationError
from evaluation.manager import EvaluationManager
from evaluation.models import (
    DatasetFormat,
    EvaluationRunConfiguration,
    EvaluationStatus,
    ReportFormat,
    ScenarioType,
)


class TestEvaluationManager:
    def setup_method(self):
        self.manager = EvaluationManager()

    @pytest.mark.asyncio
    async def test_initial_state(self):
        assert self.manager.initialized is False
        assert self.manager.last_report is None
        assert len(self.manager.registry.list_registered()) == 0

    @pytest.mark.asyncio
    async def test_initialize(self):
        await self.manager.initialize()
        assert self.manager.initialized is True
        assert self.manager.registry.count() == 11
        assert self.manager.health_checker.health.evaluators_registered == 11

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        await self.manager.initialize()
        await self.manager.initialize()
        assert self.manager.initialized is True
        assert self.manager.registry.count() == 11

    @pytest.mark.asyncio
    async def test_runner_property_before_initialize(self):
        with pytest.raises(EvaluationConfigurationError, match="not initialized"):
            _ = self.manager.runner

    @pytest.mark.asyncio
    async def test_runner_property_after_initialize(self):
        await self.manager.initialize()
        assert self.manager.runner is not None

    @pytest.mark.asyncio
    async def test_shutdown(self):
        await self.manager.initialize()
        await self.manager.shutdown()
        assert self.manager.initialized is False
        assert self.manager.registry.count() == 0
        assert self.manager.health_checker.health.healthy is True

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        await self.manager.shutdown()
        assert self.manager.initialized is False

    def test_load_golden_dataset(self):
        data = {
            "dataset_id": "golden_test",
            "name": "Golden Test",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {"query": "hello"},
                "baseline": {"expected_intent": "greeting"},
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_golden_dataset(path)
            assert dataset.dataset_id == "golden_test"
            assert len(dataset.cases) == 1
        finally:
            os.unlink(path)

    def test_load_json_dataset(self):
        data = {"dataset_id": "json_test", "name": "JSON Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_json_dataset(path)
            assert dataset.format == DatasetFormat.JSON
        finally:
            os.unlink(path)

    def test_load_yaml_dataset(self):
        import yaml
        data = {"dataset_id": "yaml_test", "name": "YAML Test", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_yaml_dataset(path)
            assert dataset.format == DatasetFormat.YAML
        finally:
            os.unlink(path)

    def test_load_csv_dataset(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("case_id,evaluation_type,scenario_type,input,golden_answer,expected_intent\n")
            f.write("c1,intent_classification,single_turn,{},hello,greeting\n")
            path = f.name
        try:
            dataset = self.manager.load_csv_dataset(path)
            assert dataset.format == DatasetFormat.CSV
            assert len(dataset.cases) == 1
        finally:
            os.unlink(path)

    def test_get_dataset(self):
        data = {"dataset_id": "ds1", "name": "DS1", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            self.manager.load_golden_dataset(path)
            dataset = self.manager.get_dataset("ds1")
            assert dataset is not None
            assert dataset.name == "DS1"
        finally:
            os.unlink(path)

    def test_get_dataset_not_found(self):
        assert self.manager.get_dataset("nonexistent") is None

    def test_get_datasets(self):
        data = {"dataset_id": "ds1", "name": "DS1", "cases": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            self.manager.load_golden_dataset(path)
            datasets = self.manager.get_datasets()
            assert "ds1" in datasets
        finally:
            os.unlink(path)

    def test_health_report(self):
        report = self.manager.health_report()
        assert "healthy" in report
        assert report["healthy"] is True

    def test_evaluation_report_before_initialization(self):
        report = self.manager.evaluation_report()
        assert report["initialized"] is False
        assert report["evaluators_registered"] == 0

    @pytest.mark.asyncio
    async def test_evaluation_report_after_initialization(self):
        await self.manager.initialize()
        report = self.manager.evaluation_report()
        assert report["initialized"] is True
        assert report["evaluators_registered"] == 11

    @pytest.mark.asyncio
    async def test_run_evaluation(self):
        await self.manager.initialize()
        data = {
            "dataset_id": "test_run",
            "name": "Test Run",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {"query": "hello"},
                "baseline": {"expected_intent": "hello"},
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_golden_dataset(path)
            report = await self.manager.run_evaluation(dataset)
            assert report.status == EvaluationStatus.COMPLETED
            assert len(report.results) == 1
            assert self.manager.last_report is not None
            assert self.manager.last_report.report_id == report.report_id
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_run_evaluation_on_dataset(self):
        await self.manager.initialize()
        data = {
            "dataset_id": "test_run_on",
            "name": "Test Run On",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {"query": "hi"},
                "baseline": {"expected_intent": "hi"},
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            self.manager.load_golden_dataset(path)
            report = await self.manager.run_evaluation_on_dataset("test_run_on")
            assert report.status == EvaluationStatus.COMPLETED
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_run_evaluation_on_dataset_not_found(self):
        await self.manager.initialize()
        with pytest.raises(EvaluationConfigurationError, match="not found"):
            await self.manager.run_evaluation_on_dataset("nonexistent")

    @pytest.mark.asyncio
    async def test_generate_report(self):
        await self.manager.initialize()
        data = {
            "dataset_id": "gen_report",
            "name": "Gen Report",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {"query": "hello"},
                "baseline": {"expected_intent": "hello"},
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_golden_dataset(path)
            report = await self.manager.run_evaluation(dataset)
            output = self.manager.generate_report(report, ReportFormat.JSON)
            parsed = json.loads(output)
            assert parsed["report_id"] == report.report_id
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_compare_reports(self):
        await self.manager.initialize()
        data = {
            "dataset_id": "compare",
            "name": "Compare",
            "cases": [{
                "case_id": "c1",
                "evaluation_type": "intent_classification",
                "scenario_type": "single_turn",
                "input": {"query": "hello"},
                "baseline": {"expected_intent": "hello"},
            }],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_golden_dataset(path)
            report1 = await self.manager.run_evaluation(dataset)
            report2 = await self.manager.run_evaluation(dataset)
            result = await self.manager.compare_reports(report1, report2)
            assert "comparison" in result
        finally:
            os.unlink(path)

    def test_load_regression_dataset(self):
        import tempfile
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
                "baseline": {"expected_intent": "hi"},
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
                    "baseline": {"expected_intent": "hi"},
                },
                {
                    "case_id": "c2",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {},
                    "baseline": {"expected_intent": "hello"},
                },
            ],
        }
        with open(prev_path, "w") as f:
            json.dump(prev_data, f)
        with open(curr_path, "w") as f:
            json.dump(curr_data, f)
        try:
            dataset = self.manager.load_regression_dataset(prev_path, curr_path)
            assert dataset.format == DatasetFormat.REGRESSION
            assert len(dataset.cases) == 2
        finally:
            os.unlink(prev_path)
            os.unlink(curr_path)
            os.rmdir(dir_path)

    @pytest.mark.asyncio
    async def test_run_evaluation_with_config(self):
        await self.manager.initialize()
        data = {
            "dataset_id": "config_test",
            "name": "Config Test",
            "cases": [
                {
                    "case_id": "c1",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "single_turn",
                    "input": {"query": "hello"},
                    "baseline": {"expected_intent": "hello"},
                },
                {
                    "case_id": "c2",
                    "evaluation_type": "intent_classification",
                    "scenario_type": "multi_turn",
                    "input": {"query": "hi"},
                    "baseline": {"expected_intent": "hi"},
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            dataset = self.manager.load_golden_dataset(path)
            config = EvaluationRunConfiguration(scenario_types=[ScenarioType.MULTI_TURN])
            report = await self.manager.run_evaluation(dataset, config)
            assert len(report.results) == 1
            assert report.results[0].case_id == "c2"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_validator_property(self):
        assert self.manager.validator is not None
