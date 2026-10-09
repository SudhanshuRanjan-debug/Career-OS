"""
Career & Job Application Management Platform
FastAPI Application Entry Point
"""

from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import Settings, settings
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router


def create_application(custom_settings: Optional[Settings] = None) -> FastAPI:
    """Create and configure FastAPI application instance."""
    cfg = custom_settings or settings

    application = FastAPI(
        title="Career Platform API",
        description="Career & Job Application Management Platform",
        version="1.0.0",
        docs_url="/docs" if cfg.docs_enabled else None,
        redoc_url="/redoc" if cfg.docs_enabled else None,
        openapi_url="/openapi.json" if cfg.docs_enabled else None,
    )

    if cfg.docs_enabled:
        @application.get("/api/docs", include_in_schema=False)
        async def redirect_api_docs():
            return RedirectResponse(url="/docs")

    # ---------------------------------------------------------------------------
    # Middleware
    # ---------------------------------------------------------------------------

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # In production or when DEBUG is False, enforce TrustedHostMiddleware
    if cfg.is_production or not cfg.DEBUG:
        application.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=cfg.ALLOWED_HOSTS,
        )

    # ---------------------------------------------------------------------------
    # Exception handlers
    # ---------------------------------------------------------------------------

    register_exception_handlers(application)

    # ---------------------------------------------------------------------------
    # Routes
    # ---------------------------------------------------------------------------

    application.include_router(api_router, prefix="/api/v1")

    # ---------------------------------------------------------------------------
    # Health endpoints
    # ---------------------------------------------------------------------------

    @application.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    async def readiness():
        # TODO: add DB ping in Stage 2
        return {"status": "ready"}

    @application.get("/health/live", tags=["health"])
    async def liveness():
        return {"status": "alive"}

    return application


app = create_application()
