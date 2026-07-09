from __future__ import annotations

from evaluation.models import EvaluationResult


class Scorer:
    def precision(self, true_positives: int, false_positives: int) -> float:
        denominator = true_positives + false_positives
        return true_positives / denominator if denominator > 0 else 0.0

    def recall(self, true_positives: int, false_negatives: int) -> float:
        denominator = true_positives + false_negatives
        return true_positives / denominator if denominator > 0 else 0.0

    def f1(self, precision: float, recall: float) -> float:
        denominator = precision + recall
        return 2 * precision * recall / denominator if denominator > 0 else 0.0

    def accuracy(self, correct: int, total: int) -> float:
        return correct / total if total > 0 else 0.0

    def weighted_score(self, results: list[EvaluationResult]) -> float:
        if not results:
            return 0.0
        total_weight = sum(r.metrics.get("weight", 1.0) for r in results)
        if total_weight == 0:
            return 0.0
        weighted = sum(r.score * r.metrics.get("weight", 1.0) for r in results)
        return weighted / total_weight

    def overall_platform_score(self, results: list[EvaluationResult]) -> float:
        if not results:
            return 0.0
        scores = [r.score for r in results]
        return sum(scores) / len(scores)

    def score_result(self, result: EvaluationResult) -> float:
        baseline = result.baseline
        output = result.output
        score = 0.0
        components = 0
        if baseline.expected_intent and output.predicted_intent:
            score += 1.0 if output.predicted_intent.strip().lower() == baseline.expected_intent.strip().lower() else 0.0
            components += 1
        if baseline.expected_entities and output.predicted_entities:
            expected_set = {(e.get("type", ""), e.get("value", "")) for e in baseline.expected_entities}
            predicted_set = {(e.get("type", ""), e.get("value", "")) for e in output.predicted_entities}
            if expected_set:
                hit_count = len(expected_set & predicted_set)
                score += hit_count / len(expected_set)
                components += 1
        if baseline.expected_output and output.predicted_value:
            score += 1.0 if str(output.predicted_value).strip().lower() == baseline.expected_output.strip().lower() else 0.0  # noqa: E501
            components += 1
        if baseline.expected_workflow and output.predicted_workflow:
            score += 1.0 if output.predicted_workflow.strip().lower() == baseline.expected_workflow.strip().lower() else 0.0  # noqa: E501
            components += 1
        return score / components if components > 0 else 0.0
