import pytest

from evaluation.evaluators import (
    ConfirmationEvaluator,
    ContextBuilderEvaluator,
    EntityEvaluator,
    HybridSearchEvaluator,
    IntentEvaluator,
    KnowledgeRetrievalEvaluator,
    MeetingAgentEvaluator,
    MemoryEvaluator,
    PromptRenderingEvaluator,
    ResponseValidationEvaluator,
    WorkflowRequestEvaluator,
    register_default_evaluators,
)
from evaluation.models import Baseline, EvaluationCase, EvaluationType, ScenarioType
from evaluation.registry import EvaluationRegistry


class TestIntentEvaluator:
    @pytest.mark.asyncio
    async def test_exact_match(self):
        evaluator = IntentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "hello"},
            baseline=Baseline(expected_intent="hello"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.predicted_intent == "hello"

    @pytest.mark.asyncio
    async def test_no_match(self):
        evaluator = IntentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "hello"},
            baseline=Baseline(expected_intent="goodbye"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self):
        evaluator = IntentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "HELLO"},
            baseline=Baseline(expected_intent="hello"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0

    @pytest.mark.asyncio
    async def test_empty_expected_intent(self):
        evaluator = IntentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "hello"},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0

    @pytest.mark.asyncio
    async def test_positive_latency(self):
        evaluator = IntentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"query": "hi"},
            baseline=Baseline(expected_intent="hi"),
        )
        output = await evaluator.evaluate(case)
        assert output.latency_ms >= 0


class TestEntityEvaluator:
    @pytest.mark.asyncio
    async def test_with_entities(self):
        evaluator = EntityEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.ENTITY_EXTRACTION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"entities": [{"type": "person", "value": "John"}]},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert len(output.predicted_entities) == 1

    @pytest.mark.asyncio
    async def test_no_entities(self):
        evaluator = EntityEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.ENTITY_EXTRACTION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0
        assert output.predicted_entities == []


