"""
Company schemas — target employers directory.
Pydantic v2 schemas for Stage 6: Network / Contacts.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.common import PaginatedResponse


ALLOWED_COMPANY_SIZES = {"STARTUP", "SMALL", "MEDIUM", "LARGE", "ENTERPRISE"}


def validate_safe_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    v_lower = v.lower()
    if not (v_lower.startswith("http://") or v_lower.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")
    if any(v_lower.startswith(p) for p in ("javascript:", "data:", "file:", "vbscript:")):
        raise ValueError("Invalid or unsafe URL scheme")
    return v


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Company or Employer Name")
    website: Optional[str] = Field(None, max_length=500, description="Company Website URL")
    industry: Optional[str] = Field(None, max_length=255, description="Industry sector")
    size: Optional[str] = Field(None, max_length=50, description="STARTUP, SMALL, MEDIUM, LARGE, or ENTERPRISE")
    location: Optional[str] = Field(None, max_length=255, description="Headquarters or office location")
    description: Optional[str] = Field(None, description="Company overview or description")
    notes: Optional[str] = Field(None, description="Private candidate research notes")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo image URL")
    linkedin_url: Optional[str] = Field(None, max_length=500, description="LinkedIn company page URL")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Company name cannot be empty")
        return v

    @field_validator("website", "logo_url", "linkedin_url")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_COMPANY_SIZES:
                raise ValueError(f"Invalid company size: {v}. Must be one of {sorted(ALLOWED_COMPANY_SIZES)}")
            return v_upper
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    notes: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Company name cannot be empty")
        return v

    @field_validator("website", "logo_url", "linkedin_url")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_COMPANY_SIZES:
                raise ValueError(f"Invalid company size: {v}. Must be one of {sorted(ALLOWED_COMPANY_SIZES)}")
            return v_upper
        return v


class CompanySummary(BaseModel):
    id: UUID
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyResponse(CompanyBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(PaginatedResponse[CompanyResponse]):
    pass
