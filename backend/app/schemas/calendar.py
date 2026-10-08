"""
Calendar schemas — unified schedule event aggregation.
Pydantic v2 schemas for Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date as dt_date, datetime as dt_datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CalendarEventType(str, Enum):
    INTERVIEW = "INTERVIEW"
    TASK = "TASK"
    FOLLOW_UP = "FOLLOW_UP"
    DEADLINE = "DEADLINE"


class CalendarEventResponse(BaseModel):
    id: str = Field(..., description="Unique event identifier (e.g. interview-{uuid})")
    entity_id: UUID = Field(..., description="Underlying database entity ID")
    event_type: CalendarEventType = Field(..., description="INTERVIEW, TASK, FOLLOW_UP, DEADLINE")
    title: str = Field(..., description="Event display title")
    description: Optional[str] = Field(None, description="Event description or notes")
    date: dt_date = Field(..., description="Primary date of the event")
    start_time: Optional[dt_datetime] = Field(None, description="Event start timestamp if time-specific")
    end_time: Optional[dt_datetime] = Field(None, description="Event end timestamp if time-specific")
    all_day: bool = Field(default=False, description="Whether the event spans the entire day")
    status: Optional[str] = Field(None, description="Entity status (e.g. SCHEDULED, PENDING, COMPLETED)")
    priority: Optional[str] = Field(None, description="Entity priority (e.g. HIGH, MEDIUM)")
    color: Optional[str] = Field(None, description="UI accent color token (e.g. blue, amber, emerald, purple)")
    meeting_link: Optional[str] = Field(None, description="Virtual meeting URL for interviews")

    # Associated context
    related_type: Optional[str] = Field(None, description="APPLICATION, INTERVIEW, COMPANY, CONTACT")
    related_id: Optional[UUID] = Field(None, description="Foreign key to related parent entity")
    company_name: Optional[str] = Field(None, description="Company name context")
    job_title: Optional[str] = Field(None, description="Application job title context")

    model_config = ConfigDict(from_attributes=True)


class CalendarScheduleResponse(BaseModel):
    events: List[CalendarEventResponse]
    total_events: int
    start_date: Optional[dt_date] = None
    end_date: Optional[dt_date] = None
