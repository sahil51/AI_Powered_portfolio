from __future__ import annotations


class ConfirmationEngineError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class ConfirmationResolutionError(ConfirmationEngineError):
    pass


class ConfirmationValidationError(ConfirmationEngineError):
    pass


class ConfirmationConfigurationError(ConfirmationEngineError):
    pass
