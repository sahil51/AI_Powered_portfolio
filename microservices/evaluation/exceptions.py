from __future__ import annotations


class EvaluationError(Exception):
    pass


class EvaluationConfigurationError(EvaluationError):
    pass


class EvaluationDataError(EvaluationError):
    pass


class EvaluationExecutionError(EvaluationError):
    pass


class EvaluationNotFoundError(EvaluationError):
    pass


class EvaluationValidationError(EvaluationError):
    pass


class DatasetLoadError(EvaluationDataError):
    pass


class DatasetFormatError(EvaluationDataError):
    pass


class DatasetVersionError(EvaluationDataError):
    pass


class ScenarioLoadError(EvaluationError):
    pass


class MetricComputationError(EvaluationError):
    pass


class ReportGenerationError(EvaluationError):
    pass


class EvaluatorNotFoundError(EvaluationNotFoundError):
    pass


class BaselineMismatchError(EvaluationValidationError):
    pass


class GoldenDataNotFoundError(EvaluationDataError):
    pass
