"""
Pydantic schemas for the Opportunity & SavedOpportunity domain.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import PaginatedResponse


ALLOWED_OPPORTUNITY_STATUSES = {"ACTIVE", "SAVED", "CONSIDERING", "ARCHIVED", "NOT_INTERESTED"}
ALLOWED_LOCATION_TYPES = {"REMOTE", "HYBRID", "ON_SITE"}
ALLOWED_EMPLOYMENT_TYPES = {"FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP"}


class OpportunityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job / Opportunity Title")
    company_name: Optional[str] = Field(None, max_length=255, description="Company / Employer Name")
    company_id: Optional[UUID] = Field(None, description="Optional foreign key to registered company")
    source: Optional[str] = Field("MANUAL", max_length=100, description="Discovery source (MANUAL, URL_IMPORT, REFERRAL, etc.)")
    source_url: Optional[str] = Field(None, max_length=1000, description="External job posting URL")
    location: Optional[str] = Field(None, max_length=255, description="Geographic location (e.g. San Francisco, CA)")
    location_type: Optional[str] = Field(None, max_length=20, description="REMOTE, HYBRID, or ON_SITE")
    employment_type: Optional[str] = Field(None, max_length=50, description="FULL_TIME, PART_TIME, CONTRACT, or INTERNSHIP")
    description: Optional[str] = Field(None, description="Complete job description")
    requirements: Optional[str] = Field(None, description="Job requirements and qualifications")
    compensation_min: Optional[Decimal] = Field(None, ge=0, description="Minimum compensation range")
    compensation_max: Optional[Decimal] = Field(None, ge=0, description="Maximum compensation range")
    compensation_currency: Optional[str] = Field("USD", max_length=10, description="ISO currency code")
    posted_date: Optional[date] = Field(None, description="Date the opportunity was posted")
    expiry_date: Optional[date] = Field(None, description="Application deadline or posting expiration date")
    status: str = Field("ACTIVE", max_length=30, description="Opportunity tracking status")
    notes: Optional[str] = Field(None, description="Personal tracking notes")
    job_posting_id: Optional[UUID] = Field(None, description="Optional foreign key to platform job posting")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Title must not be empty or whitespace only")
        return v

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        lower_v = v.lower()
        if not (lower_v.startswith("http://") or lower_v.startswith("https://")):
            raise ValueError("External URL must use a safe http:// or https:// scheme")
        if any(lower_v.startswith(unsafe) for unsafe in ["javascript:", "data:", "file:", "vbscript:"]):
            raise ValueError("Unsafe URL scheme detected")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ALLOWED_OPPORTUNITY_STATUSES:
            raise ValueError(f"Invalid opportunity status: {v}. Must be one of {sorted(ALLOWED_OPPORTUNITY_STATUSES)}")
        return upper

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        upper = v.strip().upper()
        if upper not in ALLOWED_LOCATION_TYPES:
            raise ValueError(f"Invalid location type: {v}. Must be one of {sorted(ALLOWED_LOCATION_TYPES)}")
        return upper

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        upper = v.strip().upper()
        if upper not in ALLOWED_EMPLOYMENT_TYPES:
            raise ValueError(f"Invalid employment type: {v}. Must be one of {sorted(ALLOWED_EMPLOYMENT_TYPES)}")
        return upper

    @model_validator(mode="after")
    def validate_ranges(self) -> "OpportunityBase":
        if self.compensation_min is not None and self.compensation_max is not None:
            if self.compensation_min > self.compensation_max:
                raise ValueError("compensation_min cannot exceed compensation_max")
        if self.posted_date is not None and self.expiry_date is not None:
            if self.posted_date > self.expiry_date:
                raise ValueError("posted_date cannot be after expiry_date")
        return self


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    company_id: Optional[UUID] = None
    source: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=255)
    location_type: Optional[str] = Field(None, max_length=20)
    employment_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    requirements: Optional[str] = None
    compensation_min: Optional[Decimal] = Field(None, ge=0)
    compensation_max: Optional[Decimal] = Field(None, ge=0)
    compensation_currency: Optional[str] = Field(None, max_length=10)
    posted_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = None
    job_posting_id: Optional[UUID] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title must not be empty or whitespace only")
        return v

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        lower_v = v.lower()
        if not (lower_v.startswith("http://") or lower_v.startswith("https://")):
            raise ValueError("External URL must use a safe http:// or https:// scheme")
        if any(lower_v.startswith(unsafe) for unsafe in ["javascript:", "data:", "file:", "vbscript:"]):
            raise ValueError("Unsafe URL scheme detected")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        upper = v.strip().upper()
        if upper not in ALLOWED_OPPORTUNITY_STATUSES:
            raise ValueError(f"Invalid opportunity status: {v}. Must be one of {sorted(ALLOWED_OPPORTUNITY_STATUSES)}")
        return upper

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        upper = v.strip().upper()
        if upper not in ALLOWED_LOCATION_TYPES:
            raise ValueError(f"Invalid location type: {v}. Must be one of {sorted(ALLOWED_LOCATION_TYPES)}")
        return upper

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        upper = v.strip().upper()
        if upper not in ALLOWED_EMPLOYMENT_TYPES:
            raise ValueError(f"Invalid employment type: {v}. Must be one of {sorted(ALLOWED_EMPLOYMENT_TYPES)}")
        return upper

    @model_validator(mode="after")
    def validate_ranges(self) -> "OpportunityUpdate":
        if self.compensation_min is not None and self.compensation_max is not None:
            if self.compensation_min > self.compensation_max:
                raise ValueError("compensation_min cannot exceed compensation_max")
        if self.posted_date is not None and self.expiry_date is not None:
            if self.posted_date > self.expiry_date:
                raise ValueError("posted_date cannot be after expiry_date")
        return self


class OpportunityResponse(OpportunityBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    is_saved: bool = Field(False, description="Indicates if this opportunity is saved by the current user")

    model_config = ConfigDict(from_attributes=True)


class OpportunityListResponse(PaginatedResponse[OpportunityResponse]):
    pass


class SavedOpportunityCreate(BaseModel):
    notes: Optional[str] = Field(None, description="Optional notes on why this opportunity was saved")


class SavedOpportunityResponse(BaseModel):
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    saved_at: datetime
    notes: Optional[str] = None
    opportunity: Optional[OpportunityResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SavedOpportunityListResponse(BaseModel):
    items: list[SavedOpportunityResponse] = Field(..., description="List of saved opportunities")
    total: int = Field(..., ge=0, description="Total number of saved opportunities")
