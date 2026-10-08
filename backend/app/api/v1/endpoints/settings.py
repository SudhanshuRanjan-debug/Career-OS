"""
Settings, Security, Sessions & GDPR Data Export API Router.
Stage 9: Analytics & Settings.
Strict user isolation via current_user.id.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import SessionResponse
from app.schemas.common import MessageResponse
from app.schemas.settings import (
    AccountDetailsResponse,
    AccountUpdateRequest,
    ChangePasswordRequest,
    DataExportResponse,
    DeleteAccountRequest,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)
from app.services.settings_service import settings_service

router = APIRouter()


# -----------------------------------------------------------------------------
# Account Details & Profile Settings
# -----------------------------------------------------------------------------

@router.get("/account", response_model=AccountDetailsResponse, summary="Get Account Details")
async def get_account_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve user account information and status."""
    return await settings_service.get_account(db=db, user_id=current_user.id)


@router.put("/account", response_model=AccountDetailsResponse, summary="Update Account Details")
async def update_account_details(
    data: AccountUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update username or email with duplicate validation."""
    return await settings_service.update_account(
        db=db, user_id=current_user.id, data=data
    )


# -----------------------------------------------------------------------------
# Security & Password
# -----------------------------------------------------------------------------

@router.put("/security/password", response_model=MessageResponse, summary="Change Password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password, verifying current credentials and invalidating active sessions."""
    await settings_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password successfully updated. All other sessions revoked.")


# -----------------------------------------------------------------------------
# Sessions Management
# -----------------------------------------------------------------------------

@router.get("/sessions", response_model=List[SessionResponse], summary="List Active Sessions")
async def list_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List authenticated active refresh sessions across candidate devices."""
    current_cookie = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    return await settings_service.list_sessions(
        db=db, user_id=current_user.id, current_cookie=current_cookie
    )


@router.delete("/sessions/{session_id}", response_model=MessageResponse, summary="Revoke Specific Session")
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific user session."""
    await settings_service.revoke_session(
        db=db, user_id=current_user.id, session_id=session_id
    )
    return MessageResponse(message="Session revoked successfully.")


@router.delete("/sessions", response_model=MessageResponse, summary="Revoke All Other Sessions")
async def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all active sessions except the current device."""
    current_cookie = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    count = await settings_service.revoke_all_sessions(
        db=db, user_id=current_user.id, current_cookie=current_cookie
    )
    return MessageResponse(message=f"Revoked {count} other active session(s).")


# -----------------------------------------------------------------------------
# Notification Preferences
# -----------------------------------------------------------------------------

@router.get("/notifications", response_model=NotificationSettingsResponse, summary="Get Notification Settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get in-app notification preference switches."""
    return await settings_service.get_notification_settings(db=db, user_id=current_user.id)


@router.put("/notifications", response_model=NotificationSettingsResponse, summary="Update Notification Settings")
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update in-app notification preference switches."""
    return await settings_service.update_notification_settings(
        db=db, user_id=current_user.id, data=data
    )


# -----------------------------------------------------------------------------
# GDPR Data Export
# -----------------------------------------------------------------------------

@router.post("/data-export", response_model=DataExportResponse, summary="GDPR Complete Data Export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and export a complete GDPR archive of all candidate records."""
    return await settings_service.export_user_data(db=db, user_id=current_user.id)


# -----------------------------------------------------------------------------
# Account Deletion
# -----------------------------------------------------------------------------

@router.delete("/account", response_model=MessageResponse, summary="Delete Account")
async def delete_account(
    data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete user account and all personal job application data."""
    await settings_service.delete_account(
        db=db, user_id=current_user.id, password=data.password
    )
    return MessageResponse(message="Account and all associated records permanently purged.")
