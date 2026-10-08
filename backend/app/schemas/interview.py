"""
Interview and Interview Preparation schemas.
Pydantic v2 schemas for Stage 7: Interviews & Interview Preparation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanySummary, validate_safe_url
from app.schemas.contact import ApplicationSummary, ContactSummary


ALLOWED_INTERVIEW_TYPES = {
    "PHONE",
    "VIDEO",
    "ON_SITE",
    "TECHNICAL",
    "PANEL",
    "HR",
    "SYSTEM_DESIGN",
    "BEHAVIORAL",
}

ALLOWED_INTERVIEW_STATUSES = {
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    "RESCHEDULED",
}

ALLOWED_INTERVIEW_RESULTS = {
    "PASSED",
    "FAILED",
    "PENDING",
    "CANCELLED",
}


# ===========================================================================
# 1. Interview Preparation Checklist Item & Schemas
# ===========================================================================

class PreparationChecklistItem(BaseModel):
    id: str = Field(..., description="Unique ID for checklist item")
    label: str = Field(..., min_length=1, max_length=255, description="Actionable checklist item text")
    done: bool = Field(False, description="Whether checklist item is completed")


class InterviewPreparationBase(BaseModel):
    company_research: Optional[str] = Field(None, description="Company background, engineering blog notes, tech stack")
    role_research: Optional[str] = Field(None, description="Role expectations, key competencies, team scope")
    questions_to_ask: Optional[str] = Field(None, description="Questions prepared to ask the interviewers")
    personal_notes: Optional[str] = Field(None, description="Anticipated questions, STAR stories, architecture cheat sheet")
    preparation_checklist: Optional[List[Dict[str, Any]]] = Field(
        None, description="Array of checklist items {id, label, done}"
    )
    post_interview_notes: Optional[str] = Field(None, description="Debrief reflections, unexpected questions, follow-up items")


class InterviewPreparationCreate(InterviewPreparationBase):
    pass


class InterviewPreparationUpdate(InterviewPreparationBase):
    pass


class InterviewPreparationResponse(InterviewPreparationBase):
    id: UUID
    interview_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 2. Interview Schemas
# ===========================================================================

class InterviewBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Interview title or session topic")
    interview_type: Optional[str] = Field(
        "TECHNICAL",
        max_length=50,
        description="PHONE, VIDEO, ON_SITE, TECHNICAL, PANEL, HR, SYSTEM_DESIGN, or BEHAVIORAL",
    )
    stage: Optional[str] = Field(
        None,
        max_length=100,
        validation_alias=AliasChoices("stage", "round_name"),
        description="Round name or stage label (e.g. Round 1, Screen)",
    )
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled date and time (UTC / timezone-aware)")
    duration_mins: Optional[int] = Field(
        None,
        ge=1,
        le=1440,
        validation_alias=AliasChoices("duration_mins", "duration_minutes"),
        description="Estimated duration in minutes",
    )
    meeting_link: Optional[str] = Field(
        None,
        max_length=500,
        validation_alias=AliasChoices("meeting_link", "meeting_url"),
        description="Video conference or call URL",
    )
    location: Optional[str] = Field(None, max_length=255, description="Physical location or meeting platform")
    status: str = Field("SCHEDULED", max_length=20, description="SCHEDULED, COMPLETED, CANCELLED, or RESCHEDULED")
    result: Optional[str] = Field(None, max_length=30, description="PASSED, FAILED, PENDING, or CANCELLED")
    interviewer_names: Optional[List[str]] = Field(None, description="Names of interviewers on the panel")
    notes: Optional[str] = Field(None, description="General session notes or agenda")

    @field_validator("interviewer_names", mode="before")
    @classmethod
    def normalize_interviewer_names(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts if parts else None
        if isinstance(v, (list, tuple, set)):
            return [str(p).strip() for p in v if str(p).strip()]
        return v

    @field_validator("title", "stage", "location", mode="before")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_TYPES:
                raise ValueError(
                    f"Invalid interview type: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_TYPES)}"
                )
            return v_upper
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if isinstance(v, str):
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_STATUSES:
                raise ValueError(
                    f"Invalid interview status: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_STATUSES)}"
                )
            return v_upper
        return v

    @field_validator("result")
    @classmethod
    def validate_result(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_RESULTS:
                raise ValueError(
                    f"Invalid interview result: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_RESULTS)}"
                )
            return v_upper
        return v

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)


class InterviewCreate(InterviewBase):
    application_id: Optional[UUID] = Field(None, description="Associated job application ID")
    company_id: Optional[UUID] = Field(None, description="Associated target company ID")
    contact_id: Optional[UUID] = Field(None, description="Primary interviewer contact ID")


class InterviewUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    interview_type: Optional[str] = Field(None, max_length=50)
    stage: Optional[str] = Field(None, max_length=100, validation_alias=AliasChoices("stage", "round_name"))
    scheduled_at: Optional[datetime] = None
    duration_mins: Optional[int] = Field(None, ge=1, le=1440, validation_alias=AliasChoices("duration_mins", "duration_minutes"))
    meeting_link: Optional[str] = Field(None, max_length=500, validation_alias=AliasChoices("meeting_link", "meeting_url"))
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=20)
    result: Optional[str] = Field(None, max_length=30)
    interviewer_names: Optional[List[str]] = None
    notes: Optional[str] = None
    feedback: Optional[str] = None
    application_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None

    @field_validator("interviewer_names", mode="before")
    @classmethod
    def normalize_interviewer_names(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts if parts else None
        if isinstance(v, (list, tuple, set)):
            return [str(p).strip() for p in v if str(p).strip()]
        return v

    @field_validator("title", "stage", "location", mode="before")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_TYPES:
                raise ValueError(
                    f"Invalid interview type: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_TYPES)}"
                )
            return v_upper
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_STATUSES:
                raise ValueError(
                    f"Invalid interview status: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_STATUSES)}"
                )
            return v_upper
        return v

    @field_validator("result")
    @classmethod
    def validate_result(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper not in ALLOWED_INTERVIEW_RESULTS:
                raise ValueError(
                    f"Invalid interview result: {v}. Must be one of {sorted(ALLOWED_INTERVIEW_RESULTS)}"
                )
            return v_upper
        return v

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_url(v)


class InterviewSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    interview_type: Optional[str] = None
    stage: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_mins: Optional[int] = None
    status: str
    result: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewResponse(InterviewBase):
    id: UUID
    user_id: UUID
    application_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    round_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    meeting_url: Optional[str] = None
    application: Optional[ApplicationSummary] = None
    company: Optional[CompanySummary] = None
    contact: Optional[ContactSummary] = None
    preparation: Optional[InterviewPreparationResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_aliases(self) -> "InterviewResponse":
        if not self.round_name:
            self.round_name = self.stage or self.title
        if self.duration_minutes is None:
            self.duration_minutes = self.duration_mins
        if not self.meeting_url:
            self.meeting_url = self.meeting_link
        return self


class InterviewListResponse(PaginatedResponse[InterviewResponse]):
    pass
