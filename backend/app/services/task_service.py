"""
Task service — business logic, polymorphic validation, and persistence for tasks.
Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.company import Company
from app.models.contact import Contact
from app.models.interview import Interview
from app.models.task import Task
from app.schemas.common import PaginationParams
from app.schemas.company import CompanySummary
from app.schemas.contact import ApplicationSummary, ContactSummary
from app.schemas.interview import InterviewSummary
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskRelatedType,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


class TaskService:
    @staticmethod
    def _build_response(task: Task) -> TaskResponse:
        app_summary = None
        if task.application:
            app_summary = ApplicationSummary(
                id=task.application.id,
                job_title=task.application.job_title,
                company_name=task.application.company_name,
                current_stage=task.application.current_stage,
                status=task.application.status,
                applied_date=task.application.applied_date,
            )

        int_summary = None
        if task.interview:
            int_summary = InterviewSummary(
                id=task.interview.id,
                stage=task.interview.stage,
                interview_type=task.interview.interview_type,
                status=task.interview.status,
                scheduled_at=task.interview.scheduled_at,
            )

        comp_summary = None
        if task.company:
            comp_summary = CompanySummary(
                id=task.company.id,
                name=task.company.name,
                website=task.company.website,
                industry=task.company.industry,
            )

        cont_summary = None
        if task.contact:
            cont_summary = ContactSummary(
                id=task.contact.id,
                first_name=task.contact.first_name,
                last_name=task.contact.last_name,
                role=task.contact.role,
                contact_type=task.contact.contact_type,
                email=task.contact.email,
            )

        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status,
            is_completed=task.is_completed,
            completed_at=task.completed_at,
            related_type=task.related_type,
            application_id=task.application_id,
            interview_id=task.interview_id,
            company_id=task.company_id,
            contact_id=task.contact_id,
            application=app_summary,
            interview=int_summary,
            company=comp_summary,
            contact=cont_summary,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def _validate_user_application(self, db: AsyncSession, user_id: UUID, application_id: UUID) -> Application:
        stmt = select(Application).where(Application.id == application_id, Application.user_id == user_id)
        result = await db.execute(stmt)
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or unauthorized",
            )
        return app

    async def _validate_user_interview(self, db: AsyncSession, user_id: UUID, interview_id: UUID) -> Interview:
        stmt = select(Interview).where(Interview.id == interview_id, Interview.user_id == user_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found or unauthorized",
            )
        return item

    async def _validate_user_company(self, db: AsyncSession, user_id: UUID, company_id: UUID) -> Company:
        stmt = select(Company).where(Company.id == company_id, Company.user_id == user_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found or unauthorized",
            )
        return item

    async def _validate_user_contact(self, db: AsyncSession, user_id: UUID, contact_id: UUID) -> Contact:
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found or unauthorized",
            )
        return item

    async def create_task(self, db: AsyncSession, user_id: UUID, data: TaskCreate) -> TaskResponse:
        # Validate polymorphic parent linkages for tenant ownership
        if data.application_id:
            await self._validate_user_application(db, user_id, data.application_id)
        if data.interview_id:
            await self._validate_user_interview(db, user_id, data.interview_id)
        if data.company_id:
            await self._validate_user_company(db, user_id, data.company_id)
        if data.contact_id:
            await self._validate_user_contact(db, user_id, data.contact_id)

        is_completed = (data.status == TaskStatus.COMPLETED)
        completed_at = datetime.now(timezone.utc) if is_completed else None

        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            priority=data.priority.value if hasattr(data.priority, "value") else str(data.priority),
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            is_completed=is_completed,
            completed_at=completed_at,
            related_type=data.related_type.value if hasattr(data.related_type, "value") else str(data.related_type),
            application_id=data.application_id,
            interview_id=data.interview_id,
            company_id=data.company_id,
            contact_id=data.contact_id,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return await self.get_task(db, user_id, task.id)

    async def get_task(self, db: AsyncSession, user_id: UUID, task_id: UUID) -> TaskResponse:
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(
                selectinload(Task.application),
                selectinload(Task.interview),
                selectinload(Task.company),
                selectinload(Task.contact),
            )
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return self._build_response(task)

    async def list_tasks(
        self,
        db: AsyncSession,
        user_id: UUID,
        filter_mode: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        related_type: Optional[str] = None,
        application_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        search: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> TaskListResponse:
        base_query = select(Task).where(Task.user_id == user_id)

        # Tab filter modes: all, today, upcoming, completed
        today_date = date.today()
        if filter_mode == "today":
            base_query = base_query.where(Task.due_date == today_date, Task.is_completed.is_(False))
        elif filter_mode == "upcoming":
            base_query = base_query.where(Task.due_date > today_date, Task.is_completed.is_(False))
        elif filter_mode == "completed":
            base_query = base_query.where(Task.is_completed.is_(True))

        if status_filter:
            base_query = base_query.where(Task.status == status_filter.upper())
        if priority_filter:
            base_query = base_query.where(Task.priority == priority_filter.upper())
        if related_type:
            base_query = base_query.where(Task.related_type == related_type.upper())
        if application_id:
            base_query = base_query.where(Task.application_id == application_id)
        if interview_id:
            base_query = base_query.where(Task.interview_id == interview_id)
        if search and search.strip():
            kw = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Task.title.ilike(kw),
                    Task.description.ilike(kw),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 50
        offset = (page - 1) * page_size

        # Sorting: uncompleted first, then due_date ascending (nulls last), then priority, created_at
        stmt = (
            base_query.options(
                selectinload(Task.application),
                selectinload(Task.interview),
                selectinload(Task.company),
                selectinload(Task.contact),
            )
            .order_by(
                Task.is_completed.asc(),
                Task.due_date.asc().nulls_last(),
                Task.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        items = [self._build_response(t) for t in tasks]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        return TaskListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_task(
        self,
        db: AsyncSession,
        user_id: UUID,
        task_id: UUID,
        data: TaskUpdate,
    ) -> TaskResponse:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        # Validate polymorphic linkages if being updated
        if data.application_id is not None:
            await self._validate_user_application(db, user_id, data.application_id)
            task.application_id = data.application_id
        if data.interview_id is not None:
            await self._validate_user_interview(db, user_id, data.interview_id)
            task.interview_id = data.interview_id
        if data.company_id is not None:
            await self._validate_user_company(db, user_id, data.company_id)
            task.company_id = data.company_id
        if data.contact_id is not None:
            await self._validate_user_contact(db, user_id, data.contact_id)
            task.contact_id = data.contact_id

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.due_date is not None:
            task.due_date = data.due_date
        if data.priority is not None:
            task.priority = data.priority.value if hasattr(data.priority, "value") else str(data.priority)
        if data.related_type is not None:
            task.related_type = data.related_type.value if hasattr(data.related_type, "value") else str(data.related_type)

        # Handle completion transitions
        if data.status is not None:
            status_val = data.status.value if hasattr(data.status, "value") else str(data.status)
            task.status = status_val
            if status_val == TaskStatus.COMPLETED.value:
                task.is_completed = True
                task.completed_at = datetime.now(timezone.utc)
            elif status_val in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value):
                task.is_completed = False
                task.completed_at = None

        if data.is_completed is not None:
            task.is_completed = data.is_completed
            if data.is_completed:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.now(timezone.utc)
            else:
                if task.status == TaskStatus.COMPLETED.value:
                    task.status = TaskStatus.PENDING.value
                task.completed_at = None

        task.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return await self.get_task(db, user_id, task_id)

    async def complete_task(
        self,
        db: AsyncSession,
        user_id: UUID,
        task_id: UUID,
    ) -> TaskResponse:
        """Deterministic completion action per Stage 8 specification."""
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        task.is_completed = True
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)

        await db.commit()
        return await self.get_task(db, user_id, task_id)

    async def delete_task(
        self,
        db: AsyncSession,
        user_id: UUID,
        task_id: UUID,
    ) -> None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        await db.delete(task)
        await db.commit()


task_service = TaskService()
