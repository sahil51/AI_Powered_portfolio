
from evaluation.models import (
    Baseline,
    ComparisonResult,
    DatasetFormat,
    EvaluationCase,
    EvaluationComparison,
    EvaluationDataset,
    EvaluationHealth,
    EvaluationMetrics,
    EvaluationOutput,
    EvaluationReport,
    EvaluationResult,
    EvaluationRunConfiguration,
    EvaluationScenario,
    EvaluationStatistics,
    EvaluationStatus,
    EvaluationType,
    MetricType,
    ReportFormat,
    ScenarioType,
)


class TestEvaluationType:
    def test_values(self):
        assert EvaluationType.INTENT_CLASSIFICATION.value == "intent_classification"
        assert EvaluationType.ENTITY_EXTRACTION.value == "entity_extraction"
        assert EvaluationType.CONFIRMATION_RESOLUTION.value == "confirmation_resolution"
        assert EvaluationType.CONVERSATION_MEMORY.value == "conversation_memory"
        assert EvaluationType.KNOWLEDGE_RETRIEVAL.value == "knowledge_retrieval"
        assert EvaluationType.HYBRID_SEARCH.value == "hybrid_search"
        assert EvaluationType.CONTEXT_BUILDER.value == "context_builder"
        assert EvaluationType.PROMPT_RENDERING.value == "prompt_rendering"
        assert EvaluationType.MEETING_AGENT.value == "meeting_agent"
        assert EvaluationType.WORKFLOW_REQUEST.value == "workflow_request"
        assert EvaluationType.RESPONSE_VALIDATION.value == "response_validation"

    def test_from_string(self):
        assert EvaluationType("intent_classification") == EvaluationType.INTENT_CLASSIFICATION
        assert EvaluationType("entity_extraction") == EvaluationType.ENTITY_EXTRACTION

    def test_members_count(self):
        assert len(EvaluationType) == 11


class TestScenarioType:
    def test_values(self):
        assert ScenarioType.SINGLE_TURN.value == "single_turn"
        assert ScenarioType.MULTI_TURN.value == "multi_turn"
        assert ScenarioType.WORKFLOW_EXECUTION.value == "workflow_execution"

    def test_from_string(self):
        assert ScenarioType("single_turn") == ScenarioType.SINGLE_TURN
        assert ScenarioType("memory_recall") == ScenarioType.MEMORY_RECALL

    def test_members_count(self):
        assert len(ScenarioType) == 14


class TestDatasetFormat:
    def test_values(self):
        assert DatasetFormat.GOLDEN.value == "golden"
        assert DatasetFormat.JSON.value == "json"
        assert DatasetFormat.YAML.value == "yaml"
        assert DatasetFormat.CSV.value == "csv"
        assert DatasetFormat.VERSIONED.value == "versioned"
        assert DatasetFormat.SCENARIO.value == "scenario"
        assert DatasetFormat.REGRESSION.value == "regression"

    def test_members_count(self):
        assert len(DatasetFormat) == 7


class TestMetricType:
    def test_values(self):
        assert MetricType.INTENT_ACCURACY.value == "intent_accuracy"
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.FAILURE_RATE.value == "failure_rate"

    def test_members_count(self):
        assert len(MetricType) == 18


class TestReportFormat:
    def test_values(self):
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.TREND.value == "trend"

    def test_members_count(self):
        assert len(ReportFormat) == 7


class TestEvaluationStatus:
    def test_values(self):
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.RUNNING.value == "running"
        assert EvaluationStatus.COMPLETED.value == "completed"
        assert EvaluationStatus.FAILED.value == "failed"
        assert EvaluationStatus.PARTIAL.value == "partial"

    def test_members_count(self):
        assert len(EvaluationStatus) == 5


class TestBaseline:
    def test_defaults(self):
        b = Baseline()
        assert b.golden_answer == ""
        assert b.expected_output == ""
        assert b.expected_entities == []
        assert b.expected_intent == ""
        assert b.expected_workflow == ""
        assert b.expected_missing_fields == []
        assert b.expected_context == {}

    def test_with_values(self):
        b = Baseline(
            golden_answer="yes",
            expected_output="Hello",
            expected_entities=[{"type": "person", "value": "John"}],
            expected_intent="greeting",
            expected_workflow="book_meeting",
            expected_missing_fields=["email"],
            expected_context={"time": "10am"},
        )
        assert b.golden_answer == "yes"
        assert len(b.expected_entities) == 1
        assert b.expected_intent == "greeting"


