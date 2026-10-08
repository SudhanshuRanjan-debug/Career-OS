"""
Company Service.
Stage 6: Target Employers & Companies.
Provides CRUD and search for candidate target companies under strict multi-tenant isolation.
Reuses existing company records by name to prevent duplicate entries.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)


class CompanyService:

    async def list_companies(
        self,
        db: AsyncSession,
        user_id: UUID,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> CompanyListResponse:
        """
        List candidate target companies with search, industry filter, and pagination.
        Enforces strict tenant isolation on user_id.
        """
        base_query = select(Company).where(Company.user_id == user_id)

        if search:
            s = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Company.name.ilike(s),
                    Company.industry.ilike(s),
                    Company.location.ilike(s),
                )
            )

        if industry:
            base_query = base_query.where(Company.industry == industry.strip())

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        # Sorting
        sort_col = getattr(Company, sort_by, Company.name)
        if sort_order.lower() == "desc":
            base_query = base_query.order_by(sort_col.desc())
        else:
            base_query = base_query.order_by(sort_col.asc())

        # Pagination
        offset = (page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)
        result = await db.execute(query)
        companies = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        items = [CompanyResponse.model_validate(c) for c in companies]

        return CompanyListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def create_company(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: CompanyCreate,
    ) -> CompanyResponse:
        """
        Create a new target company or reuse an existing company with matching name.
        Enforces user_id ownership.
        """
        # De-duplication check: if user already has a company with this exact name (case-insensitive), reuse it
        existing_res = await db.execute(
            select(Company).where(
                Company.user_id == user_id,
                func.lower(Company.name) == func.lower(data.name.strip()),
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            # Update missing fields if provided in creation request
            updated = False
            for field in ("website", "industry", "size", "location", "description", "logo_url", "linkedin_url"):
                val = getattr(data, field, None)
                if val and not getattr(existing, field, None):
                    setattr(existing, field, val)
                    updated = True
            if updated:
                existing.updated_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(existing)
            return CompanyResponse.model_validate(existing)

        company = Company(
            user_id=user_id,
            name=data.name.strip(),
            website=data.website,
            industry=data.industry,
            size=data.size,
            location=data.location,
            description=data.description,
            notes=data.notes,
            logo_url=data.logo_url,
            linkedin_url=data.linkedin_url,
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return CompanyResponse.model_validate(company)

    async def get_company(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
    ) -> CompanyResponse:
        """
        Retrieve single target company by ID.
        Raises NotFoundError (HTTP 404) if company does not exist or belongs to another user.
        """
        res = await db.execute(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == user_id,
            )
        )
        company = res.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company not found")
        return CompanyResponse.model_validate(company)

    async def update_company(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        data: CompanyUpdate,
    ) -> CompanyResponse:
        """
        Update company details.
        Raises NotFoundError (HTTP 404) if company does not belong to user.
        """
        res = await db.execute(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == user_id,
            )
        )
        company = res.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company not found")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(company, field, value)

        company.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(company)
        return CompanyResponse.model_validate(company)

    async def delete_company(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
    ) -> None:
        """
        Delete target company.
        Raises NotFoundError (HTTP 404) if company does not belong to user.
        """
        res = await db.execute(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == user_id,
            )
        )
        company = res.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company not found")

        await db.delete(company)
        await db.commit()


company_service = CompanyService()
