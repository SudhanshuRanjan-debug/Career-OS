"""
Common reusable Pydantic schemas: pagination, sorting, envelopes, and error representations.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number starting from 1")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort direction")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(..., description="List of items on current page")
    total: int = Field(..., ge=0, description="Total count across all pages")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Human-readable success message")


class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="User-friendly error explanation")
    details: dict | list | None = Field(None, description="Optional diagnostic details")
