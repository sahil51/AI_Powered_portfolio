from __future__ import annotations


class IntentEngineError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class IntentClassificationError(IntentEngineError):
    pass


class IntentValidationError(IntentEngineError):
    pass


class IntentResolutionError(IntentEngineError):
    pass


class IntentConfigurationError(IntentEngineError):
    pass
