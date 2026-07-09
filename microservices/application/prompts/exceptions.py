from exceptions.base import AppError


class PromptRegistryError(AppError):
    status_code: int = 500
    message: str = "Prompt registry error"


class PromptNotFoundError(PromptRegistryError):
    status_code: int = 404
    message: str = "Prompt not found"


class PromptVersionNotFoundError(PromptRegistryError):
    status_code: int = 404
    message: str = "Prompt version not found"


class PromptLoadError(PromptRegistryError):
    status_code: int = 500
    message: str = "Failed to load prompt"


class PromptRenderError(PromptRegistryError):
    status_code: int = 422
    message: str = "Failed to render prompt"


class PromptValidationError(PromptRegistryError):
    status_code: int = 422
    message: str = "Prompt validation failed"
