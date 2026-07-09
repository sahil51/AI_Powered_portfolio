from exceptions.base import AppError


class ObservabilityError(AppError):
    status_code = 500
    message = "Observability error"


class ObservabilityConfigurationError(ObservabilityError):
    status_code = 500
    message = "Observability configuration error"


class ObservabilityInitializationError(ObservabilityError):
    status_code = 500
    message = "Observability initialization failed"


class ObservabilityConnectionError(ObservabilityError):
    status_code = 503
    message = "Observability connection failed"


class ObservabilityProviderError(ObservabilityError):
    status_code = 502
    message = "Observability provider error"
