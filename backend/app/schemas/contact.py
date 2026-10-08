"""
Contact schemas — recruiter, manager, interviewer, and referral network directory.
Pydantic v2 schemas for Stage 6: Network / Contacts.
"""

import re
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanySummary, validate_safe_url


EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

ALLOWED_CONTACT_TYPES = {
    "RECRUITER",
    "HIRING_MANAGER",
    "INTERVIEWER",
    "EMPLOYEE",
    "REFERRAL",
    "OTHER",
}


class ApplicationSummary(BaseModel):
    id: UUID
    job_title: str
    company_name: str
    current_stage: str
    status: str
    applied_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Contact First Name")
    last_name: Optional[str] = Field(None, max_length=100, description="Contact Last Name")
    role: Optional[str] = Field(None, max_length=255, description="Job title or professional role")
    contact_type: Optional[str] = Field(
        "RECRUITER",
        max_length=30,
        description="RECRUITER, HIRING_MANAGER, INTERVIEWER, EMPLOYEE, REFERRAL, or OTHER",
    )
    email: Optional[str] = Field(None, max_length=255, pattern=EMAIL_REGEX, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=30, description="Phone number")
    linkedin_url: Optional[str] = Field(None, max_length=500, description="LinkedIn profile URL")
    relationship: Optional[str] = Field(None, max_length=100, description="Relationship context")
    notes: Optional[str] = Field(None, description="Private candidate notes regarding this contact")
    company_id: Optional[UUID] = Field(None, description="Optional associated target company")

    @field_validator("first_name", mode="before")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("First name cannot be empty")
        return v

    @field_validator("last_name", "role", "relationship", mode="before")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip().lower()
            return v if v else None
        return v

    @field_validator("contact_type")
    @classmethod
    def validate_contact_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_CONTACT_TYPES:
                raise ValueError(
                    f"Invalid contact type: {v}. Must be one of {sorted(ALLOWED_CONTACT_TYPES)}"
                )
            return v_upper
        return v

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=255)
    contact_type: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=255, pattern=EMAIL_REGEX)
    phone: Optional[str] = Field(None, max_length=30)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    relationship: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    company_id: Optional[UUID] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip().lower()
            return v if v else None
        return v

    @field_validator("first_name", mode="before")
    @classmethod
    def validate_first_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("First name cannot be empty")
        return v

    @field_validator("contact_type")
    @classmethod
    def validate_contact_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_CONTACT_TYPES:
                raise ValueError(
                    f"Invalid contact type: {v}. Must be one of {sorted(ALLOWED_CONTACT_TYPES)}"
                )
            return v_upper
        return v

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)


class ContactSummary(BaseModel):
    id: UUID
    first_name: str
    last_name: Optional[str] = None
    role: Optional[str] = None
    contact_type: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContactResponse(ContactBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanySummary] = None

    model_config = ConfigDict(from_attributes=True)


class ContactDetailResponse(ContactResponse):
    linked_applications: List[ApplicationSummary] = []


class ContactListResponse(PaginatedResponse[ContactResponse]):
    pass
