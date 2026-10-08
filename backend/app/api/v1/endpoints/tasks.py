"""
Tasks API endpoints — polymorphic action items, follow-ups, and career milestone tracking.
Stage 8: Tasks, Calendar & Notifications.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationParams
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import task_service

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    filter_mode: Optional[str] = Query(None, alias="filter", description="Filter mode: all, today, upcoming, completed"),
    status: Optional[str] = Query(None, description="PENDING, IN_PROGRESS, COMPLETED, CANCELLED"),
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, URGENT"),
    related_type: Optional[str] = Query(None, description="APPLICATION, INTERVIEW, COMPANY, CONTACT, GENERAL"),
    application_id: Optional[UUID] = Query(None, description="Filter by linked application"),
    interview_id: Optional[UUID] = Query(None, description="Filter by linked interview"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tasks owned by current user with optional filters, search, and pagination."""
    pagination = PaginationParams(page=page, page_size=page_size)
    return await task_service.list_tasks(
        db=db,
        user_id=current_user.id,
        filter_mode=filter_mode,
        status_filter=status,
        priority_filter=priority,
        related_type=related_type,
        application_id=application_id,
        interview_id=interview_id,
        search=search,
        pagination=pagination,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a task with strict polymorphic linkage validation."""
    return await task_service.create_task(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve task details by ID with tenant isolation."""
    return await task_service.get_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task fields and handle status/completion transitions."""
    return await task_service.update_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
        data=data,
    )


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deterministic task completion action."""
    return await task_service.complete_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
    )


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete task with tenant isolation check."""
    await task_service.delete_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
    )
    return MessageResponse(message="Task deleted successfully")
