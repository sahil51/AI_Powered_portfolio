from evaluation.health import EvaluationHealthChecker
from evaluation.models import EvaluationHealth, EvaluationStatus


class TestEvaluationHealthChecker:
    def setup_method(self):
        self.checker = EvaluationHealthChecker()

    def test_initial_health(self):
        health = self.checker.health
        assert health.healthy is True
        assert health.datasets_loaded == 0
        assert health.evaluators_registered == 0
        assert health.last_run_timestamp == 0.0
        assert health.last_run_status == ""
        assert health.errors == []

    def test_record_run(self):
        self.checker.record_run(EvaluationStatus.COMPLETED)
        health = self.checker.health
        assert health.last_run_status == "completed"
        assert health.last_run_timestamp > 0

    def test_record_run_failed(self):
        self.checker.record_run(EvaluationStatus.FAILED)
        assert self.checker.health.last_run_status == "failed"

    def test_record_error(self):
        self.checker.record_error("Something went wrong")
        health = self.checker.health
        assert health.healthy is False
        assert len(health.errors) == 1
        assert health.errors[0] == "Something went wrong"

    def test_record_multiple_errors(self):
        self.checker.record_error("Error 1")
        self.checker.record_error("Error 2")
        assert len(self.checker.health.errors) == 2
        assert self.checker.health.healthy is False

    def test_set_datasets_loaded(self):
        self.checker.set_datasets_loaded(5)
        assert self.checker.health.datasets_loaded == 5

    def test_set_evaluators_registered(self):
        self.checker.set_evaluators_registered(10)
        assert self.checker.health.evaluators_registered == 10

    def test_check(self):
        self.checker.set_datasets_loaded(3)
        self.checker.set_evaluators_registered(7)
        self.checker.record_run(EvaluationStatus.COMPLETED)
        self.checker.record_error("minor issue")
        result = self.checker.check()
        assert result["healthy"] is False
        assert result["datasets_loaded"] == 3
        assert result["evaluators_registered"] == 7
        assert result["last_run_status"] == "completed"
        assert len(result["errors"]) == 1

    def test_check_healthy(self):
        result = self.checker.check()
        assert result["healthy"] is True
        assert result["errors"] == []

    def test_reset(self):
        self.checker.record_error("error")
        self.checker.set_datasets_loaded(5)
        self.checker.set_evaluators_registered(10)
        self.checker.record_run(EvaluationStatus.COMPLETED)
        self.checker.reset()
        health = self.checker.health
        assert health.healthy is True
        assert health.datasets_loaded == 0
        assert health.evaluators_registered == 0
        assert health.last_run_timestamp == 0.0
        assert health.last_run_status == ""
        assert health.errors == []

    def test_health_property_immutable(self):
        health = self.checker.health
        assert isinstance(health, EvaluationHealth)

    def test_record_run_sequential(self):
        self.checker.record_run(EvaluationStatus.RUNNING)
        ts1 = self.checker.health.last_run_timestamp
        self.checker.record_run(EvaluationStatus.COMPLETED)
        ts2 = self.checker.health.last_run_timestamp
        assert ts2 >= ts1
        assert self.checker.health.last_run_status == "completed"

    def test_reset_after_error(self):
        self.checker.record_error("critical failure")
        assert self.checker.health.healthy is False
        self.checker.reset()
        assert self.checker.health.healthy is True
