"""
Settings, Account & Security Pydantic Schemas.
Stage 9: Analytics & Settings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class AccountDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class AccountUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[str] = Field(None, max_length=255, pattern=EMAIL_REGEX)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current user password")
    new_password: str = Field(..., min_length=8, description="New strong password")


class NotificationSettingsResponse(BaseModel):
    in_app_alerts: bool = Field(True, description="Enable platform in-app notification toasts/alerts")
    interview_reminders: bool = Field(True, description="Alert for upcoming interviews within 24h")
    deadline_reminders: bool = Field(True, description="Alert for approaching application deadlines")
    task_reminders: bool = Field(True, description="Alert for tasks due today")


class NotificationSettingsUpdate(BaseModel):
    in_app_alerts: Optional[bool] = None
    interview_reminders: Optional[bool] = None
    deadline_reminders: Optional[bool] = None
    task_reminders: Optional[bool] = None


class DataExportResponse(BaseModel):
    exported_at: datetime
    user_id: str
    email: str
    data: Dict[str, Any]


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password confirmation to authorize account deletion")
