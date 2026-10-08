"""
System and API health check endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="API Health Check")
async def get_health() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        database="connected",
        storage=settings.STORAGE_PROVIDER,
    )