class TestConfirmationEvaluator:
    @pytest.mark.asyncio
    async def test_exact_match(self):
        evaluator = ConfirmationEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONFIRMATION_RESOLUTION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"resolution": "yes"},
            baseline=Baseline(golden_answer="yes"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.predicted_value == "yes"

    @pytest.mark.asyncio
    async def test_no_match(self):
        evaluator = ConfirmationEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONFIRMATION_RESOLUTION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"resolution": "no"},
            baseline=Baseline(golden_answer="yes"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestMemoryEvaluator:
    @pytest.mark.asyncio
    async def test_recall_match(self):
        evaluator = MemoryEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONVERSATION_MEMORY,
            scenario_type=ScenarioType.MEMORY_RECALL,
            input={"recalled": "John"},
            baseline=Baseline(expected_output="John"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0

    @pytest.mark.asyncio
    async def test_recall_mismatch(self):
        evaluator = MemoryEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONVERSATION_MEMORY,
            scenario_type=ScenarioType.MEMORY_RECALL,
            input={"recalled": "Jane"},
            baseline=Baseline(expected_output="John"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestKnowledgeRetrievalEvaluator:
    @pytest.mark.asyncio
    async def test_with_results(self):
        evaluator = KnowledgeRetrievalEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.KNOWLEDGE_RETRIEVAL,
            scenario_type=ScenarioType.KNOWLEDGE_QUESTIONS,
            input={"results": [{"id": "doc1"}], "token_count": 100},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.token_count == 100

    @pytest.mark.asyncio
    async def test_no_results(self):
        evaluator = KnowledgeRetrievalEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.KNOWLEDGE_RETRIEVAL,
            scenario_type=ScenarioType.KNOWLEDGE_QUESTIONS,
            input={},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0
        assert output.predicted_value == []


class TestHybridSearchEvaluator:
    @pytest.mark.asyncio
    async def test_with_hybrid_results(self):
        evaluator = HybridSearchEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.HYBRID_SEARCH,
            scenario_type=ScenarioType.KNOWLEDGE_QUESTIONS,
            input={"hybrid_results": [{"id": "doc1"}]},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0

    @pytest.mark.asyncio
    async def test_no_hybrid_results(self):
        evaluator = HybridSearchEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.HYBRID_SEARCH,
            scenario_type=ScenarioType.KNOWLEDGE_QUESTIONS,
            input={},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestContextBuilderEvaluator:
    @pytest.mark.asyncio
    async def test_context_match(self):
        evaluator = ContextBuilderEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONTEXT_BUILDER,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"context": {"key": "value"}},
            baseline=Baseline(expected_context={"key": "value"}),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0

    @pytest.mark.asyncio
    async def test_context_mismatch(self):
        evaluator = ContextBuilderEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.CONTEXT_BUILDER,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"context": {"key": "wrong"}},
            baseline=Baseline(expected_context={"key": "value"}),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestPromptRenderingEvaluator:
    @pytest.mark.asyncio
    async def test_rendered_match(self):
        evaluator = PromptRenderingEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.PROMPT_RENDERING,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"rendered": "Hello {{name}}", "token_count": 5},
            baseline=Baseline(expected_output="Hello {{name}}"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.token_count == 5

    @pytest.mark.asyncio
    async def test_rendered_mismatch(self):
        evaluator = PromptRenderingEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.PROMPT_RENDERING,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"rendered": "Hello"},
            baseline=Baseline(expected_output="Hi"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestMeetingAgentEvaluator:
    @pytest.mark.asyncio
    async def test_action_match(self):
        evaluator = MeetingAgentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.MEETING_AGENT,
            scenario_type=ScenarioType.MEETING_SCHEDULE,
            input={"action": "schedule"},
            baseline=Baseline(expected_workflow="schedule"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.predicted_workflow == "schedule"

    @pytest.mark.asyncio
    async def test_action_mismatch(self):
        evaluator = MeetingAgentEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.MEETING_AGENT,
            scenario_type=ScenarioType.MEETING_SCHEDULE,
            input={"action": "cancel"},
            baseline=Baseline(expected_workflow="schedule"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestWorkflowRequestEvaluator:
    @pytest.mark.asyncio
    async def test_workflow_match(self):
        evaluator = WorkflowRequestEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.WORKFLOW_REQUEST,
            scenario_type=ScenarioType.WORKFLOW_EXECUTION,
            input={"request": {"workflow_type": "book_meeting"}},
            baseline=Baseline(expected_workflow="book_meeting"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0
        assert output.predicted_workflow == "book_meeting"

    @pytest.mark.asyncio
    async def test_workflow_mismatch(self):
        evaluator = WorkflowRequestEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.WORKFLOW_REQUEST,
            scenario_type=ScenarioType.WORKFLOW_EXECUTION,
            input={"request": {"workflow_type": "cancel"}},
            baseline=Baseline(expected_workflow="book_meeting"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0


class TestResponseValidationEvaluator:
    @pytest.mark.asyncio
    async def test_response_match(self):
        evaluator = ResponseValidationEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.RESPONSE_VALIDATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"response": "Hello there"},
            baseline=Baseline(golden_answer="Hello there"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0

    @pytest.mark.asyncio
    async def test_response_mismatch(self):
        evaluator = ResponseValidationEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.RESPONSE_VALIDATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"response": "Wrong"},
            baseline=Baseline(golden_answer="Correct"),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 0.0

    @pytest.mark.asyncio
    async def test_empty_expected_golden_answer(self):
        evaluator = ResponseValidationEvaluator()
        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.RESPONSE_VALIDATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={"response": "anything"},
            baseline=Baseline(),
        )
        output = await evaluator.evaluate(case)
        assert output.confidence == 1.0


class TestRegisterDefaultEvaluators:
    def test_register_all_evaluators(self):
        registry = EvaluationRegistry()
        register_default_evaluators(registry)
        assert registry.count() == 11
        assert registry.has(EvaluationType.INTENT_CLASSIFICATION)
        assert registry.has(EvaluationType.RESPONSE_VALIDATION)
