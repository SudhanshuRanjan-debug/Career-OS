"""
Notification schemas — in-app alerts, interview reminders, and milestone notifications.
Pydantic v2 schemas for Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import PaginatedResponse


class NotificationType(str, Enum):
    INTERVIEW_REMINDER = "INTERVIEW_REMINDER"
    TASK_DUE = "TASK_DUE"
    FOLLOW_UP_DUE = "FOLLOW_UP_DUE"
    DEADLINE = "DEADLINE"
    SYSTEM = "SYSTEM"


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: Optional[str] = None
    notification_type: NotificationType = NotificationType.SYSTEM
    related_type: Optional[str] = Field(None, max_length=30)
    related_id: Optional[UUID] = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: Optional[str] = None
    notification_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    related_type: Optional[str] = None
    related_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    pass
