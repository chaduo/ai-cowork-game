from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@dataclass
class ApiError(Exception):
    code: str
    message: str
    details: list[Any] | None = None
    status_code: int = 400


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def error_response(request: Request, *, code: str, message: str, details: list[Any], status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id(request),
            }
        },
    )


async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(
        request,
        code=exc.code,
        message=exc.message,
        details=exc.details or [],
        status_code=exc.status_code,
    )


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request,
        code="validation_error",
        message="Request validation failed",
        details=exc.errors(),
        status_code=422,
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        request,
        code="internal_error",
        message="Internal server error",
        details=[],
        status_code=500,
    )
