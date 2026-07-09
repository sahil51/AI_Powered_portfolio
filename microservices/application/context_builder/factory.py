from __future__ import annotations

from application.context_builder.budget import ContextBudgetPolicy
from application.context_builder.builder import ContextBuilder
from application.context_builder.compression import ContextCompressionPolicy, DeduplicationStrategy, TruncationStrategy
from application.context_builder.policies import ContextPolicy, LayerOrderingPolicy, PrivacyPolicy, VisibilityPolicy


class ContextFactory:
    @staticmethod
    def create_default_builder() -> ContextBuilder:
        budget_policy = ContextBudgetPolicy(max_tokens=8192)
        layer_weights = {
            "system": 0.15,
            "identity": 0.05,
            "conversation": 0.40,
            "memory": 0.25,
            "workflow": 0.10,
            "knowledge": 0.03,
            "tool": 0.02,
        }
        budget = budget_policy.create_budget(layer_weights)
        compression = ContextCompressionPolicy(
            dedup=DeduplicationStrategy(enabled=True, field_key="content"),
            truncation=TruncationStrategy(enabled=True, max_tokens=2048),
        )
        policy = ContextPolicy(
            ordering=LayerOrderingPolicy(
                order=["system", "identity", "conversation", "memory", "workflow", "knowledge", "tool"],
            ),
            visibility=VisibilityPolicy(),
            privacy=PrivacyPolicy(),
        )
        return ContextBuilder(budget=budget, compression=compression, policy=policy)

    @staticmethod
    def create_builder(
        max_tokens: int = 8192,
        reserved_tokens: int = 1024,
        output_tokens: int = 2048,
        layer_weights: dict[str, float] | None = None,
    ) -> ContextBuilder:
        weights = layer_weights or {
            "system": 0.15,
            "identity": 0.05,
            "conversation": 0.40,
            "memory": 0.25,
            "workflow": 0.10,
            "knowledge": 0.03,
            "tool": 0.02,
        }
        budget_policy = ContextBudgetPolicy(
            max_tokens=max_tokens,
            reserved_tokens=reserved_tokens,
            output_tokens=output_tokens,
        )
        budget = budget_policy.create_budget(weights)
        return ContextBuilder(budget=budget)
