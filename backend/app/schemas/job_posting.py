"""
JobPosting and JobPostingSkill schemas — recruiter job listings.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.organization import OrganizationResponse


ALLOWED_JOB_STATUSES = {"DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED"}
ALLOWED_LOCATION_TYPES = {"REMOTE", "HYBRID", "ON_SITE"}
ALLOWED_EMPLOYMENT_TYPES = {"FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP"}
ALLOWED_EXPERIENCE_LEVELS = {"ENTRY", "MID", "SENIOR", "LEAD", "EXECUTIVE"}


class JobPostingSkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip()


class JobPostingSkillResponse(BaseModel):
    id: UUID
    job_posting_id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class JobPostingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job Title")
    description: str = Field(..., min_length=1, description="Job Description")
    requirements: Optional[str] = Field(None, description="Requirements and qualifications")
    location: Optional[str] = Field(None, max_length=255, description="Location (City, Country)")
    location_type: str = Field("ON_SITE", description="REMOTE, HYBRID, or ON_SITE")
    employment_type: str = Field("FULL_TIME", description="FULL_TIME, PART_TIME, CONTRACT, or INTERNSHIP")
    experience_level: Optional[str] = Field(None, max_length=50, description="ENTRY, MID, SENIOR, LEAD, or EXECUTIVE")
    compensation_min: Optional[Decimal] = Field(None, ge=0, description="Minimum compensation")
    compensation_max: Optional[Decimal] = Field(None, ge=0, description="Maximum compensation")
    compensation_currency: str = Field("INR", max_length=10, description="ISO currency code, default INR")
    deadline_date: Optional[date] = Field(None, description="Application closing date")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Job title cannot be empty")
        return v

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ALLOWED_LOCATION_TYPES:
            raise ValueError(f"location_type must be one of: {', '.join(sorted(ALLOWED_LOCATION_TYPES))}")
        return v_upper

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ALLOWED_EMPLOYMENT_TYPES:
            raise ValueError(f"employment_type must be one of: {', '.join(sorted(ALLOWED_EMPLOYMENT_TYPES))}")
        return v_upper

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_EXPERIENCE_LEVELS:
                raise ValueError(f"experience_level must be one of: {', '.join(sorted(ALLOWED_EXPERIENCE_LEVELS))}")
            return v_upper
        return v

    @field_validator("compensation_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.strip().upper()


class JobPostingCreate(JobPostingBase):
    skills: list[str] = Field(default_factory=list, description="List of required or relevant skill names")


class JobPostingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    location_type: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    compensation_min: Optional[Decimal] = Field(None, ge=0)
    compensation_max: Optional[Decimal] = Field(None, ge=0)
    compensation_currency: Optional[str] = Field(None, max_length=10)
    deadline_date: Optional[date] = None
    skills: Optional[list[str]] = None

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_LOCATION_TYPES:
                raise ValueError(f"location_type must be one of: {', '.join(sorted(ALLOWED_LOCATION_TYPES))}")
            return v_upper
        return v

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_EMPLOYMENT_TYPES:
                raise ValueError(f"employment_type must be one of: {', '.join(sorted(ALLOWED_EMPLOYMENT_TYPES))}")
            return v_upper
        return v

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ALLOWED_EXPERIENCE_LEVELS:
                raise ValueError(f"experience_level must be one of: {', '.join(sorted(ALLOWED_EXPERIENCE_LEVELS))}")
            return v_upper
        return v


class JobPostingResponse(JobPostingBase):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    skills: list[JobPostingSkillResponse] = Field(default_factory=list)
    organization_name: Optional[str] = None
    applicant_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class JobPostingDetailResponse(JobPostingResponse):
    organization: Optional[OrganizationResponse] = None
    has_applied: Optional[bool] = False
    saved_opportunity_id: Optional[UUID] = None
