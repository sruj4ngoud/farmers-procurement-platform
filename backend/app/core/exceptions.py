"""Domain exceptions that map cleanly onto HTTP responses.

Services raise these typed errors instead of leaking transport concerns. A global
exception handler (see app/middleware/error_handler.py) converts them into JSON
responses with the right status code.
"""

from typing import Any


class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, detail: str = "Internal server error", *args: Any) -> None:
        self.detail = detail
        super().__init__(detail, *args)


class BadRequestError(AppError):
    """The request is malformed or violates business validation rules."""

    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppError):
    """Authentication is missing, invalid, or expired."""

    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    """The authenticated farmer is not allowed to access the resource."""

    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    """The requested resource does not exist."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """The request conflicts with the current state of the resource."""

    status_code = 409
    code = "conflict"
