from __future__ import annotations

from application.exceptions import ApplicationError
from application.knowledge_context.exceptions import (
    ContextAssemblyError,
    ContextCacheError,
    ContextCompressionError,
    ContextRetrievalError,
    ContextSecurityError,
    ContextValidationError,
    KnowledgeContextError,
    KnowledgeFreshnessError,
    TokenBudgetExceededError,
)


class TestKnowledgeContextError:
    def test_is_subclass_of_application_error(self):
        assert issubclass(KnowledgeContextError, ApplicationError)

    def test_default_message(self):
        e = KnowledgeContextError()
        assert e.message == "Application error"

    def test_custom_message(self):
        e = KnowledgeContextError("custom error message")
        assert e.message == "custom error message"

    def test_with_detail(self):
        e = KnowledgeContextError("test", detail="some detail")
        assert e.message == "test"
        assert e.detail == "some detail"


class TestContextAssemblyError:
    def test_is_subclass(self):
        assert issubclass(ContextAssemblyError, KnowledgeContextError)

    def test_message(self):
        e = ContextAssemblyError("assembly failed")
        assert e.message == "assembly failed"


class TestContextRetrievalError:
    def test_is_subclass(self):
        assert issubclass(ContextRetrievalError, KnowledgeContextError)

    def test_message(self):
        e = ContextRetrievalError("retrieval failed")
        assert e.message == "retrieval failed"


class TestContextValidationError:
    def test_is_subclass(self):
        assert issubclass(ContextValidationError, KnowledgeContextError)

    def test_message(self):
        e = ContextValidationError("validation failed")
        assert e.message == "validation failed"


class TestContextCacheError:
    def test_is_subclass(self):
        assert issubclass(ContextCacheError, KnowledgeContextError)

    def test_message(self):
        e = ContextCacheError("cache failed")
        assert e.message == "cache failed"


class TestContextCompressionError:
    def test_is_subclass(self):
        assert issubclass(ContextCompressionError, KnowledgeContextError)

    def test_message(self):
        e = ContextCompressionError("compression failed")
        assert e.message == "compression failed"


class TestTokenBudgetExceededError:
    def test_is_subclass(self):
        assert issubclass(TokenBudgetExceededError, KnowledgeContextError)

    def test_message(self):
        e = TokenBudgetExceededError("budget exceeded")
        assert e.message == "budget exceeded"


class TestKnowledgeFreshnessError:
    def test_is_subclass(self):
        assert issubclass(KnowledgeFreshnessError, KnowledgeContextError)

    def test_message(self):
        e = KnowledgeFreshnessError("knowledge outdated")
        assert e.message == "knowledge outdated"


class TestContextSecurityError:
    def test_is_subclass(self):
        assert issubclass(ContextSecurityError, KnowledgeContextError)

    def test_message(self):
        e = ContextSecurityError("access denied")
        assert e.message == "access denied"


class TestExceptionHierarchy:
    def test_all_exceptions_are_knowledge_context_errors(self):
        exceptions = [
            ContextAssemblyError,
            ContextRetrievalError,
            ContextValidationError,
            ContextCacheError,
            ContextCompressionError,
            TokenBudgetExceededError,
            KnowledgeFreshnessError,
            ContextSecurityError,
        ]
        for exc in exceptions:
            assert issubclass(exc, KnowledgeContextError), f"{exc.__name__} is not a subclass of KnowledgeContextError"

    def test_all_exceptions_are_application_errors(self):
        exceptions = [
            KnowledgeContextError,
            ContextAssemblyError,
            ContextRetrievalError,
            ContextValidationError,
            ContextCacheError,
            ContextCompressionError,
            TokenBudgetExceededError,
            KnowledgeFreshnessError,
            ContextSecurityError,
        ]
        for exc in exceptions:
            assert issubclass(exc, ApplicationError), f"{exc.__name__} is not a subclass of ApplicationError"
