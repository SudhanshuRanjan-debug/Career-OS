"""
Candidate Profile, Preferences, Completeness, and Normalized Item Schemas.
"""

from __future__ import annotations

from datetime import date as dt_date, datetime as dt_datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Personal Information Schemas
# ---------------------------------------------------------------------------

class PersonalInfoUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    preferred_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=30)
    location_city: str | None = Field(None, max_length=100)
    location_state: str | None = Field(None, max_length=100)
    location_country: str | None = Field(None, max_length=100)
    timezone: str | None = Field(None, max_length=60)
    headline: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=500)
    profile_photo_key: str | None = Field(None, max_length=500)


class PersonalInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    preferred_name: str | None = None
    phone: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    timezone: str | None = None
    headline: str | None = None
    website: str | None = None
    profile_photo_key: str | None = None
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 2. Professional Information Schemas
# ---------------------------------------------------------------------------

class ProfessionalInfoUpdate(BaseModel):
    headline: str | None = Field(None, max_length=255)
    professional_summary: str | None = None
    career_objective: str | None = None
    current_role: str | None = Field(None, max_length=150)
    total_experience_yrs: Decimal | None = Field(None, ge=0, le=70)
    notice_period_days: int | None = Field(None, ge=0, le=365)
    open_to_work: bool = True
    website: str | None = Field(None, max_length=500)


class ProfessionalInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    headline: str | None = None
    professional_summary: str | None = None
    career_objective: str | None = None
    current_role: str | None = None
    total_experience_yrs: Decimal | None = None
    notice_period_days: int | None = None
    open_to_work: bool = True
    website: str | None = None
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 3. Job Preferences Schemas
# ---------------------------------------------------------------------------

class CandidatePreferencesUpdate(BaseModel):
    desired_job_titles: list[str] | None = None
    preferred_industries: list[str] | None = None
    preferred_locations: list[str] | None = None
    work_arrangement: str | None = Field(None, max_length=30)
    employment_type: list[str] | None = None
    min_compensation: Decimal | None = Field(None, ge=0)
    target_compensation: Decimal | None = Field(None, ge=0)
    compensation_currency: str = Field("USD", max_length=10)
    compensation_period: str = Field("ANNUAL", max_length=20)
    availability: str | None = Field(None, max_length=50)
    notice_period_days: int | None = Field(None, ge=0, le=365)
    work_authorization: list[str] | None = None
    relocation_preference: str | None = Field(None, max_length=30)
    preferred_company_sizes: list[str] | None = None
    notes: str | None = None


class CandidatePreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    desired_job_titles: list[str] | None = None
    preferred_industries: list[str] | None = None
    preferred_locations: list[str] | None = None
    work_arrangement: str | None = None
    employment_type: list[str] | None = None
    min_compensation: Decimal | None = None
    target_compensation: Decimal | None = None
    compensation_currency: str = "USD"
    compensation_period: str = "ANNUAL"
    availability: str | None = None
    notice_period_days: int | None = None
    work_authorization: list[str] | None = None
    relocation_preference: str | None = None
    preferred_company_sizes: list[str] | None = None
    notes: str | None = None
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 4. Education Schemas
# ---------------------------------------------------------------------------

class EducationCreate(BaseModel):
    institution: str = Field(..., min_length=1, max_length=255)
    degree: str | None = Field(None, max_length=100)
    field_of_study: str | None = Field(None, max_length=255)
    grade: str | None = Field(None, max_length=50)
    description: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool = False
    location: str | None = Field(None, max_length=255)
    sort_order: int = 0


class EducationUpdate(BaseModel):
    institution: str | None = Field(None, min_length=1, max_length=255)
    degree: str | None = Field(None, max_length=100)
    field_of_study: str | None = Field(None, max_length=255)
    grade: str | None = Field(None, max_length=50)
    description: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool | None = None
    location: str | None = Field(None, max_length=255)
    sort_order: int | None = None


class EducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    grade: str | None = None
    description: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool = False
    location: str | None = None
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 5. Experience Schemas
# ---------------------------------------------------------------------------

class ExperienceCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    employment_type: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    location_type: str | None = Field(None, max_length=20)
    description: str | None = None
    responsibilities: str | None = None
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool = False
    sort_order: int = 0


class ExperienceUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=255)
    title: str | None = Field(None, min_length=1, max_length=255)
    employment_type: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    location_type: str | None = Field(None, max_length=20)
    description: str | None = None
    responsibilities: str | None = None
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool | None = None
    sort_order: int | None = None


class ExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    company_name: str
    title: str
    employment_type: str | None = None
    location: str | None = None
    location_type: str | None = None
    description: str | None = None
    responsibilities: str | None = None
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_current: bool = False
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 6. Project Schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    role: str | None = Field(None, max_length=150)
    tech_stack: list[str] | None = None
    url: str | None = Field(None, max_length=500)
    repo_url: str | None = Field(None, max_length=500)
    project_type: str | None = Field(None, max_length=50)
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_ongoing: bool = False
    sort_order: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    role: str | None = Field(None, max_length=150)
    tech_stack: list[str] | None = None
    url: str | None = Field(None, max_length=500)
    repo_url: str | None = Field(None, max_length=500)
    project_type: str | None = Field(None, max_length=50)
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_ongoing: bool | None = None
    sort_order: int | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    role: str | None = None
    tech_stack: list[str] | None = None
    url: str | None = None
    repo_url: str | None = None
    project_type: str | None = None
    achievements: str | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    is_ongoing: bool = False
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 7. Skill Schemas
# ---------------------------------------------------------------------------

class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field("TECHNICAL", max_length=100)
    proficiency: str | None = Field("INTERMEDIATE", max_length=30)
    years_of_exp: Decimal | None = Field(None, ge=0, le=50)
    sort_order: int = 0


class SkillUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=30)
    years_of_exp: Decimal | None = Field(None, ge=0, le=50)
    sort_order: int | None = None


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    category: str | None = None
    proficiency: str | None = None
    years_of_exp: Decimal | None = None
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 8. Certification Schemas
# ---------------------------------------------------------------------------

class CertificationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    issuing_org: str | None = Field(None, max_length=255)
    issue_date: dt_date | None = None
    expiry_date: dt_date | None = None
    credential_id: str | None = Field(None, max_length=255)
    credential_url: str | None = Field(None, max_length=500)
    description: str | None = None
    sort_order: int = 0


class CertificationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    issuing_org: str | None = Field(None, max_length=255)
    issue_date: dt_date | None = None
    expiry_date: dt_date | None = None
    credential_id: str | None = Field(None, max_length=255)
    credential_url: str | None = Field(None, max_length=500)
    description: str | None = None
    sort_order: int | None = None


class CertificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    issuing_org: str | None = None
    issue_date: dt_date | None = None
    expiry_date: dt_date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    description: str | None = None
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 9. Achievement Schemas
# ---------------------------------------------------------------------------

class AchievementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    date: dt_date | None = None
    issuer: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=500)
    sort_order: int = 0


class AchievementUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    date: dt_date | None = None
    issuer: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=500)
    sort_order: int | None = None


class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str | None = None
    category: str | None = None
    date: dt_date | None = None
    issuer: str | None = None
    url: str | None = None
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 10. Language Schemas
# ---------------------------------------------------------------------------

class LanguageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    proficiency: str | None = Field("PROFICIENT", max_length=30)
    sort_order: int = 0


class LanguageUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    proficiency: str | None = Field(None, max_length=30)
    sort_order: int | None = None


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    proficiency: str | None = None
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 11. Profile Link Schemas
# ---------------------------------------------------------------------------

class ProfileLinkCreate(BaseModel):
    platform: str | None = Field(None, max_length=50)
    label: str | None = Field(None, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    sort_order: int = 0


class ProfileLinkUpdate(BaseModel):
    platform: str | None = Field(None, max_length=50)
    label: str | None = Field(None, max_length=100)
    url: str | None = Field(None, min_length=1, max_length=500)
    sort_order: int | None = None


class ProfileLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    platform: str | None = None
    label: str | None = None
    url: str
    sort_order: int = 0
    created_at: dt_datetime
    updated_at: dt_datetime


# ---------------------------------------------------------------------------
# 12. Completeness & Overview Schemas
# ---------------------------------------------------------------------------

class SectionCompleteness(BaseModel):
    completed: bool
    weight: int
    missing_fields: list[str]


class ProfileCompletenessResponse(BaseModel):
    overall_score: int
    sections: dict[str, SectionCompleteness]


class ProfileOverviewResponse(BaseModel):
    personal: PersonalInfoResponse | None = None
    professional: ProfessionalInfoResponse | None = None
    preferences: CandidatePreferencesResponse | None = None
    completeness: ProfileCompletenessResponse
    counts: dict[str, int]
