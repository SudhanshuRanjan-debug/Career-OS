"""
Organization schemas — employer/recruiter profile.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_ORGANIZATION_SIZES = {"STARTUP", "SMALL", "MEDIUM", "LARGE", "ENTERPRISE"}


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


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization / Company Name")
    website: Optional[str] = Field(None, max_length=500, description="Company Website URL")
    industry: Optional[str] = Field(None, max_length=255, description="Industry sector")
    size: Optional[str] = Field(None, max_length=50, description="STARTUP, SMALL, MEDIUM, LARGE, or ENTERPRISE")
    location: Optional[str] = Field(None, max_length=255, description="Headquarters or primary location")
    description: Optional[str] = Field(None, description="Company description")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo image URL")
    linkedin_url: Optional[str] = Field(None, max_length=500, description="LinkedIn company page URL")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Organization name cannot be empty")
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
            if v_upper not in ALLOWED_ORGANIZATION_SIZES:
                raise ValueError(f"Size must be one of: {', '.join(sorted(ALLOWED_ORGANIZATION_SIZES))}")
            return v_upper
        return v


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Organization name cannot be empty")
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
            if v_upper not in ALLOWED_ORGANIZATION_SIZES:
                raise ValueError(f"Size must be one of: {', '.join(sorted(ALLOWED_ORGANIZATION_SIZES))}")
            return v_upper
        return v


class OrganizationResponse(OrganizationBase):
    id: UUID
    owner_user_id: UUID
    slug: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
