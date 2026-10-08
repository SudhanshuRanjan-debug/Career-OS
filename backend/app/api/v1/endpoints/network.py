"""
Professional Contacts & Networking Directory API Router.
Stage 6: Network / Contacts.
Provides complete contact management with search, filtering, and linked applications.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.contact import (
    ContactCreate,
    ContactDetailResponse,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.services.contact_service import contact_service

# Router that can be mounted under /contacts and /network/contacts
router = APIRouter()


@router.get(
    "",
    response_model=ContactListResponse,
    summary="List professional contacts",
)
async def list_contacts(
    search: Optional[str] = Query(None, description="Search by name, role, email, company"),
    contact_type: Optional[str] = Query(None, description="Filter: RECRUITER, HIRING_MANAGER, etc."),
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort by: first_name, last_name, role, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactListResponse:
    return await contact_service.list_contacts(
        db=db,
        user_id=current_user.id,
        search=search,
        contact_type=contact_type,
        company_id=company_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create professional contact",
)
async def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    return await contact_service.create_contact(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactDetailResponse,
    summary="Get contact details and linked applications",
)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactDetailResponse:
    return await contact_service.get_contact(
        db=db,
        user_id=current_user.id,
        contact_id=contact_id,
    )


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Update contact details",
)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    return await contact_service.update_contact(
        db=db,
        user_id=current_user.id,
        contact_id=contact_id,
        data=data,
    )


@router.delete(
    "/{contact_id}",
    summary="Delete contact",
)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await contact_service.delete_contact(
        db=db,
        user_id=current_user.id,
        contact_id=contact_id,
    )
    return {"message": "Contact deleted successfully"}
