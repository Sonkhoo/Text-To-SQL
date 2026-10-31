from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from slowapi.errors import RateLimitExceeded

from backend.core.exception import AppException


async def app_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:

    if not isinstance(exc, AppException):
        raise exc

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


async def rate_limit_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:

    if not isinstance(exc, RateLimitExceeded):
        raise exc

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": str(exc.detail),
            },
        },
    )