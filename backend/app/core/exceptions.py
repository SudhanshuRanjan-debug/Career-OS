"""
Custom exception classes and FastAPI exception handler registration.
"""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class NotFoundError(Exception):
    def __init__(self, resource: str = "Resource"):
        self.resource = resource
        super().__init__(f"{resource} not found")


class ForbiddenError(Exception):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message)


class ConflictError(Exception):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message)


class ValidationError(Exception):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message)


class StorageError(Exception):
    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def custom_validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, exc: StorageError):
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors()), "body": str(exc.body)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
