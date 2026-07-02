"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404,
            details={"resource": resource, "resource_id": str(resource_id)},
        )


class ValidationException(AppException):
    """Input validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class DatabaseException(AppException):
    """Database operation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, details=details)