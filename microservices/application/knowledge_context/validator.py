from __future__ import annotations

from application.knowledge_context.exceptions import ContextValidationError
from application.knowledge_context.models import (
    KnowledgeContextConfig,
    KnowledgeContextResult,
    TokenBudget,
)


class KnowledgeContextValidator:
    MAX_QUERY_LENGTH = 10000
    MIN_QUERY_LENGTH = 1
    MAX_CHUNKS = 100
    MIN_TOKEN_BUDGET = 128

    def validate_query(self, query: str) -> None:
        if not query or not query.strip():
            raise ContextValidationError("Query cannot be empty")
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ContextValidationError(
                f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH}"
            )

    def validate_config(self, config: KnowledgeContextConfig) -> None:
        if config.max_knowledge_tokens <= 0:
            raise ContextValidationError("max_knowledge_tokens must be positive")
        if config.max_retrieved_chunks <= 0:
            raise ContextValidationError("max_retrieved_chunks must be positive")
        if not 0.0 <= config.min_relevance_score <= 1.0:
            raise ContextValidationError("min_relevance_score must be between 0 and 1")

    def validate_budget(self, budget: TokenBudget) -> None:
        if budget.total_tokens < self.MIN_TOKEN_BUDGET:
            raise ContextValidationError(
                f"Total token budget must be at least {self.MIN_TOKEN_BUDGET}"
            )
        if budget.reserved_tokens < 0:
            raise ContextValidationError("Reserved tokens cannot be negative")
        if budget.knowledge_tokens <= 0:
            raise ContextValidationError("Knowledge token budget must be positive")

    def validate_result(self, result: KnowledgeContextResult) -> None:
        if result.total_chunks > self.MAX_CHUNKS:
            raise ContextValidationError(
                f"Result has {result.total_chunks} chunks, max is {self.MAX_CHUNKS}"
            )

    def validate_context_output(self, text: str, max_tokens: int) -> None:
        word_count = len(text.split())
        if word_count > max_tokens * 1.5:
            raise ContextValidationError(
                f"Output text is too large: ~{word_count} words for {max_tokens} token budget"
            )
