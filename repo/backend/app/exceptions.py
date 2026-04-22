"""Application-level errors mapped to standard API error JSON."""


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(404, "NOT_FOUND", message)


class ValidationAppError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(400, "VALIDATION_ERROR", message)


class ConflictAppError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(409, "CONFLICT", message)
