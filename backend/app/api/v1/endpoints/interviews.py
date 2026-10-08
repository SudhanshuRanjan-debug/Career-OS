"""
Interviews & Interview Preparation API Router.
Stage 7: Interviews & Interview Preparation.
Provides interview tracking, outcome recording, and preparation workspaces.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewListResponse,
    InterviewPreparationResponse,
    InterviewPreparationUpdate,
    InterviewResponse,
    InterviewUpdate,
)
from app.services.interview_service import InterviewService

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get(
    "",
    response_model=InterviewListResponse,
    summary="List candidate interviews",
    description="Retrieve paginated interviews filtered by status, application, company, or type.",
)
async def list_interviews(
    search: Optional[str] = Query(None, description="Search by title, stage, location, or notes"),
    application_id: Optional[UUID] = Query(None, description="Filter by application ID"),
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED, UPCOMING)"),
    interview_type: Optional[str] = Query(None, description="Filter by type (TECHNICAL, PHONE, HR, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("scheduled_at", description="Sort by: scheduled_at, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewListResponse:
    items, total = await InterviewService.list_interviews(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        application_id=application_id,
        company_id=company_id,
        status_filter=status,
        interview_type=interview_type,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return InterviewListResponse(
        items=[InterviewResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule new interview",
    description="Schedule an interview associated with an application, company, or contact.",
)
async def create_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    interview = await InterviewService.create_interview(
        db=db, user_id=current_user.id, data=data
    )
    return InterviewResponse.model_validate(interview)


@router.get(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Get interview details",
    description="Fetch single interview session with relationships and preparation workspace.",
)
async def get_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    interview = await InterviewService.get_interview(
        db=db, user_id=current_user.id, interview_id=interview_id
    )
    return InterviewResponse.model_validate(interview)


@router.put(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Update interview",
    description="Modify interview details, outcome result, or status.",
)
async def update_interview(
    interview_id: UUID,
    data: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    interview = await InterviewService.update_interview(
        db=db, user_id=current_user.id, interview_id=interview_id, data=data
    )
    return InterviewResponse.model_validate(interview)


@router.delete(
    "/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete interview",
    description="Permanently remove interview and its preparation workspace.",
)
async def delete_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await InterviewService.delete_interview(
        db=db, user_id=current_user.id, interview_id=interview_id
    )


# ===========================================================================
# Interview Preparation Workspace Endpoints
# ===========================================================================

@router.get(
    "/{interview_id}/preparation",
    response_model=InterviewPreparationResponse,
    summary="Get interview preparation workspace",
    description="Retrieve research, questions to ask, personal talking points, and checklist for an interview.",
)
async def get_preparation(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewPreparationResponse:
    prep = await InterviewService.get_preparation(
        db=db, user_id=current_user.id, interview_id=interview_id
    )
    return InterviewPreparationResponse.model_validate(prep)


@router.put(
    "/{interview_id}/preparation",
    response_model=InterviewPreparationResponse,
    summary="Update interview preparation workspace",
    description="Save company research, role research, questions to ask, checklist items, and post-interview debrief.",
)
async def update_preparation(
    interview_id: UUID,
    data: InterviewPreparationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewPreparationResponse:
    prep = await InterviewService.update_preparation(
        db=db, user_id=current_user.id, interview_id=interview_id, data=data
    )
    return InterviewPreparationResponse.model_validate(prep)
