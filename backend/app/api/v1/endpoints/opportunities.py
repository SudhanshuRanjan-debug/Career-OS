"""
Opportunities & Job Board Discovery API Router.
Stage 4 Master Implementation.
All endpoints enforce strict authentication and ownership isolation.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.application import ApplicationConvertRequest, ApplicationResponse
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunityUpdate,
    SavedOpportunityCreate,
    SavedOpportunityListResponse,
    SavedOpportunityResponse,
)
from app.services.application_service import application_service
from app.services.opportunity_service import opportunity_service

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    search: Optional[str] = Query(None, description="Search term in title, company, location, or description"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, SAVED, CONSIDERING, ARCHIVED, NOT_INTERESTED)"),
    location_type: Optional[str] = Query(None, description="Filter by location type (REMOTE, HYBRID, ON_SITE)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP)"),
    is_saved: Optional[bool] = Query(None, description="Filter by bookmark state"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List and search user-owned opportunities with filtering, sorting, and pagination.
    """
    return await opportunity_service.list_opportunities(
        db=db,
        user_id=current_user.id,
        search=search,
        status=status,
        location_type=location_type,
        employment_type=employment_type,
        is_saved=is_saved,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new opportunity manually or via clean URL import.
    """
    return await opportunity_service.create_opportunity(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get("/saved", response_model=SavedOpportunityListResponse)
async def list_saved_opportunities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all bookmarked opportunities for the current authenticated user.
    """
    return await opportunity_service.list_saved_opportunities(
        db=db,
        user_id=current_user.id,
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete details for a single opportunity.
    Returns 404 if not found or belongs to another user.
    """
    return await opportunity_service.get_opportunity(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
    )


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: UUID,
    data: OpportunityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update opportunity fields, status, or tracking notes.
    Returns 404 if not found or belongs to another user.
    """
    return await opportunity_service.update_opportunity(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
        data=data,
    )


@router.delete("/{opportunity_id}", response_model=MessageResponse)
async def delete_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an opportunity and any associated saved bookmarks.
    Returns 404 if not found or belongs to another user.
    """
    await opportunity_service.delete_opportunity(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
    )
    return MessageResponse(message="Opportunity deleted successfully")


@router.post("/{opportunity_id}/save", response_model=SavedOpportunityResponse)
async def save_opportunity(
    opportunity_id: UUID,
    data: Optional[SavedOpportunityCreate] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bookmark an opportunity to the saved queue. Idempotent.
    """
    notes = data.notes if data else None
    return await opportunity_service.save_opportunity(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
        notes=notes,
    )


@router.delete("/{opportunity_id}/save", response_model=MessageResponse)
async def unsave_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove an opportunity from the saved queue. Idempotent.
    """
    await opportunity_service.unsave_opportunity(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
    )
    return MessageResponse(message="Opportunity unsaved successfully")


@router.post("/{opportunity_id}/convert", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def convert_opportunity_to_application(
    opportunity_id: UUID,
    data: Optional[ApplicationConvertRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Convert an existing opportunity into an active application snapshot.
    Does not modify Opportunity status enum.
    """
    req = data or ApplicationConvertRequest()
    return await application_service.convert_opportunity_to_application(
        db=db,
        user_id=current_user.id,
        opportunity_id=opportunity_id,
        data=req,
    )