class TestEvaluationCase:
    def test_defaults(self):
        case = EvaluationCase(
            case_id="case-1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "hello"},
            baseline=Baseline(),
        )
        assert case.case_id == "case-1"
        assert case.metadata == {}
        assert case.tags == []
        assert case.weight == 1.0

    def test_with_all_fields(self):
        case = EvaluationCase(
            case_id="case-2",
            evaluation_type=EvaluationType.ENTITY_EXTRACTION,
            scenario_type=ScenarioType.MULTI_TURN,
            input={"entities": []},
            baseline=Baseline(expected_intent="test"),
            metadata={"source": "test"},
            tags=["smoke", "regression"],
            weight=2.0,
        )
        assert case.weight == 2.0
        assert "smoke" in case.tags
        assert case.metadata["source"] == "test"


class TestEvaluationScenario:
    def test_defaults(self):
        scenario = EvaluationScenario(
            scenario_id="sc-1",
            scenario_type=ScenarioType.SINGLE_TURN,
            name="Basic",
        )
        assert scenario.description == ""
        assert scenario.cases == []
        assert scenario.metadata == {}

    def test_with_cases(self):
        case = EvaluationCase(
            case_id="c-1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={},
            baseline=Baseline(),
        )
        scenario = EvaluationScenario(
            scenario_id="sc-1",
            scenario_type=ScenarioType.MULTI_TURN,
            name="Multi",
            description="Multi-turn test",
            cases=[case],
        )
        assert len(scenario.cases) == 1
        assert scenario.cases[0].case_id == "c-1"


class TestEvaluationDataset:
    def test_defaults(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Test",
            format=DatasetFormat.GOLDEN,
        )
        assert dataset.version == "1.0.0"
        assert dataset.scenarios == []
        assert dataset.cases == []
        assert dataset.metadata == {}

    def test_with_full_data(self):
        dataset = EvaluationDataset(
            dataset_id="ds-1",
            name="Full",
            format=DatasetFormat.JSON,
            version="2.0.0",
            scenarios=[],
            cases=[EvaluationCase(
                case_id="c-1",
                evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
                scenario_type=ScenarioType.SINGLE_TURN,
                input={},
                baseline=Baseline(),
            )],
            metadata={"author": "tester"},
        )
        assert len(dataset.cases) == 1
        assert dataset.version == "2.0.0"


class TestEvaluationOutput:
    def test_defaults(self):
        out = EvaluationOutput()
        assert out.predicted_value is None
        assert out.predicted_intent == ""
        assert out.predicted_entities == []
        assert out.confidence == 0.0
        assert out.latency_ms == 0.0
        assert out.token_count == 0
        assert out.error == ""

    def test_with_values(self):
        out = EvaluationOutput(
            predicted_value="result",
            predicted_intent="greet",
            confidence=0.95,
            latency_ms=100.0,
            token_count=50,
            provider="openai",
            model="gpt-4",
        )
        assert out.predicted_value == "result"
        assert out.confidence == 0.95


class TestEvaluationResult:
    def test_defaults(self):
        result = EvaluationResult(
            case_id="r-1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(),
            baseline=Baseline(),
        )
        assert result.passed is False
        assert result.score == 0.0
        assert result.metrics == {}
        assert result.errors == []
        assert result.timestamp == 0.0

    def test_with_values(self):
        result = EvaluationResult(
            case_id="r-1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            output=EvaluationOutput(confidence=0.9),
            baseline=Baseline(expected_intent="hi"),
            passed=True,
            score=0.9,
            metrics={"intent_match": 1.0},
            timestamp=12345.0,
        )
        assert result.passed is True
        assert result.score == 0.9
        assert result.metrics["intent_match"] == 1.0


class TestEvaluationMetrics:
    def test_defaults(self):
        m = EvaluationMetrics(evaluation_type=EvaluationType.INTENT_CLASSIFICATION)
        assert m.intent_accuracy == 0.0
        assert m.entity_accuracy == 0.0
        assert m.latency_ms == 0.0
        assert m.token_usage == 0
        assert m.hallucination_rate == 0.0

    def test_with_values(self):
        m = EvaluationMetrics(
            evaluation_type=EvaluationType.ENTITY_EXTRACTION,
            intent_accuracy=0.95,
            entity_accuracy=0.85,
            latency_ms=200.0,
            token_usage=1000,
            hallucination_rate=0.02,
        )
        assert m.intent_accuracy == 0.95
        assert m.entity_accuracy == 0.85
        assert m.token_usage == 1000


