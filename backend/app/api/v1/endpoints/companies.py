"""
Target Employers & Companies API Router.
Stage 6: Network / Contacts.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.company_service import company_service

router = APIRouter()


@router.get(
    "",
    response_model=CompanyListResponse,
    summary="List target companies",
)
async def list_companies(
    search: Optional[str] = Query(None, description="Search by name, industry, location"),
    industry: Optional[str] = Query(None, description="Filter by exact industry"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field: name, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    return await company_service.list_companies(
        db=db,
        user_id=current_user.id,
        search=search,
        industry=industry,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create target company",
)
async def create_company(
    data: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    return await company_service.create_company(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get target company details",
)
async def get_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    return await company_service.get_company(
        db=db,
        user_id=current_user.id,
        company_id=company_id,
    )


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Update target company",
)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    return await company_service.update_company(
        db=db,
        user_id=current_user.id,
        company_id=company_id,
        data=data,
    )


@router.delete(
    "/{company_id}",
    summary="Delete target company",
)
async def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await company_service.delete_company(
        db=db,
        user_id=current_user.id,
        company_id=company_id,
    )
    return {"message": "Company deleted successfully"}
