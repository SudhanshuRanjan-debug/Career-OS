"""
Jobs Discovery API endpoints for candidates & public search.
Allows browsing published job listings, saving them to personal opportunities,
and submitting applications.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_optional_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import ApplicationResponse, JobApplyRequest
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.job_posting import JobPostingDetailResponse, JobPostingResponse
from app.schemas.opportunity import OpportunityResponse
from app.services.application_service import application_service
from app.services.job_posting_service import job_posting_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[JobPostingResponse])
async def list_published_jobs(
    search: Optional[str] = Query(None, description="Search keyword in title, description, or company"),
    location: Optional[str] = Query(None, description="Filter by location"),
    location_type: Optional[str] = Query(None, description="Filter by REMOTE, HYBRID, ON_SITE"),
    employment_type: Optional[str] = Query(None, description="Filter by FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP"),
    experience_level: Optional[str] = Query(None, description="Filter by ENTRY, MID, SENIOR, LEAD, EXECUTIVE"),
    skill: Optional[str] = Query(None, description="Filter by required skill name"),
    min_compensation: Optional[Decimal] = Query(None, description="Minimum compensation filter"),
    currency: Optional[str] = Query(None, description="Compensation currency filter (e.g. INR, USD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Browse published job listings across all verified employers."""
    return await job_posting_service.list_published_jobs(
        db=db,
        search=search,
        location=location,
        location_type=location_type,
        employment_type=employment_type,
        experience_level=experience_level,
        skill=skill,
        min_compensation=min_compensation,
        currency=currency,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobPostingDetailResponse)
async def get_published_job(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details of a published job posting including employer overview."""
    candidate_id = current_user.id if current_user and current_user.role == "CANDIDATE" else None
    return await job_posting_service.get_published_job_detail(
        db=db,
        job_id=job_id,
        candidate_user_id=candidate_id,
    )


@router.post("/{job_id}/save", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def save_job_as_opportunity(
    job_id: UUID,
    current_user: User = Depends(require_candidate),
    db: AsyncSession = Depends(get_db),
):
    """Save a platform job posting directly into the candidate's personal opportunity pipeline."""
    opp = await job_posting_service.save_job_to_opportunities(
        db=db,
        candidate_user_id=current_user.id,
        job_id=job_id,
    )
    return OpportunityResponse.model_validate(opp)


@router.post("/{job_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: UUID,
    data: JobApplyRequest,
    current_user: User = Depends(require_candidate),
    db: AsyncSession = Depends(get_db),
):
    """Submit a verified application linking candidate locked resume to this published job."""
    app = await job_posting_service.apply_to_job(
        db=db,
        candidate_user_id=current_user.id,
        job_id=job_id,
        data=data,
    )
    return await application_service.get_application(
        db=db,
        user_id=current_user.id,
        application_id=app.id,
    )
