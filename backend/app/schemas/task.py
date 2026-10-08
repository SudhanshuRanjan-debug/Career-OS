"""
Task schemas — polymorphic action items, follow-ups, and career milestones.
Pydantic v2 schemas for Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanySummary
from app.schemas.contact import ApplicationSummary, ContactSummary
from app.schemas.interview import InterviewSummary


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskRelatedType(str, Enum):
    APPLICATION = "APPLICATION"
    INTERVIEW = "INTERVIEW"
    COMPANY = "COMPANY"
    CONTACT = "CONTACT"
    GENERAL = "GENERAL"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title / action item")
    description: Optional[str] = Field(None, description="Detailed task notes or instructions")
    due_date: Optional[date] = Field(None, description="Target completion date")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="LOW, MEDIUM, HIGH, URGENT")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="PENDING, IN_PROGRESS, COMPLETED, CANCELLED")

    # Polymorphic linkages
    related_type: Optional[TaskRelatedType] = Field(default=TaskRelatedType.GENERAL, description="Polymorphic entity category")
    application_id: Optional[UUID] = Field(None, description="Linked application ID")
    interview_id: Optional[UUID] = Field(None, description="Linked interview ID")
    company_id: Optional[UUID] = Field(None, description="Linked company ID")
    contact_id: Optional[UUID] = Field(None, description="Linked contact ID")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Task title cannot be empty")
        return v


    @model_validator(mode="before")
    @classmethod
    def validate_polymorphic_consistency(cls, data):
        if not isinstance(data, dict):
            return data

        rel_type = data.get("related_type")
        app_id = data.get("application_id")
        int_id = data.get("interview_id")
        comp_id = data.get("company_id")
        cont_id = data.get("contact_id")

        # Auto-infer related_type if omitted but exactly one ID is provided
        if not rel_type:
            if app_id:
                rel_type = TaskRelatedType.APPLICATION.value
                data["related_type"] = rel_type
            elif int_id:
                rel_type = TaskRelatedType.INTERVIEW.value
                data["related_type"] = rel_type
            elif comp_id:
                rel_type = TaskRelatedType.COMPANY.value
                data["related_type"] = rel_type
            elif cont_id:
                rel_type = TaskRelatedType.CONTACT.value
                data["related_type"] = rel_type
            else:
                rel_type = TaskRelatedType.GENERAL.value
                data["related_type"] = rel_type

        # Convert to string uppercase if enum/string
        if hasattr(rel_type, "value"):
            rel_type_str = rel_type.value
        else:
            rel_type_str = str(rel_type).upper() if rel_type else "GENERAL"

        # Enforce strict polymorphic consistency
        if rel_type_str == TaskRelatedType.APPLICATION.value:
            if not app_id:
                raise ValueError("application_id is required when related_type is APPLICATION")
            if int_id or comp_id or cont_id:
                raise ValueError("Only application_id may be specified when related_type is APPLICATION")
        elif rel_type_str == TaskRelatedType.INTERVIEW.value:
            if not int_id:
                raise ValueError("interview_id is required when related_type is INTERVIEW")
            if app_id or comp_id or cont_id:
                raise ValueError("Only interview_id may be specified when related_type is INTERVIEW")
        elif rel_type_str == TaskRelatedType.COMPANY.value:
            if not comp_id:
                raise ValueError("company_id is required when related_type is COMPANY")
            if app_id or int_id or cont_id:
                raise ValueError("Only company_id may be specified when related_type is COMPANY")
        elif rel_type_str == TaskRelatedType.CONTACT.value:
            if not cont_id:
                raise ValueError("contact_id is required when related_type is CONTACT")
            if app_id or int_id or comp_id:
                raise ValueError("Only contact_id may be specified when related_type is CONTACT")
        elif rel_type_str == TaskRelatedType.GENERAL.value:
            if app_id or int_id or comp_id or cont_id:
                raise ValueError("No linked entity IDs are allowed when related_type is GENERAL")

        return data


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    is_completed: Optional[bool] = None
    related_type: Optional[TaskRelatedType] = None
    application_id: Optional[UUID] = None
    interview_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None

    @model_validator(mode="before")
    @classmethod
    def validate_polymorphic_update(cls, data):
        if not isinstance(data, dict):
            return data

        rel_type = data.get("related_type")
        if rel_type is None:
            ids = [data.get(k) for k in ("application_id", "interview_id", "company_id", "contact_id") if data.get(k) is not None]
            if len(ids) > 1:
                raise ValueError("Only one linked entity ID may be set for a task")
            return data

        if hasattr(rel_type, "value"):
            rel_type_str = rel_type.value
        else:
            rel_type_str = str(rel_type).upper()

        app_id = data.get("application_id")
        int_id = data.get("interview_id")
        comp_id = data.get("company_id")
        cont_id = data.get("contact_id")

        if rel_type_str == TaskRelatedType.APPLICATION.value:
            if int_id or comp_id or cont_id:
                raise ValueError("Only application_id may be specified when related_type is APPLICATION")
        elif rel_type_str == TaskRelatedType.INTERVIEW.value:
            if app_id or comp_id or cont_id:
                raise ValueError("Only interview_id may be specified when related_type is INTERVIEW")
        elif rel_type_str == TaskRelatedType.COMPANY.value:
            if app_id or int_id or cont_id:
                raise ValueError("Only company_id may be specified when related_type is COMPANY")
        elif rel_type_str == TaskRelatedType.CONTACT.value:
            if app_id or int_id or comp_id:
                raise ValueError("Only contact_id may be specified when related_type is CONTACT")
        elif rel_type_str == TaskRelatedType.GENERAL.value:
            if app_id or int_id or comp_id or cont_id:
                raise ValueError("No linked entity IDs are allowed when related_type is GENERAL")

        return data


class TaskSummary(BaseModel):
    id: UUID
    title: str
    priority: str
    status: str
    due_date: Optional[date] = None
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    is_completed: bool
    completed_at: Optional[datetime] = None

    related_type: Optional[str] = None
    application_id: Optional[UUID] = None
    interview_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None

    application: Optional[ApplicationSummary] = None
    interview: Optional[InterviewSummary] = None
    company: Optional[CompanySummary] = None
    contact: Optional[ContactSummary] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(PaginatedResponse[TaskResponse]):
    pass
