"""
Interview and Interview Preparation domain service.
Stage 7: Interviews & Interview Preparation.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.application import Application, ApplicationActivity
from app.models.company import Company
from app.models.contact import Contact
from app.models.interview import Interview, InterviewPreparation
from app.schemas.interview import (
    InterviewCreate,
    InterviewPreparationUpdate,
    InterviewUpdate,
)


class InterviewService:
    @staticmethod
    async def _validate_user_application(
        db: AsyncSession, user_id: UUID, application_id: Optional[UUID]
    ) -> Optional[Application]:
        """Verify that application belongs to current user."""
        if not application_id:
            return None
        stmt = select(Application).where(
            Application.id == application_id, Application.user_id == user_id
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return app

    @staticmethod
    async def _validate_user_company(
        db: AsyncSession, user_id: UUID, company_id: Optional[UUID]
    ) -> Optional[Company]:
        """Verify that company belongs to current user."""
        if not company_id:
            return None
        stmt = select(Company).where(
            Company.id == company_id, Company.user_id == user_id
        )
        res = await db.execute(stmt)
        company = res.scalar_one_or_none()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        return company

    @staticmethod
    async def _validate_user_contact(
        db: AsyncSession, user_id: UUID, contact_id: Optional[UUID]
    ) -> Optional[Contact]:
        """Verify that contact belongs to current user."""
        if not contact_id:
            return None
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user_id
        )
        res = await db.execute(stmt)
        contact = res.scalar_one_or_none()
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        return contact

    @classmethod
    async def create_interview(
        cls, db: AsyncSession, user_id: UUID, data: InterviewCreate
    ) -> Interview:
        """Create new interview with ownership validation and initialized preparation record."""
        app = await cls._validate_user_application(db, user_id, data.application_id)
        comp = await cls._validate_user_company(db, user_id, data.company_id)
        await cls._validate_user_contact(db, user_id, data.contact_id)

        # Inherit company_id from application if not explicitly provided
        final_company_id = data.company_id
        if final_company_id is None and app and app.company_id:
            final_company_id = app.company_id

        # Determine title if not provided
        title = data.title
        if not title:
            round_label = data.stage or (data.interview_type.capitalize() if data.interview_type else "Technical")
            title = f"{round_label} Interview"

        interview = Interview(
            user_id=user_id,
            application_id=data.application_id,
            company_id=final_company_id,
            contact_id=data.contact_id,
            title=title,
            interview_type=data.interview_type,
            stage=data.stage,
            scheduled_at=data.scheduled_at,
            duration_mins=data.duration_mins,
            meeting_link=data.meeting_link,
            location=data.location,
            status=data.status or "SCHEDULED",
            result=data.result,
            interviewer_names=data.interviewer_names,
            notes=data.notes,
        )
        db.add(interview)
        await db.flush()

        # Initialize 1:1 interview preparation workspace
        prep = InterviewPreparation(interview_id=interview.id)
        db.add(prep)

        # Append to ApplicationActivity if application is attached
        if app:
            scheduled_str = (
                f" for {interview.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}"
                if interview.scheduled_at
                else ""
            )
            activity = ApplicationActivity(
                application_id=app.id,
                user_id=user_id,
                event_type="INTERVIEW_SCHEDULED",
                description=f"Scheduled {interview.interview_type or 'session'} ({interview.title}){scheduled_str}",
                event_data={
                    "interview_id": str(interview.id),
                    "interview_type": interview.interview_type,
                    "scheduled_at": interview.scheduled_at.isoformat() if interview.scheduled_at else None,
                },
            )
            db.add(activity)

        await db.commit()

        return await cls.get_interview(db, user_id, interview.id)

    @classmethod
    async def get_interview(
        cls, db: AsyncSession, user_id: UUID, interview_id: UUID
    ) -> Interview:
        """Fetch interview by ID with tenant isolation and eager-loaded relations."""
        stmt = (
            select(Interview)
            .where(Interview.id == interview_id, Interview.user_id == user_id)
            .options(
                selectinload(Interview.application),
                selectinload(Interview.company),
                selectinload(Interview.contact),
                selectinload(Interview.preparation),
            )
        )
        res = await db.execute(stmt)
        interview = res.scalar_one_or_none()
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )
        return interview

    @classmethod
    async def list_interviews(
        cls,
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        application_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        interview_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "scheduled_at",
        sort_order: str = "asc",
    ) -> Tuple[List[Interview], int]:
        """List and filter candidate interviews with server-side pagination."""
        filters = [Interview.user_id == user_id]

        if application_id:
            filters.append(Interview.application_id == application_id)
        if company_id:
            filters.append(Interview.company_id == company_id)
        if interview_type:
            filters.append(Interview.interview_type == interview_type.upper().strip())

        if status_filter:
            st = status_filter.upper().strip()
            if st == "UPCOMING":
                # Scheduled or rescheduled sessions
                filters.append(Interview.status.in_(["SCHEDULED", "RESCHEDULED"]))
            elif st == "COMPLETED":
                filters.append(Interview.status == "COMPLETED")
            elif st == "CANCELLED":
                filters.append(Interview.status == "CANCELLED")
            else:
                filters.append(Interview.status == st)

        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Interview.title.ilike(term),
                    Interview.stage.ilike(term),
                    Interview.location.ilike(term),
                    Interview.notes.ilike(term),
                )
            )

        # Count total
        count_stmt = select(func.count(Interview.id)).where(*filters)
        total = (await db.execute(count_stmt)).scalar() or 0

        # Query items
        stmt = (
            select(Interview)
            .where(*filters)
            .options(
                selectinload(Interview.application),
                selectinload(Interview.company),
                selectinload(Interview.contact),
                selectinload(Interview.preparation),
            )
        )

        # Ordering
        if sort_by == "created_at":
            sort_col = Interview.created_at
        else:
            sort_col = Interview.scheduled_at

        if sort_order.lower() == "desc":
            stmt = stmt.order_by(sort_col.desc().nulls_last(), Interview.created_at.desc())
        else:
            stmt = stmt.order_by(sort_col.asc().nulls_last(), Interview.created_at.asc())

        # Pagination offset & limit
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        res = await db.execute(stmt)
        items = list(res.scalars().all())

        return items, total

    @classmethod
    async def update_interview(
        cls, db: AsyncSession, user_id: UUID, interview_id: UUID, data: InterviewUpdate
    ) -> Interview:
        """Update interview details with tenant validation."""
        interview = await cls.get_interview(db, user_id, interview_id)

        update_dict = data.model_dump(exclude_unset=True)

        # Validate relationships if being modified
        if "application_id" in update_dict:
            await cls._validate_user_application(db, user_id, update_dict["application_id"])
        if "company_id" in update_dict:
            await cls._validate_user_company(db, user_id, update_dict["company_id"])
        if "contact_id" in update_dict:
            await cls._validate_user_contact(db, user_id, update_dict["contact_id"])

        old_status = interview.status
        for field, value in update_dict.items():
            if hasattr(interview, field):
                setattr(interview, field, value)
            elif field == "feedback" and interview.preparation and value:
                interview.preparation.post_interview_notes = value

        interview.updated_at = datetime.now(timezone.utc)

        # If status changed, log to application activity if application attached
        if "status" in update_dict and update_dict["status"] != old_status and interview.application_id:
            activity = ApplicationActivity(
                application_id=interview.application_id,
                user_id=user_id,
                event_type="INTERVIEW_STATUS_CHANGED",
                description=f"Interview '{interview.title}' status updated to {interview.status}",
                event_data={
                    "interview_id": str(interview.id),
                    "old_status": old_status,
                    "new_status": interview.status,
                },
            )
            db.add(activity)

        await db.commit()
        return await cls.get_interview(db, user_id, interview_id)

    @classmethod
    async def delete_interview(
        cls, db: AsyncSession, user_id: UUID, interview_id: UUID
    ) -> None:
        """Delete an interview and cascade delete its preparation record."""
        interview = await cls.get_interview(db, user_id, interview_id)
        app_id = interview.application_id
        title = interview.title

        await db.delete(interview)

        if app_id:
            activity = ApplicationActivity(
                application_id=app_id,
                user_id=user_id,
                event_type="INTERVIEW_DELETED",
                description=f"Removed interview: {title or 'Session'}",
                event_data={"interview_id": str(interview_id)},
            )
            db.add(activity)

        await db.commit()

    @classmethod
    async def get_preparation(
        cls, db: AsyncSession, user_id: UUID, interview_id: UUID
    ) -> InterviewPreparation:
        """Get interview preparation workspace, initializing one if not present."""
        # Ensure interview exists and is owned by current user
        await cls.get_interview(db, user_id, interview_id)

        stmt = select(InterviewPreparation).where(
            InterviewPreparation.interview_id == interview_id
        )
        res = await db.execute(stmt)
        prep = res.scalar_one_or_none()

        if not prep:
            prep = InterviewPreparation(interview_id=interview_id)
            db.add(prep)
            await db.commit()
            await db.refresh(prep)

        return prep

    @classmethod
    async def update_preparation(
        cls,
        db: AsyncSession,
        user_id: UUID,
        interview_id: UUID,
        data: InterviewPreparationUpdate,
    ) -> InterviewPreparation:
        """Save interview preparation notes, checklist, and research."""
        prep = await cls.get_preparation(db, user_id, interview_id)

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(prep, field, value)

        prep.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(prep)
        return prep

    @classmethod
    async def list_application_interviews(
        cls, db: AsyncSession, user_id: UUID, application_id: UUID
    ) -> List[Interview]:
        """Retrieve all interviews associated with a given application."""
        await cls._validate_user_application(db, user_id, application_id)
        stmt = (
            select(Interview)
            .where(
                Interview.application_id == application_id,
                Interview.user_id == user_id,
            )
            .options(
                selectinload(Interview.application),
                selectinload(Interview.company),
                selectinload(Interview.contact),
                selectinload(Interview.preparation),
            )
            .order_by(Interview.scheduled_at.asc().nulls_last(), Interview.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
