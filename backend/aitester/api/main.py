"""
FastAPI application factory for SpecGuard AI.

SOLID Principles:
- Single Responsibility: Each middleware/router handles one concern.
- Open/Closed: New routes added via include_router without touching this file.
- Dependency Inversion: All dependencies injected via FastAPI Depends().
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aitester.api.middleware import RequestTimingMiddleware
from aitester.api.v1.routes import analytics, auth, projects, reports, test_runs
from aitester.core.config import settings
from aitester.core.exceptions import AITesterError, RecordNotFoundError

logger = logging.getLogger("aitester.api")


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]"
    )
    yield
    logger.info("Shutting down SpecGuard AI...")


# ─── App Factory ──────────────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """
    Factory that creates and wires the FastAPI application.
    Using a factory allows clean test overrides (Open/Closed Principle).
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "SpecGuard AI — Automatically generate, execute, and analyze API tests "
            "from OpenAPI specs using AI, with real-time insights and security scoring."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestTimingMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    application.include_router(auth.router,      prefix=API_PREFIX)
    application.include_router(projects.router,  prefix=API_PREFIX)
    application.include_router(test_runs.router, prefix=API_PREFIX)
    application.include_router(reports.router,   prefix=API_PREFIX)
    application.include_router(analytics.router, prefix=API_PREFIX)

    # ── Exception Handlers ────────────────────────────────────────────────────
    _register_exception_handlers(application)

    return application


def _register_exception_handlers(application: FastAPI) -> None:
    """Register all exception handlers (Single Responsibility)."""

    @application.exception_handler(RecordNotFoundError)
    async def not_found_handler(request: Request, exc: RecordNotFoundError) -> JSONResponse:
        logger.warning(f"Record not found: {exc}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "message": exc.message, "details": exc.details},
        )

    @application.exception_handler(AITesterError)
    async def aitester_error_handler(request: Request, exc: AITesterError) -> JSONResponse:
        logger.error(f"Internal error: {exc}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "message": exc.message},
        )

    @application.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "message": "An unexpected error occurred."},
        )


# ─── Singleton ────────────────────────────────────────────────────────────────
app = create_application()


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
