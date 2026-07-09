from __future__ import annotations


class EmbeddingError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class EmbeddingConnectionError(EmbeddingError):
    pass


class EmbeddingTimeoutError(EmbeddingError):
    pass


class EmbeddingValidationError(EmbeddingError):
    pass


class EmbeddingProviderError(EmbeddingError):
    pass


class EmbeddingConfigurationError(EmbeddingError):
    pass


class EmbeddingSerializationError(EmbeddingError):
    pass


class EmbeddingChunkingError(EmbeddingError):
    pass
