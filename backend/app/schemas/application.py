"""
Pydantic schemas for the Application domain and deterministic Health Engine.
Stage 5 Master Implementation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedResponse
from app.schemas.contact import ContactSummary


ALLOWED_APPLICATION_STAGES = {
    "APPLIED",
    "PHONE_SCREEN",
    "ASSESSMENT",
    "INTERVIEW",
    "OFFER",
    "ACCEPTED",
    "REJECTED",
    "WITHDRAWN",
}

ALLOWED_APPLICATION_STATUSES = {"ACTIVE", "CLOSED", "ARCHIVED"}
ALLOWED_APPLICATION_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}
ALLOWED_APPLICATION_OUTCOMES = {"ACCEPTED", "REJECTED", "WITHDRAWN", "OFFER_DECLINED"}
HEALTH_STATUSES = {"EXCELLENT", "GOOD", "NEEDS_ATTENTION", "POOR"}


# ---------------------------------------------------------------------------
# Application Base & CRUD Schemas
# ---------------------------------------------------------------------------

class ApplicationBase(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=255, description="Job / Role Title")
    company_name: str = Field(..., min_length=1, max_length=255, description="Employer / Company Name")
    company_id: Optional[UUID] = Field(None, description="Optional foreign key to registered company")
    opportunity_id: Optional[UUID] = Field(None, description="Optional foreign key to source opportunity")
    job_posting_id: Optional[UUID] = Field(None, description="Optional foreign key to platform job posting")
    contact_id: Optional[UUID] = Field(None, description="Primary recruiter or contact")
    job_location: Optional[str] = Field(None, max_length=255)
    job_location_type: Optional[str] = Field(None, max_length=20)
    employment_type: Optional[str] = Field(None, max_length=50)
    job_description: Optional[str] = Field(None)
    job_url: Optional[str] = Field(None, max_length=1000)
    compensation_min: Optional[Decimal] = Field(None, ge=0)
    compensation_max: Optional[Decimal] = Field(None, ge=0)
    compensation_currency: Optional[str] = Field("USD", max_length=10)
    source: Optional[str] = Field(None, max_length=100)
    status: str = Field("ACTIVE", max_length=20)
    current_stage: str = Field("APPLIED", max_length=50)
    applied_date: Optional[date] = Field(None)
    deadline_date: Optional[date] = Field(None)
    resume_id: Optional[UUID] = Field(None, description="Locked resume version reference")
    cover_letter_doc_id: Optional[UUID] = Field(None, description="Locked cover letter reference")
    priority: str = Field("MEDIUM", max_length=20)
    outcome: Optional[str] = Field(None, max_length=50)

    @field_validator("job_title", "company_name", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field must not be empty or whitespace only")
        return v

    @field_validator("current_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in ALLOWED_APPLICATION_STAGES:
            raise ValueError(f"Invalid application stage: {v}. Must be one of {sorted(ALLOWED_APPLICATION_STAGES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_APPLICATION_STATUSES:
            raise ValueError(f"Invalid status: {v}. Must be one of {sorted(ALLOWED_APPLICATION_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ALLOWED_APPLICATION_PRIORITIES:
            raise ValueError(f"Invalid priority: {v}. Must be one of {sorted(ALLOWED_APPLICATION_PRIORITIES)}")
        return v

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_APPLICATION_OUTCOMES:
            raise ValueError(f"Invalid outcome: {v}. Must be one of {sorted(ALLOWED_APPLICATION_OUTCOMES)}")
        return v


class ApplicationCreate(ApplicationBase):
    initial_notes: Optional[str] = Field(None, description="Initial note recorded upon creation")


class ApplicationUpdate(BaseModel):
    job_title: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    job_location: Optional[str] = None
    job_location_type: Optional[str] = None
    employment_type: Optional[str] = None
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    compensation_min: Optional[Decimal] = Field(None, ge=0)
    compensation_max: Optional[Decimal] = Field(None, ge=0)
    compensation_currency: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    current_stage: Optional[str] = None
    applied_date: Optional[date] = None
    deadline_date: Optional[date] = None
    resume_id: Optional[UUID] = None
    cover_letter_doc_id: Optional[UUID] = None
    priority: Optional[str] = None
    outcome: Optional[str] = None

    @field_validator("current_stage")
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_APPLICATION_STAGES:
            raise ValueError(f"Invalid application stage: {v}. Must be one of {sorted(ALLOWED_APPLICATION_STAGES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_APPLICATION_STATUSES:
            raise ValueError(f"Invalid status: {v}. Must be one of {sorted(ALLOWED_APPLICATION_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_APPLICATION_PRIORITIES:
            raise ValueError(f"Invalid priority: {v}. Must be one of {sorted(ALLOWED_APPLICATION_PRIORITIES)}")
        return v


class ApplicationConvertRequest(BaseModel):
    resume_id: Optional[UUID] = Field(None, description="Locked resume version")
    cover_letter_doc_id: Optional[UUID] = Field(None, description="Locked cover letter document")
    current_stage: str = Field("APPLIED", description="Initial application stage")
    applied_date: Optional[date] = Field(None, description="Date applied (defaults to today)")
    priority: str = Field("MEDIUM", description="Application priority")
    initial_notes: Optional[str] = Field(None, description="Optional note recorded upon conversion")

    @field_validator("current_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in ALLOWED_APPLICATION_STAGES:
            raise ValueError(f"Invalid application stage: {v}")
        return v


class ResumeSnapshotInfo(BaseModel):
    id: UUID
    name: str
    original_filename: str
    version: int

    model_config = ConfigDict(from_attributes=True)


class ApplicationHealthCheck(BaseModel):
    check_id: str
    name: str
    category: str = Field(..., description="REQUIRED, PENALTY, or SUGGESTION")
    passed: bool
    impact: int
    message: str


class ApplicationHealthResponse(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Deterministic Health Score (0-100)")
    status: str = Field(..., description="EXCELLENT, GOOD, NEEDS_ATTENTION, or POOR")
    checks: List[ApplicationHealthCheck]


class ApplicationResponse(ApplicationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    resume: Optional[ResumeSnapshotInfo] = None
    contact: Optional[ContactSummary] = None
    health: Optional[ApplicationHealthResponse] = None
    notes_count: Optional[int] = 0
    followups_count: Optional[int] = 0
    documents_count: Optional[int] = 0
    interviews_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(PaginatedResponse[ApplicationResponse]):
    pass


# ---------------------------------------------------------------------------
# Stage Transitions & Stage History
# ---------------------------------------------------------------------------

class StageTransitionRequest(BaseModel):
    to_stage: str = Field(..., description="Target recruitment stage")
    notes: Optional[str] = Field(None, description="Notes explaining stage change")

    @field_validator("to_stage")
    @classmethod
    def validate_to_stage(cls, v: str) -> str:
        if v not in ALLOWED_APPLICATION_STAGES:
            raise ValueError(f"Invalid target stage: {v}. Must be one of {sorted(ALLOWED_APPLICATION_STAGES)}")
        return v


class StageHistoryResponse(BaseModel):
    id: UUID
    application_id: UUID
    from_stage: Optional[str] = None
    to_stage: str
    changed_at: datetime
    notes: Optional[str] = None
    changed_by_user: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Application Notes
# ---------------------------------------------------------------------------

class ApplicationNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Note content")

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Note content must not be empty")
        return v


class ApplicationNoteUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="Updated note content")

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Note content must not be empty")
        return v


class ApplicationNoteResponse(BaseModel):
    id: UUID
    application_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Application Follow-ups
# ---------------------------------------------------------------------------

class ApplicationFollowupCreate(BaseModel):
    due_date: Optional[date] = Field(None, description="Due date for followup reminder")
    note: Optional[str] = Field(None, description="Followup action details")


class ApplicationFollowupUpdate(BaseModel):
    due_date: Optional[date] = None
    note: Optional[str] = None
    is_completed: Optional[bool] = None


class ApplicationFollowupResponse(BaseModel):
    id: UUID
    application_id: UUID
    user_id: UUID
    due_date: Optional[date] = None
    note: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationFollowupWithAppResponse(ApplicationFollowupResponse):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    current_stage: Optional[str] = None
    application_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Application Documents
# ---------------------------------------------------------------------------

class ApplicationDocumentAttach(BaseModel):
    document_id: UUID = Field(..., description="Document ID from document vault")


class DocumentMetaSummary(BaseModel):
    id: UUID
    name: str
    original_filename: str
    doc_type: str
    file_size_bytes: int

    model_config = ConfigDict(from_attributes=True)


class ApplicationDocumentResponse(BaseModel):
    id: UUID
    application_id: UUID
    document_id: UUID
    attached_at: datetime
    document: Optional[DocumentMetaSummary] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Application Activity Timeline
# ---------------------------------------------------------------------------

class ApplicationActivityResponse(BaseModel):
    id: UUID
    application_id: UUID
    user_id: UUID
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Pipeline (Kanban) Representation
# ---------------------------------------------------------------------------

class PipelineColumnResponse(BaseModel):
    stage: str
    name: str
    count: int
    items: List[ApplicationResponse]


class PipelineResponse(BaseModel):
    columns: List[PipelineColumnResponse]
    total_active: int


# ---------------------------------------------------------------------------
# Two-Sided Platform: Job Application & Recruiter Review
# ---------------------------------------------------------------------------

class JobApplyRequest(BaseModel):
    resume_id: UUID = Field(..., description="Candidate locked resume ID to submit")
    cover_letter_doc_id: Optional[UUID] = Field(None, description="Optional cover letter document ID")
    notes: Optional[str] = Field(None, description="Optional candidate note or application message")


class CandidateApplicationSummary(BaseModel):
    candidate_user_id: UUID
    full_name: Optional[str] = None
    headline: Optional[str] = None
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicantListItem(BaseModel):
    application_id: UUID
    job_posting_id: UUID
    candidate: CandidateApplicationSummary
    current_stage: str
    status: str
    applied_date: Optional[date] = None
    created_at: datetime
    resume_id: Optional[UUID] = None
    resume_name: Optional[str] = None
    resume_filename: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicantDetailResponse(BaseModel):
    application_id: UUID
    job_posting_id: UUID
    job_title: str
    candidate: CandidateApplicationSummary
    current_stage: str
    status: str
    applied_date: Optional[date] = None
    created_at: datetime
    resume: Optional[ResumeSnapshotInfo] = None
    cover_letter_doc_id: Optional[UUID] = None
    cover_notes: Optional[str] = None
    stage_history: List[StageHistoryResponse] = Field(default_factory=list)
    notes: List[ApplicationNoteResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
