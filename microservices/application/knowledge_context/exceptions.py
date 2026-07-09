from __future__ import annotations

from application.exceptions import ApplicationError


class KnowledgeContextError(ApplicationError):
    pass


class ContextAssemblyError(KnowledgeContextError):
    pass


class ContextRetrievalError(KnowledgeContextError):
    pass


class ContextValidationError(KnowledgeContextError):
    pass


class ContextCacheError(KnowledgeContextError):
    pass


class ContextCompressionError(KnowledgeContextError):
    pass


class TokenBudgetExceededError(KnowledgeContextError):
    pass


class KnowledgeFreshnessError(KnowledgeContextError):
    pass


class ContextSecurityError(KnowledgeContextError):
    pass
