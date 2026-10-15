# app/core/exception_handler.py
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.service_exceptions import StorageException, FileTooBigException


def add_exception_handlers(app: FastAPI) -> None:
    """
    Enregistre les gestionnaires d'exceptions pour l'application FastAPI.
    """

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(_: Request, exc: NotFoundError):
        logging.warning("Resource not found: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(_: Request, exc: ForbiddenError):
        logging.warning("Forbidden access: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(_: Request, exc: ConflictError):
        logging.warning("Conflict error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        logging.warning("Value error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(StorageException)
    async def storage_exception_handler(_: Request, exc: StorageException):
        logging.warning("Storage exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileTooBigException)
    async def file_too_big_exception_handler(_: Request, exc: FileTooBigException):
        logging.warning("File too big: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception):
        logging.error("Unhandled exception occurred: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )