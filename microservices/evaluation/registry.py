from __future__ import annotations

from collections.abc import Awaitable, Callable

from evaluation.exceptions import EvaluatorNotFoundError
from evaluation.models import EvaluationCase, EvaluationOutput, EvaluationType

EvaluatorFn = Callable[[EvaluationCase], Awaitable[EvaluationOutput]]


class EvaluationRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[EvaluationType, EvaluatorFn] = {}

    def register(self, evaluation_type: EvaluationType, fn: EvaluatorFn) -> None:
        self._evaluators[evaluation_type] = fn

    def unregister(self, evaluation_type: EvaluationType) -> None:
        self._evaluators.pop(evaluation_type, None)

    def get(self, evaluation_type: EvaluationType) -> EvaluatorFn:
        evaluator = self._evaluators.get(evaluation_type)
        if evaluator is None:
            raise EvaluatorNotFoundError(f"No evaluator registered for {evaluation_type.value}")
        return evaluator

    def has(self, evaluation_type: EvaluationType) -> bool:
        return evaluation_type in self._evaluators

    def list_registered(self) -> list[EvaluationType]:
        return list(self._evaluators.keys())

    def count(self) -> int:
        return len(self._evaluators)

    def clear(self) -> None:
        self._evaluators.clear()
