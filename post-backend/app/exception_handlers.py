"""
Gestionnaires d'ions pour l'application.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.services.service_exceptions import (FileTooBigException, 
                                             NotFoundException, 
                                             NsfwContentException,
                                             StorageException)  


def add_exception_handlers(app: FastAPI) -> None:
    """
    Enregistre les gestionnaires d'ions pour l'application FastAPI.
    """

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(_: Request, exc: NotFoundException):
        logging.warning("Resource not found: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileTooBigException)
    async def file_too_big_exception_handler(_: Request, exc: FileTooBigException):
        logging.warning("File upload too big: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(StorageException)
    async def storage_exception_handler(_: Request, exc: StorageException):
        logging.warning("Storage exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(NsfwContentException)
    async def nsfw_content_exception_handler(_: Request, exc: NsfwContentException):
        logging.warning("NSFW content rejected: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception):
        logging.error("Unhandled exception occurred: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )
