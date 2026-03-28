from __future__ import annotations

from typing import Any


class AppError(Exception):
    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InsufficientInventoryError(AppError):
    code = "INSUFFICIENT_INVENTORY"
    status_code = 400


class InvalidTransitionError(AppError):
    code = "INVALID_TRANSITION"
    status_code = 400


class TenantResolutionError(AppError):
    code = "TENANT_RESOLUTION_ERROR"
    status_code = 400


class EntityNotFoundError(AppError):
    code = "ENTITY_NOT_FOUND"
    status_code = 404


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400


class AuthorizationError(AppError):
    code = "AUTHZ_FORBIDDEN"
    status_code = 403

    def __init__(
        self,
        message: str,
        details: Any | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, details=details)
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
