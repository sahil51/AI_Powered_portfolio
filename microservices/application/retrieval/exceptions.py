from __future__ import annotations


class RetrievalError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class RetrievalConnectionError(RetrievalError):
    pass


class RetrievalTimeoutError(RetrievalError):
    pass


class RetrievalValidationError(RetrievalError):
    pass


class RetrievalProviderError(RetrievalError):
    pass


class RetrievalConfigurationError(RetrievalError):
    pass


class RetrievalSerializationError(RetrievalError):
    pass


class RetrievalFusionError(RetrievalError):
    pass


class RetrievalRerankingError(RetrievalError):
    pass
