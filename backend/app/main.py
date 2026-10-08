"""
Career & Job Application Management Platform
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router

from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Career Platform API",
    description="Career & Job Application Management Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

if settings.DEBUG:
    @app.get("/api/docs", include_in_schema=False)
    async def redirect_api_docs():
        return RedirectResponse(url="/docs")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness():
    # TODO: add DB ping in Stage 2
    return {"status": "ready"}


@app.get("/health/live", tags=["health"])
async def liveness():
    return {"status": "alive"}
