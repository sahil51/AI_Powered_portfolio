from exceptions.base import AppError


class AgentError(AppError):
    status_code: int = 500
    message: str = "Agent error"

    def __init__(self, message: str | None = None, detail: str | None = None, agent_id: str | None = None) -> None:
        self.agent_id = agent_id
        super().__init__(message=message or self.message, detail=detail)


class AgentNotFoundError(AgentError):
    status_code: int = 404
    message: str = "Agent not found"


class AgentConfigurationError(AgentError):
    status_code: int = 500
    message: str = "Agent configuration error"


class AgentExecutionError(AgentError):
    status_code: int = 500
    message: str = "Agent execution error"


class AgentTimeoutError(AgentError):
    status_code: int = 504
    message: str = "Agent execution timeout"


class AgentStateError(AgentError):
    status_code: int = 409
    message: str = "Agent state error"


class AgentValidationError(AgentError):
    status_code: int = 422
    message: str = "Agent validation error"


class AgentRegistrationError(AgentError):
    status_code: int = 409
    message: str = "Agent registration error"


class AgentRecoveryError(AgentError):
    status_code: int = 500
    message: str = "Agent recovery error"
