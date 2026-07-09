from __future__ import annotations

import math

from evaluation.exceptions import MetricComputationError
from evaluation.models import (
    EvaluationMetrics,
    EvaluationResult,
    EvaluationStatistics,
    EvaluationType,
    MetricType,
)


class MetricsComputer:
    def compute_metrics(self, results: list[EvaluationResult]) -> EvaluationMetrics:
        if not results:
            return EvaluationMetrics(evaluation_type=EvaluationType.INTENT_CLASSIFICATION)

        eval_type = results[0].evaluation_type
        metrics = EvaluationMetrics(evaluation_type=eval_type)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        correct_intent = sum(1 for r in results if r.metrics.get("intent_match", 0) > 0)
        total_latency = sum(r.output.latency_ms for r in results)
        total_tokens = sum(r.output.token_count for r in results)

        entity_results = [r for r in results if r.metrics.get("entity_count", 0) > 0]
        correct_entities = sum(1 for r in entity_results if r.metrics.get("entity_accuracy", 0) > 0.5)
        metrics.intent_accuracy = correct_intent / total if total else 0.0
        metrics.entity_accuracy = correct_entities / len(entity_results) if entity_results else 0.0
        metrics.confirmation_accuracy = passed / total if total else 0.0

        recall_results = [r for r in results if r.metrics.get("recall", -1) >= 0]
        metrics.memory_recall = sum(r.metrics.get("recall", 0) for r in recall_results) / len(recall_results) if recall_results else 0.0  # noqa: E501

        precision_results = [r for r in results if r.metrics.get("precision", -1) >= 0]
        metrics.knowledge_precision = sum(r.metrics.get("precision", 0) for r in precision_results) / len(precision_results) if precision_results else 0.0  # noqa: E501
        metrics.knowledge_recall = sum(r.metrics.get("recall", 0) for r in recall_results) / len(recall_results) if recall_results else 0.0  # noqa: E501

        mrr_results = [r for r in results if r.metrics.get("mrr", -1) >= 0]
        metrics.mrr = sum(r.metrics.get("mrr", 0) for r in mrr_results) / len(mrr_results) if mrr_results else 0.0

        ndcg_results = [r for r in results if r.metrics.get("ndcg", -1) >= 0]
        metrics.ndcg = sum(r.metrics.get("ndcg", 0) for r in ndcg_results) / len(ndcg_results) if ndcg_results else 0.0

        context_results = [r for r in results if r.metrics.get("context_quality", -1) >= 0]
        metrics.context_quality = sum(r.metrics.get("context_quality", 0) for r in context_results) / len(context_results) if context_results else 0.0  # noqa: E501

        prompt_results = [r for r in results if r.metrics.get("prompt_quality", -1) >= 0]
        metrics.prompt_quality = sum(r.metrics.get("prompt_quality", 0) for r in prompt_results) / len(prompt_results) if prompt_results else 0.0  # noqa: E501

        hallucinated = sum(1 for r in results if r.metrics.get("hallucinated", 0) > 0)
        metrics.hallucination_rate = hallucinated / total if total else 0.0
        metrics.latency_ms = total_latency / total if total else 0.0
        metrics.token_usage = total_tokens

        cost_results = [r for r in results if r.metrics.get("cost", 0) > 0]
        metrics.embedding_cost = sum(r.metrics.get("cost", 0) for r in cost_results if r.evaluation_type in ("embedding",))  # noqa: E501
        metrics.provider_cost = sum(r.metrics.get("cost", 0) for r in cost_results if r.evaluation_type not in ("embedding",))  # noqa: E501

        workflow_results = [r for r in results if r.metrics.get("workflow_success", -1) >= 0]
        workflow_success = sum(1 for r in workflow_results if r.metrics.get("workflow_success", 0) > 0)
        metrics.workflow_success_rate = workflow_success / len(workflow_results) if workflow_results else 0.0

        retry_results = [r for r in results if r.metrics.get("retry_count", 0) > 0]
        metrics.retry_rate = len(retry_results) / total if total else 0.0
        metrics.failure_rate = (total - passed) / total if total else 0.0

        return metrics

    def compute_statistics(self, results: list[EvaluationResult]) -> EvaluationStatistics:
        if not results:
            return EvaluationStatistics()
        scores = [r.score for r in results]
        latencies = [r.output.latency_ms for r in results]
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        stats = EvaluationStatistics(
            total_cases=total,
            passed=passed,
            failed=total - passed,
            pass_rate=passed / total if total else 0.0,
            average_score=sum(scores) / total if total else 0.0,
            min_score=min(scores) if scores else 0.0,
            max_score=max(scores) if scores else 0.0,
            average_latency_ms=sum(latencies) / total if total else 0.0,
            total_tokens=sum(r.output.token_count for r in results),
            total_cost=sum(r.metrics.get("cost", 0) for r in results),
        )
        sorted_scores = sorted(scores)
        mid = len(sorted_scores) // 2
        stats.median_score = sorted_scores[mid] if len(sorted_scores) % 2 else (sorted_scores[mid - 1] + sorted_scores[mid]) / 2  # noqa: E501
        if len(sorted_scores) > 1:
            mean = stats.average_score
            variance = sum((s - mean) ** 2 for s in sorted_scores) / len(sorted_scores)
            stats.std_dev = math.sqrt(variance)
        p95_idx = max(0, min(len(sorted_scores) - 1, int(len(sorted_scores) * 0.95)))
        stats.p95_score = sorted_scores[p95_idx] if sorted_scores else 0.0
        p99_idx = max(0, min(len(sorted_scores) - 1, int(len(sorted_scores) * 0.99)))
        stats.p99_score = sorted_scores[p99_idx] if sorted_scores else 0.0
        per_type: dict[str, float] = {}
        type_scores: dict[str, list[float]] = {}
        for r in results:
            key = r.evaluation_type.value
            type_scores.setdefault(key, []).append(r.score)
        for eval_type, type_scores_list in type_scores.items():
            per_type[eval_type] = sum(type_scores_list) / len(type_scores_list) if type_scores_list else 0.0
        stats.per_type = per_type
        per_scenario: dict[str, float] = {}
        scenario_scores: dict[str, list[float]] = {}
        for r in results:
            key = r.scenario_type.value
            scenario_scores.setdefault(key, []).append(r.score)
        for scenario, scenario_scores_list in scenario_scores.items():
            per_scenario[scenario] = sum(scenario_scores_list) / len(scenario_scores_list) if scenario_scores_list else 0.0  # noqa: E501
        stats.per_scenario = per_scenario
        return stats

    def compute_metric(self, metric_type: MetricType, results: list[EvaluationResult]) -> float:
        metrics = self.compute_metrics(results)
        mapping = {
            MetricType.INTENT_ACCURACY: metrics.intent_accuracy,
            MetricType.ENTITY_ACCURACY: metrics.entity_accuracy,
            MetricType.CONFIRMATION_ACCURACY: metrics.confirmation_accuracy,
            MetricType.MEMORY_RECALL: metrics.memory_recall,
            MetricType.KNOWLEDGE_PRECISION: metrics.knowledge_precision,
            MetricType.KNOWLEDGE_RECALL: metrics.knowledge_recall,
            MetricType.MRR: metrics.mrr,
            MetricType.NDCG: metrics.ndcg,
            MetricType.CONTEXT_QUALITY: metrics.context_quality,
            MetricType.PROMPT_QUALITY: metrics.prompt_quality,
            MetricType.HALLUCINATION_RATE: metrics.hallucination_rate,
            MetricType.LATENCY: metrics.latency_ms,
            MetricType.TOKEN_USAGE: float(metrics.token_usage),
            MetricType.EMBEDDING_COST: metrics.embedding_cost,
            MetricType.PROVIDER_COST: metrics.provider_cost,
            MetricType.WORKFLOW_SUCCESS_RATE: metrics.workflow_success_rate,
            MetricType.RETRY_RATE: metrics.retry_rate,
            MetricType.FAILURE_RATE: metrics.failure_rate,
        }
        if metric_type not in mapping:
            raise MetricComputationError(f"Unknown metric type: {metric_type}")
        return mapping[metric_type]
