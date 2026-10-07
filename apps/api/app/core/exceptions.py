"""App errors and their JSON handlers."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """An intentional app error with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        """Creates the error."""

        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Attaches error handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        """Returns an AppError as JSON and only logs real server errors."""

        if exc.status_code >= 500:
            logger.error("%s %s failed: %s", request.method, request.url.path, exc.message)

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Reformats FastAPI's validation errors to match our standard style."""

        fields = []

        for error in exc.errors():
            location = [str(part) for part in error["loc"]]

            if location and location[0] in {"body", "query", "path", "header", "cookie"}:
                location = location[1:]

            name = ".".join(location) if location and not location[0].isdigit() else "body"

            fields.append({"field": name, "message": error["msg"]})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": {"message": "Received data is not valid", "fields": fields}},
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        """Catches all other errors, logs them, and returns a generic 500 error."""

        logger.exception("unhandled error on %s %s", request.method, request.url.path)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"message": "Internal server error"}},
        )
