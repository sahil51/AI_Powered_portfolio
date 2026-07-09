from __future__ import annotations

from application.exceptions import ApplicationError


class KnowledgeIngestionError(ApplicationError):
    pass


class ParsingError(KnowledgeIngestionError):
    pass


class UnsupportedSourceError(KnowledgeIngestionError):
    pass


class ValidationError(KnowledgeIngestionError):
    pass


class NormalizationError(KnowledgeIngestionError):
    pass


class DeduplicationError(KnowledgeIngestionError):
    pass


class VersioningError(KnowledgeIngestionError):
    pass


class ImportError(KnowledgeIngestionError):
    pass


class SchedulerError(KnowledgeIngestionError):
    pass


class IngestionCancelledError(KnowledgeIngestionError):
    pass


class ImportTimeoutError(KnowledgeIngestionError):
    pass


class ImportBatchError(KnowledgeIngestionError):
    pass


class DeadLetterError(KnowledgeIngestionError):
    pass
