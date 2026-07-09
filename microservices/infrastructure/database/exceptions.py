from exceptions.base import AppError


class DatabaseError(AppError):
    status_code: int = 500

    def __init__(self, message: str = "Database error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class ConnectionError(DatabaseError):
    status_code: int = 503

    def __init__(self, message: str = "Database connection error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class RepositoryError(DatabaseError):
    status_code: int = 500

    def __init__(self, message: str = "Repository error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class TransactionError(DatabaseError):
    status_code: int = 500

    def __init__(self, message: str = "Transaction error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class IntegrityError(DatabaseError):
    status_code: int = 409

    def __init__(self, message: str = "Integrity constraint violation", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class ConcurrencyError(DatabaseError):
    status_code: int = 409

    def __init__(self, message: str = "Concurrency conflict", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)


class MigrationError(DatabaseError):
    status_code: int = 500

    def __init__(self, message: str = "Migration error", detail: str | None = None) -> None:
        super().__init__(message=message, detail=detail)
