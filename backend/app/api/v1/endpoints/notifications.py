"""
In-app Notifications API endpoints — deterministic alerts, interview reminders, and milestone tracking.
Stage 8: Tasks, Calendar & Notifications.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationParams
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List in-app notifications with idempotent background sync and tenant isolation."""
    pagination = PaginationParams(page=page, page_size=page_size)
    return await notification_service.list_notifications(
        db=db,
        user_id=current_user.id,
        is_read=is_read,
        pagination=pagination,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current count of unread notifications for TopBar bell badge."""
    count = await notification_service.get_unread_count(
        db=db,
        user_id=current_user.id,
    )
    return NotificationUnreadCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    return await notification_service.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all unread notifications for the current user as read."""
    updated = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )
    return MessageResponse(message=f"Marked {updated} notifications as read")


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    await notification_service.delete_notification(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return MessageResponse(message="Notification deleted successfully")
