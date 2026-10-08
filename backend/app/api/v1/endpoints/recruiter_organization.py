"""
Recruiter Organization API endpoints.
Provides retrieval and updating of employer profile for authenticated HIRER users.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_hirer
from app.db.session import get_db
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.services.organization_service import organization_service

router = APIRouter()


@router.get("", response_model=OrganizationResponse)
async def get_recruiter_organization(
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated recruiter's organization profile."""
    return await organization_service.get_by_owner_id(db, current_user.id)


@router.patch("", response_model=OrganizationResponse)
async def update_recruiter_organization(
    data: OrganizationUpdate,
    current_user: User = Depends(require_hirer),
    db: AsyncSession = Depends(get_db),
):
    """Update organization profile details for the authenticated recruiter."""
    return await organization_service.update_organization(db, current_user.id, data)
