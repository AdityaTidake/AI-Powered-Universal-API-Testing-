"""
FastAPI application factory for SpecGuard AI.

SOLID Principles Applied:
- Single Responsibility: Each middleware/router handles one concern.
- Open/Closed: New routes added via router.include_router without modifying this file.
- Dependency Inversion: Depends() injection used throughout.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aitester.api.middleware import RequestTimingMiddleware
from aitester.api.routes import projects, test_runs
from aitester.api.v1 import reports
from aitester.core.config import settings
from aitester.core.exceptions import AITesterError, RecordNotFoundError

logger = logging.getLogger("aitester.api")


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.
    Runs startup logic before yield, shutdown logic after yield.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    # Future: warm up DB pool, connect Redis, etc.
    yield
    logger.info("Shutting down SpecGuard AI...")


# ─── App factory ──────────────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """
    Factory function that creates and configures the FastAPI application.
    Using a factory follows the Open/Closed principle — behaviour can be
    extended (e.g. in tests) without modifying this module.
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

    # ── Middleware (applied in reverse order — last added = outermost) ────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestTimingMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    # NOTE: Auth dependency moved from global app to per-route via Depends().
    #       This follows the Dependency Inversion Principle.
    application.include_router(projects.router, prefix="/api/v1")
    application.include_router(test_runs.router, prefix="/api/v1")
    application.include_router(reports.router, prefix="/api/v1")

    # ── Exception Handlers ────────────────────────────────────────────────────
    _register_exception_handlers(application)

    return application


def _register_exception_handlers(application: FastAPI) -> None:
    """Register all custom exception handlers (Single Responsibility)."""

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


# ─── Application singleton ────────────────────────────────────────────────────
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
