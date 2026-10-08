"""
Health check schema.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field("healthy", description="Overall service health status")
    version: str = Field(..., description="Application semantic version")
    timestamp: datetime = Field(..., description="Current server UTC timestamp")
    database: str = Field("connected", description="Database connectivity status")
    storage: str = Field("connected", description="Storage provider connectivity status")