class TestEvaluationStatistics:
    def test_defaults(self):
        s = EvaluationStatistics()
        assert s.total_cases == 0
        assert s.passed == 0
        assert s.failed == 0
        assert s.pass_rate == 0.0
        assert s.average_score == 0.0
        assert s.per_type == {}
        assert s.per_scenario == {}

    def test_with_values(self):
        s = EvaluationStatistics(
            total_cases=100,
            passed=80,
            failed=20,
            pass_rate=0.8,
            average_score=0.75,
        )
        assert s.total_cases == 100
        assert s.pass_rate == 0.8


class TestEvaluationReport:
    def test_defaults(self):
        r = EvaluationReport(
            report_id="rep-1",
            dataset_name="Test",
        )
        assert r.status == EvaluationStatus.PENDING
        assert r.metrics is None
        assert r.statistics is None
        assert r.results == []
        assert r.errors == []

    def test_with_full_data(self):
        r = EvaluationReport(
            report_id="rep-1",
            dataset_name="Test",
            timestamp=1000.0,
            status=EvaluationStatus.COMPLETED,
            metrics=EvaluationMetrics(evaluation_type=EvaluationType.INTENT_CLASSIFICATION),
            statistics=EvaluationStatistics(total_cases=10),
            results=[],
            errors=[],
            metadata={"env": "prod"},
        )
        assert r.status == EvaluationStatus.COMPLETED
        assert r.statistics.total_cases == 10


class TestComparisonResult:
    def test_defaults(self):
        cr = ComparisonResult(label="accuracy")
        assert cr.scores == {}
        assert cr.metrics == {}
        assert cr.improvement == 0.0

    def test_with_values(self):
        cr = ComparisonResult(
            label="accuracy",
            scores={"baseline": 0.8, "comparison": 0.9},
            metrics={"delta": 0.1},
            improvement=0.125,
        )
        assert cr.label == "accuracy"
        assert cr.scores["baseline"] == 0.8
        assert cr.improvement == 0.125


class TestEvaluationComparison:
    def test_defaults(self):
        ec = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
        )
        assert ec.results == []
        assert ec.overall_improvement == 0.0

    def test_with_results(self):
        ec = EvaluationComparison(
            baseline_label="v1",
            comparison_label="v2",
            results=[ComparisonResult(label="acc", improvement=0.1)],
            overall_improvement=0.1,
        )
        assert len(ec.results) == 1
        assert ec.overall_improvement == 0.1


class TestEvaluationHealth:
    def test_defaults(self):
        h = EvaluationHealth()
        assert h.healthy is True
        assert h.datasets_loaded == 0
        assert h.evaluators_registered == 0
        assert h.last_run_timestamp == 0.0
        assert h.last_run_status == ""
        assert h.errors == []

    def test_with_values(self):
        h = EvaluationHealth(
            healthy=False,
            datasets_loaded=5,
            evaluators_registered=10,
            last_run_timestamp=123.0,
            last_run_status="completed",
            errors=["error1"],
        )
        assert h.healthy is False
        assert h.datasets_loaded == 5
        assert h.errors == ["error1"]


class TestEvaluationRunConfiguration:
    def test_defaults(self):
        cfg = EvaluationRunConfiguration()
        assert cfg.evaluation_types == []
        assert cfg.max_cases == 0
        assert cfg.fail_fast is False
        assert cfg.parallel is False
        assert cfg.timeout_seconds == 300.0

    def test_with_values(self):
        cfg = EvaluationRunConfiguration(
            evaluation_types=[EvaluationType.INTENT_CLASSIFICATION],
            scenario_types=[ScenarioType.SINGLE_TURN],
            max_cases=10,
            fail_fast=True,
            parallel=True,
            timeout_seconds=60.0,
        )
        assert len(cfg.evaluation_types) == 1
        assert cfg.fail_fast is True
        assert cfg.parallel is True
        assert cfg.timeout_seconds == 60.0
