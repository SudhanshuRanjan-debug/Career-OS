"""
Applications, Pipeline, Stage History & Activity Timeline API Router.
Stage 5 Master Implementation.
All endpoints enforce strict authentication and user ownership isolation.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import (
    ApplicationActivityResponse,
    ApplicationCreate,
    ApplicationDocumentAttach,
    ApplicationDocumentResponse,
    ApplicationFollowupCreate,
    ApplicationFollowupResponse,
    ApplicationFollowupUpdate,
    ApplicationFollowupWithAppResponse,
    ApplicationHealthResponse,
    ApplicationListResponse,
    ApplicationNoteCreate,
    ApplicationNoteResponse,
    ApplicationNoteUpdate,
    ApplicationResponse,
    ApplicationUpdate,
    PipelineResponse,
    StageHistoryResponse,
    StageTransitionRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.qa_vault import (
    ApplicationAnswerCreate,
    ApplicationAnswerResponse,
    ApplicationAnswerUpdate,
)
from app.schemas.interview import InterviewResponse
from app.schemas.task import TaskResponse
from app.services.application_service import application_service
from app.services.interview_service import InterviewService
from app.services.task_service import task_service

router = APIRouter(dependencies=[Depends(require_candidate)])


# ---------------------------------------------------------------------------
# Applications Collection & Aggregations
# ---------------------------------------------------------------------------

@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    search: Optional[str] = Query(None, description="Search term in job title, company, or location"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, CLOSED, ARCHIVED)"),
    stage: Optional[str] = Query(None, description="Filter by stage (APPLIED, PHONE_SCREEN, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user-owned applications with filtering, search, sorting, and pagination.
    """
    return await application_service.list_applications(
        db=db,
        user_id=current_user.id,
        search=search,
        status=status,
        stage=stage,
        priority=priority,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new application with company, stage, resume version, and optional initial notes.
    """
    return await application_service.create_application(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get("/pipeline", response_model=PipelineResponse)
async def get_pipeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Group active applications by recruitment stage for the Kanban pipeline board.
    """
    return await application_service.get_pipeline(
        db=db,
        user_id=current_user.id,
    )


@router.get("/followups", response_model=List[ApplicationFollowupWithAppResponse])
async def list_all_followups(
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all follow-up reminders across all user applications for the dedicated follow-ups view.
    """
    return await application_service.list_all_user_followups(
        db=db,
        user_id=current_user.id,
        is_completed=is_completed,
    )


# ---------------------------------------------------------------------------
# Individual Application Resource
# ---------------------------------------------------------------------------

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full application details, linked resume snapshot, counts, and health score.
    Returns 404 if not found or belongs to another user.
    """
    return await application_service.get_application(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update application fields, priority, outcome, or recruiter contact.
    """
    return await application_service.update_application(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.delete("/{application_id}", response_model=MessageResponse)
async def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an application and its child entities (history, notes, followups, documents, answers).
    """
    await application_service.delete_application(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )
    return MessageResponse(message="Application deleted successfully")


# ---------------------------------------------------------------------------
# Stage Transitions, History & Activity Timeline
# ---------------------------------------------------------------------------

@router.post("/{application_id}/stage", response_model=ApplicationResponse)
async def transition_stage(
    application_id: UUID,
    data: StageTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Transition application stage.
    Appends an immutable stage history record and logs activity.
    """
    return await application_service.transition_stage(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.get("/{application_id}/stage-history", response_model=List[StageHistoryResponse])
async def list_stage_history(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    View chronological stage transition history.
    """
    return await application_service.list_stage_history(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.get("/{application_id}/activity", response_model=List[ApplicationActivityResponse])
async def list_activity(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    View immutable application activity timeline.
    """
    return await application_service.list_activity(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.get("/{application_id}/health", response_model=ApplicationHealthResponse)
async def get_application_health(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate deterministic application health score, status, and explainable checks.
    """
    return await application_service.get_application_health(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


# ---------------------------------------------------------------------------
# Application Notes
# ---------------------------------------------------------------------------

@router.get("/{application_id}/notes", response_model=List[ApplicationNoteResponse])
async def list_notes(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List personal tracking notes for this application.
    """
    return await application_service.list_notes(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.post("/{application_id}/notes", response_model=ApplicationNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    application_id: UUID,
    data: ApplicationNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a tracking note to the application.
    """
    return await application_service.create_note(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.put("/{application_id}/notes/{note_id}", response_model=ApplicationNoteResponse)
async def update_note(
    application_id: UUID,
    note_id: UUID,
    data: ApplicationNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing application note.
    """
    return await application_service.update_note(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        note_id=note_id,
        data=data,
    )


@router.delete("/{application_id}/notes/{note_id}", response_model=MessageResponse)
async def delete_note(
    application_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an application note.
    """
    await application_service.delete_note(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        note_id=note_id,
    )
    return MessageResponse(message="Note deleted successfully")


# ---------------------------------------------------------------------------
# Application Follow-ups
# ---------------------------------------------------------------------------

@router.get("/{application_id}/followups", response_model=List[ApplicationFollowupResponse])
async def list_application_followups(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List follow-up reminders scheduled for this specific application.
    """
    return await application_service.list_followups(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.post("/{application_id}/followups", response_model=ApplicationFollowupResponse, status_code=status.HTTP_201_CREATED)
async def create_followup(
    application_id: UUID,
    data: ApplicationFollowupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule a follow-up reminder for this application.
    """
    return await application_service.create_followup(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.put("/{application_id}/followups/{followup_id}", response_model=ApplicationFollowupResponse)
async def update_followup(
    application_id: UUID,
    followup_id: UUID,
    data: ApplicationFollowupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update follow-up details or toggle completion status.
    """
    return await application_service.update_followup(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        followup_id=followup_id,
        data=data,
    )


@router.delete("/{application_id}/followups/{followup_id}", response_model=MessageResponse)
async def delete_followup(
    application_id: UUID,
    followup_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a follow-up reminder.
    """
    await application_service.delete_followup(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        followup_id=followup_id,
    )
    return MessageResponse(message="Follow-up deleted successfully")


# ---------------------------------------------------------------------------
# Application Documents
# ---------------------------------------------------------------------------

@router.get("/{application_id}/documents", response_model=List[ApplicationDocumentResponse])
async def list_application_documents(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List supporting documents attached to this application.
    """
    return await application_service.list_documents(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.post("/{application_id}/documents", response_model=ApplicationDocumentResponse, status_code=status.HTTP_201_CREATED)
async def attach_document(
    application_id: UUID,
    data: ApplicationDocumentAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Attach a document from the candidate's document vault to this application.
    """
    return await application_service.attach_document(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        document_id=data.document_id,
    )


@router.delete("/{application_id}/documents/{document_id}", response_model=MessageResponse)
async def detach_document(
    application_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Detach a supporting document from this application (does not delete original document).
    """
    await application_service.detach_document(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        document_id=document_id,
    )
    return MessageResponse(message="Document detached successfully")


# ---------------------------------------------------------------------------
# Application Q&A Answers
# ---------------------------------------------------------------------------

@router.get("/{application_id}/answers", response_model=List[ApplicationAnswerResponse])
async def list_application_answers(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List application-specific Q&A responses.
    """
    return await application_service.list_answers(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )


@router.post("/{application_id}/answers", response_model=ApplicationAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_application_answer(
    application_id: UUID,
    data: ApplicationAnswerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an application-specific response, optionally linked to a Q&A Vault template.
    """
    return await application_service.create_answer(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.put("/{application_id}/answers/{answer_id}", response_model=ApplicationAnswerResponse)
async def update_application_answer(
    application_id: UUID,
    answer_id: UUID,
    data: ApplicationAnswerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an application-specific response.
    """
    return await application_service.update_answer(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        answer_id=answer_id,
        data=data,
    )


@router.delete("/{application_id}/answers/{answer_id}", response_model=MessageResponse)
async def delete_application_answer(
    application_id: UUID,
    answer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an application-specific response.
    """
    await application_service.delete_answer(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
        answer_id=answer_id,
    )
    return MessageResponse(message="Answer deleted successfully")


# ---------------------------------------------------------------------------
# Application Associated Interviews (Stage 7)
# ---------------------------------------------------------------------------

@router.get(
    "/{application_id}/interviews",
    response_model=List[InterviewResponse],
    summary="List interviews for application",
    description="Retrieve all scheduled, completed, or cancelled interviews for this application.",
)
async def list_application_interviews(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[InterviewResponse]:
    interviews = await InterviewService.list_application_interviews(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )
    return [InterviewResponse.model_validate(i) for i in interviews]


# ---------------------------------------------------------------------------
# Application Associated Tasks (Stage 8)
# ---------------------------------------------------------------------------

@router.get(
    "/{application_id}/tasks",
    response_model=List[TaskResponse],
    summary="List tasks for application",
    description="Retrieve all tasks linked to this application.",
)
async def list_application_tasks(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TaskResponse]:
    # Ensure application exists and belongs to current user
    await application_service.get_application(db=db, user_id=current_user.id, application_id=application_id)
    res = await task_service.list_tasks(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )
    return res.items
