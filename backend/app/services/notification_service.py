"""
Notification service — deterministic in-app alert engine with idempotent event synchronization.
Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationFollowup
from app.models.interview import Interview
from app.models.notification import Notification
from app.models.task import Task
from app.schemas.common import PaginationParams
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationType,
)


class NotificationService:
    @staticmethod
    def _build_response(notif: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            title=notif.title,
            body=notif.body,
            notification_type=notif.notification_type,
            is_read=notif.is_read,
            read_at=notif.read_at,
            related_type=notif.related_type,
            related_id=notif.related_id,
            created_at=notif.created_at,
        )

    async def sync_notifications(self, db: AsyncSession, user_id: UUID) -> None:
        """
        Idempotently scans for upcoming/due candidate events and creates in-app notifications.
        Duplicate prevention: verifies existing (user_id, notification_type, related_id) before inserting.
        No Redis/Celery required; purely local & deterministic.
        """
        now = datetime.now(timezone.utc)
        today = date.today()
        new_notifications = []

        # 1. Upcoming Interviews within 48 hours
        window_end = now + timedelta(hours=48)
        int_stmt = (
            select(Interview)
            .where(
                Interview.user_id == user_id,
                Interview.status != "CANCELLED",
                Interview.scheduled_at >= now - timedelta(hours=2),  # include very recent
                Interview.scheduled_at <= window_end,
            )
            .options(selectinload(Interview.application))
        )
        upcoming_interviews = (await db.execute(int_stmt)).scalars().all()
        for item in upcoming_interviews:
            # Check for existing notification for this interview
            dup_stmt = select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.notification_type == NotificationType.INTERVIEW_REMINDER.value,
                Notification.related_id == item.id,
            )
            exists = (await db.execute(dup_stmt)).scalar_one_or_none()
            if not exists:
                comp_name = item.application.company_name if item.application else "Upcoming"
                stage_name = item.stage or item.interview_type or "Interview"
                time_str = item.scheduled_at.strftime("%b %d at %H:%M UTC") if item.scheduled_at else "soon"
                new_notifications.append(
                    Notification(
                        user_id=user_id,
                        title=f"Interview Reminder: {comp_name} ({stage_name})",
                        body=f"Your {stage_name} is scheduled for {time_str}. Make sure your preparation notes and questions are ready.",
                        notification_type=NotificationType.INTERVIEW_REMINDER.value,
                        related_type="INTERVIEW",
                        related_id=item.id,
                    )
                )

        # 2. Tasks Due Today or Overdue
        task_stmt = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.is_completed.is_(False),
                Task.due_date.isnot(None),
                Task.due_date <= today,
            )
        )
        due_tasks = (await db.execute(task_stmt)).scalars().all()
        for t in due_tasks:
            dup_stmt = select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.notification_type == NotificationType.TASK_DUE.value,
                Notification.related_id == t.id,
            )
            exists = (await db.execute(dup_stmt)).scalar_one_or_none()
            if not exists:
                status_desc = "due today" if t.due_date == today else f"overdue (due {t.due_date})"
                new_notifications.append(
                    Notification(
                        user_id=user_id,
                        title=f"Task Due: {t.title}",
                        body=f"This task is {status_desc}. Priority: {t.priority}.",
                        notification_type=NotificationType.TASK_DUE.value,
                        related_type="TASK",
                        related_id=t.id,
                    )
                )

        # 3. Application Follow-ups Due Today or Overdue
        followup_stmt = (
            select(ApplicationFollowup)
            .where(
                ApplicationFollowup.user_id == user_id,
                ApplicationFollowup.is_completed.is_(False),
                ApplicationFollowup.due_date.isnot(None),
                ApplicationFollowup.due_date <= today,
            )
            .options(selectinload(ApplicationFollowup.application))
        )
        due_followups = (await db.execute(followup_stmt)).scalars().all()
        for f in due_followups:
            dup_stmt = select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.notification_type == NotificationType.FOLLOW_UP_DUE.value,
                Notification.related_id == f.id,
            )
            exists = (await db.execute(dup_stmt)).scalar_one_or_none()
            if not exists:
                comp_name = f.application.company_name if f.application else "Application"
                job_title = f.application.job_title if f.application else "Role"
                new_notifications.append(
                    Notification(
                        user_id=user_id,
                        title=f"Follow-up Due: {job_title} @ {comp_name}",
                        body=f.note or f"Action needed for {comp_name} follow-up.",
                        notification_type=NotificationType.FOLLOW_UP_DUE.value,
                        related_type="APPLICATION",
                        related_id=f.application_id,
                    )
                )

        if new_notifications:
            db.add_all(new_notifications)
            await db.commit()

    async def list_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        is_read: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> NotificationListResponse:
        # Idempotently synchronize pending alerts first
        await self.sync_notifications(db, user_id)

        base_query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            base_query = base_query.where(Notification.is_read == is_read)

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 50
        offset = (page - 1) * page_size

        stmt = base_query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)
        notifs = (await db.execute(stmt)).scalars().all()

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        items = [self._build_response(n) for n in notifs]
        return NotificationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        await self.sync_notifications(db, user_id)
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        return (await db.execute(stmt)).scalar_one()

    async def mark_as_read(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_id: UUID,
    ) -> NotificationResponse:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        notif = (await db.execute(stmt)).scalar_one_or_none()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notif)
        return self._build_response(notif)

    async def mark_all_as_read(self, db: AsyncSession, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount

    async def delete_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_id: UUID,
    ) -> None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        notif = (await db.execute(stmt)).scalar_one_or_none()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        await db.delete(notif)
        await db.commit()


notification_service = NotificationService()
