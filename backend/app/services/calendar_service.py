"""
Calendar service — pure read/aggregation layer over existing domain records.
Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date, datetime, time, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import cast, Date, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationFollowup
from app.models.interview import Interview
from app.models.task import Task
from app.schemas.calendar import (
    CalendarEventResponse,
    CalendarEventType,
    CalendarScheduleResponse,
)


class CalendarService:
    async def get_schedule(
        self,
        db: AsyncSession,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        event_types: Optional[List[str]] = None,
    ) -> CalendarScheduleResponse:
        """
        Pure aggregation across Interviews, Tasks, Follow-ups, and Application Deadlines.
        Maintains strict tenant isolation: user_id == current_user.id.
        """
        events: List[CalendarEventResponse] = []
        types_set = {t.upper() for t in event_types} if event_types else None

        # 1. Interviews
        if types_set is None or "INTERVIEW" in types_set:
            int_query = (
                select(Interview)
                .where(Interview.user_id == user_id)
                .options(selectinload(Interview.application))
            )
            if start_date:
                start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
                int_query = int_query.where(Interview.scheduled_at >= start_dt)
            if end_date:
                end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
                int_query = int_query.where(Interview.scheduled_at <= end_dt)

            int_results = (await db.execute(int_query)).scalars().all()
            for item in int_results:
                ev_date = item.scheduled_at.date() if item.scheduled_at else date.today()
                comp_name = item.application.company_name if item.application else None
                job_title = item.application.job_title if item.application else None
                display_stage = item.stage or item.interview_type or "Interview"
                title = f"{comp_name}: {display_stage}" if comp_name else f"Interview: {display_stage}"

                events.append(
                    CalendarEventResponse(
                        id=f"interview-{item.id}",
                        entity_id=item.id,
                        event_type=CalendarEventType.INTERVIEW,
                        title=title,
                        description=item.notes,
                        date=ev_date,
                        start_time=item.scheduled_at,
                        end_time=None,
                        all_day=False,
                        status=item.status,
                        priority=None,
                        color="blue",
                        meeting_link=item.meeting_link,
                        related_type="INTERVIEW",
                        related_id=item.id,
                        company_name=comp_name,
                        job_title=job_title,
                    )
                )

        # 2. Tasks
        if types_set is None or "TASK" in types_set:
            task_query = (
                select(Task)
                .where(Task.user_id == user_id, Task.due_date.isnot(None))
                .options(
                    selectinload(Task.application),
                    selectinload(Task.company),
                )
            )
            if start_date:
                task_query = task_query.where(Task.due_date >= start_date)
            if end_date:
                task_query = task_query.where(Task.due_date <= end_date)

            task_results = (await db.execute(task_query)).scalars().all()
            for t in task_results:
                comp_name = None
                job_title = None
                if t.application:
                    comp_name = t.application.company_name
                    job_title = t.application.job_title
                elif t.company:
                    comp_name = t.company.name

                events.append(
                    CalendarEventResponse(
                        id=f"task-{t.id}",
                        entity_id=t.id,
                        event_type=CalendarEventType.TASK,
                        title=f"Task: {t.title}",
                        description=t.description,
                        date=t.due_date,
                        start_time=None,
                        end_time=None,
                        all_day=True,
                        status=t.status,
                        priority=t.priority,
                        color="amber",
                        meeting_link=None,
                        related_type=t.related_type,
                        related_id=t.application_id or t.interview_id or t.company_id or t.contact_id,
                        company_name=comp_name,
                        job_title=job_title,
                    )
                )

        # 3. Application Follow-ups
        if types_set is None or "FOLLOW_UP" in types_set:
            followup_query = (
                select(ApplicationFollowup)
                .where(ApplicationFollowup.user_id == user_id, ApplicationFollowup.due_date.isnot(None))
                .options(selectinload(ApplicationFollowup.application))
            )
            if start_date:
                followup_query = followup_query.where(ApplicationFollowup.due_date >= start_date)
            if end_date:
                followup_query = followup_query.where(ApplicationFollowup.due_date <= end_date)

            followup_results = (await db.execute(followup_query)).scalars().all()
            for f in followup_results:
                comp_name = f.application.company_name if f.application else None
                job_title = f.application.job_title if f.application else None
                status_str = "COMPLETED" if f.is_completed else "PENDING"
                title = f"Follow-up: {job_title} @ {comp_name}" if (job_title and comp_name) else "Application Follow-up"

                events.append(
                    CalendarEventResponse(
                        id=f"followup-{f.id}",
                        entity_id=f.id,
                        event_type=CalendarEventType.FOLLOW_UP,
                        title=title,
                        description=f.note,
                        date=f.due_date,
                        start_time=None,
                        end_time=None,
                        all_day=True,
                        status=status_str,
                        priority="MEDIUM",
                        color="emerald",
                        meeting_link=None,
                        related_type="APPLICATION",
                        related_id=f.application_id,
                        company_name=comp_name,
                        job_title=job_title,
                    )
                )

        # 4. Application Deadlines (verified: applications.deadline_date exists)
        if types_set is None or "DEADLINE" in types_set:
            app_query = (
                select(Application)
                .where(Application.user_id == user_id, Application.deadline_date.isnot(None))
            )
            if start_date:
                app_query = app_query.where(Application.deadline_date >= start_date)
            if end_date:
                app_query = app_query.where(Application.deadline_date <= end_date)

            app_results = (await db.execute(app_query)).scalars().all()
            for a in app_results:
                events.append(
                    CalendarEventResponse(
                        id=f"deadline-{a.id}",
                        entity_id=a.id,
                        event_type=CalendarEventType.DEADLINE,
                        title=f"Deadline: {a.job_title} @ {a.company_name}",
                        description=f"Application cutoff deadline. Current stage: {a.current_stage}",
                        date=a.deadline_date,
                        start_time=None,
                        end_time=None,
                        all_day=True,
                        status=a.status,
                        priority=a.priority,
                        color="purple",
                        meeting_link=None,
                        related_type="APPLICATION",
                        related_id=a.id,
                        company_name=a.company_name,
                        job_title=a.job_title,
                    )
                )

        # Chronological sort: by date ascending, then start_time
        def _get_sort_key(ev):
            t = ev.start_time.time() if ev.start_time is not None else time.min
            return (ev.date, t)

        events.sort(key=_get_sort_key)

        return CalendarScheduleResponse(
            events=events,
            total_events=len(events),
            start_date=start_date,
            end_date=end_date,
        )


calendar_service = CalendarService()
