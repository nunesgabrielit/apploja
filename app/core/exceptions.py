from logging import getLogger

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = getLogger(__name__)


class AppException(Exception):
    def __init__(self, detail: str, status_code: int, code: str) -> None:
        self.detail = detail
        self.status_code = status_code
        self.code = code
        super().__init__(detail)


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="authentication_error",
        )


class AuthorizationError(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            code="authorization_error",
        )


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            code="conflict_error",
        )


class BusinessRuleError(AppException):
    def __init__(self, detail: str = "Business rule violation") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="business_rule_error",
        )


class ExternalServiceError(AppException):
    def __init__(self, detail: str = "External service error") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="external_service_error",
        )


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found_error",
        )


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "http_error"},
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Validation error",
            "code": "validation_error",
            "errors": exc.errors(),
        },
    )


async def integrity_exception_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Database integrity error",
            "code": "integrity_error",
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "internal_server_error",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
