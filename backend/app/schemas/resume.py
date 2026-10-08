"""
Resume schemas: metadata, upload response, renaming, and listing.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ResumeUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Friendly resume variant name/label")


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    original_filename: str
    storage_key: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    version: int = 1
    is_default: bool = False
    uploaded_at: datetime
    updated_at: datetime


class ResumeListResponse(BaseModel):
    items: list[ResumeResponse]
    total: int
