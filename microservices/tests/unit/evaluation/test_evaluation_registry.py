import pytest

from evaluation.exceptions import EvaluatorNotFoundError
from evaluation.models import Baseline, EvaluationCase, EvaluationOutput, EvaluationType, ScenarioType
from evaluation.registry import EvaluationRegistry


class TestEvaluationRegistry:
    def setup_method(self):
        self.registry = EvaluationRegistry()

    async def dummy_evaluator(self, case: EvaluationCase) -> EvaluationOutput:
        return EvaluationOutput()

    def test_register_and_get(self):
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        fn = self.registry.get(EvaluationType.INTENT_CLASSIFICATION)
        assert fn == self.dummy_evaluator

    def test_register_overwrites(self):
        async def second(case):
            return EvaluationOutput()

        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, second)
        assert self.registry.count() == 1
        fn = self.registry.get(EvaluationType.INTENT_CLASSIFICATION)
        assert fn == second

    def test_get_unregistered(self):
        with pytest.raises(EvaluatorNotFoundError) as exc:
            self.registry.get(EvaluationType.INTENT_CLASSIFICATION)
        assert "intent_classification" in str(exc.value)

    def test_has_registered(self):
        assert self.registry.has(EvaluationType.INTENT_CLASSIFICATION) is False
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        assert self.registry.has(EvaluationType.INTENT_CLASSIFICATION) is True

    def test_unregister(self):
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        self.registry.unregister(EvaluationType.INTENT_CLASSIFICATION)
        assert self.registry.has(EvaluationType.INTENT_CLASSIFICATION) is False

    def test_unregister_nonexistent(self):
        self.registry.unregister(EvaluationType.ENTITY_EXTRACTION)
        assert self.registry.count() == 0

    def test_list_registered(self):
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        self.registry.register(EvaluationType.ENTITY_EXTRACTION, self.dummy_evaluator)
        registered = self.registry.list_registered()
        assert EvaluationType.INTENT_CLASSIFICATION in registered
        assert EvaluationType.ENTITY_EXTRACTION in registered
        assert len(registered) == 2

    def test_count(self):
        assert self.registry.count() == 0
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        assert self.registry.count() == 1
        self.registry.register(EvaluationType.ENTITY_EXTRACTION, self.dummy_evaluator)
        assert self.registry.count() == 2

    def test_clear(self):
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        self.registry.register(EvaluationType.ENTITY_EXTRACTION, self.dummy_evaluator)
        self.registry.clear()
        assert self.registry.count() == 0

    def test_evaluator_function_called(self):
        results = []

        async def tracking_evaluator(case):
            results.append(case.case_id)
            return EvaluationOutput(predicted_intent="test")

        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, tracking_evaluator)
        fn = self.registry.get(EvaluationType.INTENT_CLASSIFICATION)
        import asyncio

        case = EvaluationCase(
            case_id="c1",
            evaluation_type=EvaluationType.INTENT_CLASSIFICATION,
            scenario_type=ScenarioType.SINGLE_TURN,
            input={},
            baseline=Baseline(),
        )
        asyncio.run(fn(case))
        assert results == ["c1"]

    def test_multiple_evaluators(self):
        self.registry.register(EvaluationType.INTENT_CLASSIFICATION, self.dummy_evaluator)
        self.registry.register(EvaluationType.ENTITY_EXTRACTION, self.dummy_evaluator)
        self.registry.register(EvaluationType.CONFIRMATION_RESOLUTION, self.dummy_evaluator)
        assert self.registry.count() == 3
        assert self.registry.has(EvaluationType.CONFIRMATION_RESOLUTION)
