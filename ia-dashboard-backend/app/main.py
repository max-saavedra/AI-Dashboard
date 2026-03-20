"""
app/main.py

FastAPI application factory.
Configures middleware, exception handlers, and mounts the API router.

Follows the application-factory pattern so the app can be imported
in tests without side effects.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AIProviderError,
    AuthorizationError,
    DataNotFoundError,
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(debug=settings.app_debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context.
    Runs startup tasks (e.g. DB connection check, AI provider validation)
    before yielding, and cleanup tasks on shutdown.
    """
    logger.info("application_starting", env=settings.app_env)

    # Validate that AI providers are properly configured
    has_gemini, has_openai = settings.has_ai_providers()
    if not has_gemini:
        logger.warning("ai_provider_misconfigured",
                       provider="gemini", issue="api_key_missing")
    if not has_openai:
        logger.warning("ai_provider_misconfigured",
                       provider="openai", issue="api_key_missing")
    if not has_gemini and not has_openai:
        logger.error("ai_providers_unconfigured",
                     issue="both_primary_and_fallback_missing")

    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="IA Dashboard API",
        description="Backend for intelligent Excel/CSV analysis with AI-powered insights.",
        version="1.0.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "message": "IA Dashboard API is running"}

    _add_logging_middleware(app)
    _add_cors(app)
    _add_exception_handlers(app)
    app.include_router(api_router)

    return app


def _add_logging_middleware(app: FastAPI) -> None:
    """
    Add middleware to log HTTP requests with timing and errors only.
    Reduces noise in production logs.
    """
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import time

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Only log errors and slow requests
        if response.status_code >= 400 or duration_ms > 1000:
            logger.warning(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 1),
            )
        elif response.status_code >= 500:
            logger.error(
                "http_error",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

        return response


def _add_cors(app: FastAPI) -> None:
    """Configure CORS so the Vue SPA can call the backend (SA section 4.2)."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_exception_handlers(app: FastAPI) -> None:
    """
    Map domain exceptions to HTTP responses.
    Keeps route handlers clean – they only raise domain exceptions.
    """

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"success": False,
                     "error_code": "FILE_TOO_LARGE", "message": str(exc)},
        )

    @app.exception_handler(UnsupportedFileFormatError)
    async def unsupported_format_handler(request: Request, exc: UnsupportedFileFormatError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False,
                     "error_code": "UNSUPPORTED_FORMAT", "message": str(exc)},
        )

    @app.exception_handler(EmptyFileError)
    async def empty_file_handler(request: Request, exc: EmptyFileError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False,
                     "error_code": "EMPTY_FILE", "message": str(exc)},
        )

    @app.exception_handler(AIProviderError)
    async def ai_provider_handler(request: Request, exc: AIProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False,
                     "error_code": "AI_UNAVAILABLE", "message": str(exc)},
        )

    @app.exception_handler(DataNotFoundError)
    async def not_found_handler(request: Request, exc: DataNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False,
                     "error_code": "NOT_FOUND", "message": str(exc)},
        )

    @app.exception_handler(AuthorizationError)
    async def auth_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False,
                     "error_code": "FORBIDDEN", "message": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback

        # Log full stack trace in debug mode
        if settings.app_debug:
            tb_str = "".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__))
            logger.error("unhandled_exception_with_trace",
                         path=str(request.url),
                         error_type=type(exc).__name__,
                         error=str(exc),
                         traceback=tb_str)
        else:
            logger.error("unhandled_exception",
                         path=str(request.url),
                         error=str(exc))

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        )


# Module-level app instance used by uvicorn and tests
app = create_app()
