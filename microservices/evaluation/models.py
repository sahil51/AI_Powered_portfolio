from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvaluationType(str, Enum):
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"
    CONFIRMATION_RESOLUTION = "confirmation_resolution"
    CONVERSATION_MEMORY = "conversation_memory"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    HYBRID_SEARCH = "hybrid_search"
    CONTEXT_BUILDER = "context_builder"
    PROMPT_RENDERING = "prompt_rendering"
    MEETING_AGENT = "meeting_agent"
    WORKFLOW_REQUEST = "workflow_request"
    RESPONSE_VALIDATION = "response_validation"


class ScenarioType(str, Enum):
    SINGLE_TURN = "single_turn"
    MULTI_TURN = "multi_turn"
    LONG_CONVERSATION = "long_conversation"
    MEETING_SCHEDULE = "meeting_schedule"
    MEETING_RESCHEDULE = "meeting_reschedule"
    MEETING_CANCEL = "meeting_cancel"
    REMINDER = "reminder"
    KNOWLEDGE_QUESTIONS = "knowledge_questions"
    FALLBACK = "fallback"
    UNKNOWN_INTENT = "unknown_intent"
    AMBIGUOUS_INPUT = "ambiguous_input"
    MEMORY_RECALL = "memory_recall"
    KNOWLEDGE_RECALL = "knowledge_recall"
    WORKFLOW_EXECUTION = "workflow_execution"


class DatasetFormat(str, Enum):
    GOLDEN = "golden"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    VERSIONED = "versioned"
    SCENARIO = "scenario"
    REGRESSION = "regression"


class MetricType(str, Enum):
    INTENT_ACCURACY = "intent_accuracy"
    ENTITY_ACCURACY = "entity_accuracy"
    CONFIRMATION_ACCURACY = "confirmation_accuracy"
    MEMORY_RECALL = "memory_recall"
    KNOWLEDGE_PRECISION = "knowledge_precision"
    KNOWLEDGE_RECALL = "knowledge_recall"
    MRR = "mrr"
    NDCG = "ndcg"
    CONTEXT_QUALITY = "context_quality"
    PROMPT_QUALITY = "prompt_quality"
    HALLUCINATION_RATE = "hallucination_rate"
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    EMBEDDING_COST = "embedding_cost"
    PROVIDER_COST = "provider_cost"
    WORKFLOW_SUCCESS_RATE = "workflow_success_rate"
    RETRY_RATE = "retry_rate"
    FAILURE_RATE = "failure_rate"


class ReportFormat(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    TREND = "trend"
    COMPARISON = "comparison"
    REGRESSION = "regression"


class EvaluationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class Baseline:
    golden_answer: str = ""
    expected_output: str = ""
    expected_entities: list[dict[str, str]] = field(default_factory=list)
    expected_intent: str = ""
    expected_workflow: str = ""
    expected_missing_fields: list[str] = field(default_factory=list)
    expected_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationCase:
    case_id: str
    evaluation_type: EvaluationType
    scenario_type: ScenarioType
    input: dict[str, Any]
    baseline: Baseline
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class EvaluationScenario:
    scenario_id: str
    scenario_type: ScenarioType
    name: str
    description: str = ""
    cases: list[EvaluationCase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationDataset:
    dataset_id: str
    name: str
    format: DatasetFormat
    version: str = "1.0.0"
    scenarios: list[EvaluationScenario] = field(default_factory=list)
    cases: list[EvaluationCase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationOutput:
    predicted_value: Any = None
    predicted_intent: str = ""
    predicted_entities: list[dict[str, str]] = field(default_factory=list)
    predicted_workflow: str = ""
    confidence: float = 0.0
    latency_ms: float = 0.0
    token_count: int = 0
    provider: str = ""
    model: str = ""
    raw_response: str = ""
    error: str = ""


@dataclass
class EvaluationResult:
    case_id: str
    evaluation_type: EvaluationType
    scenario_type: ScenarioType
    output: EvaluationOutput
    baseline: Baseline
    passed: bool = False
    score: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class EvaluationMetrics:
    evaluation_type: EvaluationType
    intent_accuracy: float = 0.0
    entity_accuracy: float = 0.0
    confirmation_accuracy: float = 0.0
    memory_recall: float = 0.0
    knowledge_precision: float = 0.0
    knowledge_recall: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    context_quality: float = 0.0
    prompt_quality: float = 0.0
    hallucination_rate: float = 0.0
    latency_ms: float = 0.0
    token_usage: int = 0
    embedding_cost: float = 0.0
    provider_cost: float = 0.0
    workflow_success_rate: float = 0.0
    retry_rate: float = 0.0
    failure_rate: float = 0.0


@dataclass
class EvaluationStatistics:
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    average_score: float = 0.0
    median_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    std_dev: float = 0.0
    p95_score: float = 0.0
    p99_score: float = 0.0
    average_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    per_type: dict[str, float] = field(default_factory=dict)
    per_scenario: dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    report_id: str
    dataset_name: str
    timestamp: float = 0.0
    status: EvaluationStatus = EvaluationStatus.PENDING
    metrics: EvaluationMetrics | None = None
    statistics: EvaluationStatistics | None = None
    results: list[EvaluationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    label: str
    scores: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    improvement: float = 0.0


@dataclass
class EvaluationComparison:
    baseline_label: str
    comparison_label: str
    results: list[ComparisonResult] = field(default_factory=list)
    overall_improvement: float = 0.0


@dataclass
class EvaluationHealth:
    healthy: bool = True
    datasets_loaded: int = 0
    evaluators_registered: int = 0
    last_run_timestamp: float = 0.0
    last_run_status: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class EvaluationRunConfiguration:
    evaluation_types: list[EvaluationType] = field(default_factory=list)
    scenario_types: list[ScenarioType] = field(default_factory=list)
    dataset_ids: list[str] = field(default_factory=list)
    max_cases: int = 0
    fail_fast: bool = False
    parallel: bool = False
    timeout_seconds: float = 300.0
    include_metrics: list[MetricType] = field(default_factory=list)
    report_formats: list[ReportFormat] = field(default_factory=list)
