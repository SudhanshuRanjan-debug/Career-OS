"""
Document Vault schemas: metadata, categories, upload responses, and listing.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DocumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    doc_type: str | None = Field(None, max_length=30)
    description: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    doc_type: str
    original_filename: str
    storage_key: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    description: str | None = None
    version: int = 1
    uploaded_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
