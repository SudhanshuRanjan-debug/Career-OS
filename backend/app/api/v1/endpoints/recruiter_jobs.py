"""
Recruiter Job Postings and Applicant Management API endpoints.
Provides complete posting lifecycle (Draft, Publish, Close, Archive) and
scoped applicant review (list, detail, stage progression, resume download) for HIRER users.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_storage, require_hirer
from app.core.file_download import create_secure_file_download_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import (
    RecruiterApplicantDetailResponse,
    RecruiterApplicantListItem,
    StageTransitionRequest,
)
from app.schemas.common import PaginatedResponse
from app.schemas.job_posting import (
    JobPostingCreate,
    JobPostingResponse,
    JobPostingUpdate,
)
from app.services.job_posting_service import job_posting_service
from app.storage.base import StorageBackend

router = APIRouter()


# ===========================================================================
# Job Postings Management
# ===========================================================================

@router.get("", response_model=PaginatedResponse[JobPostingResponse])
async def list_recruiter_jobs(
    status: Optional[str] = Query(None, description="Filter by status: DRAFT, PUBLISHED, CLOSED, ARCHIVED"),
    search: Optional[str] = Query(None, description="Search by title, description, location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """List job postings for the authenticated recruiter's organization."""
    return await job_posting_service.list_recruiter_jobs(
        db=db,
        recruiter_user_id=current_user.id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    data: JobPostingCreate,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job posting in DRAFT status."""
    return await job_posting_service.create_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        data=data,
    )


# Note: Specific routes before /{job_id} to avoid path collision
@router.get("/applications/{application_id}", response_model=RecruiterApplicantDetailResponse)
async def get_applicant_detail(
    application_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full applicant review detail under strict recruiter isolation."""
    return await job_posting_service.get_applicant_detail(
        db=db,
        recruiter_user_id=current_user.id,
        application_id=application_id,
    )


@router.post("/applications/{application_id}/stage", response_model=RecruiterApplicantDetailResponse)
async def update_applicant_stage(
    application_id: UUID,
    data: StageTransitionRequest,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Advance or update applicant recruitment stage."""
    return await job_posting_service.update_applicant_stage(
        db=db,
        recruiter_user_id=current_user.id,
        application_id=application_id,
        data=data,
    )


@router.get("/applications/{application_id}/resume")
async def download_applicant_resume(
    application_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    """Download or preview the submitted candidate resume."""
    storage_key, filename, mime_type = await job_posting_service.get_applicant_resume_file(
        db=db,
        recruiter_user_id=current_user.id,
        application_id=application_id,
    )

    file_stream = await storage.get_stream(storage_key)

    return create_secure_file_download_response(
        file_stream=file_stream,
        filename=filename,
        media_type=mime_type,
    )


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_recruiter_job(
    job_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single job posting with applicant count and skills."""
    return await job_posting_service.get_recruiter_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
    )


@router.patch("/{job_id}", response_model=JobPostingResponse)
async def update_job_posting(
    job_id: UUID,
    data: JobPostingUpdate,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Update job posting attributes and required skills."""
    return await job_posting_service.update_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
        data=data,
    )


@router.post("/{job_id}/publish", response_model=JobPostingResponse)
async def publish_job_posting(
    job_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Publish a draft job posting, making it publicly visible to candidates."""
    return await job_posting_service.publish_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
    )


@router.post("/{job_id}/close", response_model=JobPostingResponse)
async def close_job_posting(
    job_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Close a job posting (no longer accepting new applications)."""
    return await job_posting_service.close_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
    )


@router.post("/{job_id}/archive", response_model=JobPostingResponse)
async def archive_job_posting(
    job_id: UUID,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Archive a job posting for historical recordkeeping."""
    return await job_posting_service.archive_job_posting(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
    )


@router.get("/{job_id}/applicants", response_model=PaginatedResponse[RecruiterApplicantListItem])
async def list_job_applicants(
    job_id: UUID,
    stage: Optional[str] = Query(None, description="Filter applicants by stage"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """List applicants for this job posting with scoped candidate summaries."""
    return await job_posting_service.list_job_applicants(
        db=db,
        recruiter_user_id=current_user.id,
        job_id=job_id,
        stage=stage,
        page=page,
        page_size=page_size,
    )
