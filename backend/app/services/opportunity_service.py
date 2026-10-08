"""
Opportunity & SavedOpportunity service layer.
Enforces strict per-user tenant isolation on all operations.
"""

import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.company import Company
from app.models.opportunity import Opportunity, SavedOpportunity
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunityUpdate,
    SavedOpportunityListResponse,
    SavedOpportunityResponse,
)


class OpportunityService:

    async def list_opportunities(
        self,
        db: AsyncSession,
        user_id: UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        location_type: Optional[str] = None,
        employment_type: Optional[str] = None,
        is_saved: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> OpportunityListResponse:
        """
        List and search opportunities for the authenticated user with filtering,
        pagination, and is_saved bookmark state.
        """
        base_filters = [Opportunity.user_id == user_id]

        if search and search.strip():
            term = f"%{search.strip()}%"
            base_filters.append(
                or_(
                    Opportunity.title.ilike(term),
                    Opportunity.company_name.ilike(term),
                    Opportunity.location.ilike(term),
                    Opportunity.description.ilike(term),
                )
            )

        if status:
            base_filters.append(Opportunity.status == status.upper())

        if location_type:
            base_filters.append(Opportunity.location_type == location_type.upper())

        if employment_type:
            base_filters.append(Opportunity.employment_type == employment_type.upper())

        # Build count query
        count_stmt = (
            select(func.count(distinct(Opportunity.id)))
            .outerjoin(
                SavedOpportunity,
                and_(
                    SavedOpportunity.opportunity_id == Opportunity.id,
                    SavedOpportunity.user_id == user_id,
                ),
            )
            .where(*base_filters)
        )

        if is_saved is True:
            count_stmt = count_stmt.where(SavedOpportunity.id.is_not(None))
        elif is_saved is False:
            count_stmt = count_stmt.where(SavedOpportunity.id.is_(None))

        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        # Build main data query
        stmt = (
            select(Opportunity, SavedOpportunity.id.label("saved_record_id"))
            .outerjoin(
                SavedOpportunity,
                and_(
                    SavedOpportunity.opportunity_id == Opportunity.id,
                    SavedOpportunity.user_id == user_id,
                ),
            )
            .where(*base_filters)
        )

        if is_saved is True:
            stmt = stmt.where(SavedOpportunity.id.is_not(None))
        elif is_saved is False:
            stmt = stmt.where(SavedOpportunity.id.is_(None))

        # Sort
        sort_col_map = {
            "created_at": Opportunity.created_at,
            "title": Opportunity.title,
            "company_name": Opportunity.company_name,
            "posted_date": Opportunity.posted_date,
            "expiry_date": Opportunity.expiry_date,
            "status": Opportunity.status,
        }
        sort_col = sort_col_map.get(sort_by, Opportunity.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await db.execute(stmt)
        rows = result.all()

        items: list[OpportunityResponse] = []
        for opp, saved_record_id in rows:
            opp_dict = {
                c.name: getattr(opp, c.name)
                for c in opp.__table__.columns
            }
            opp_dict["is_saved"] = saved_record_id is not None
            items.append(OpportunityResponse.model_validate(opp_dict))

        total_pages = math.ceil(total / page_size) if page_size > 0 else 1

        return OpportunityListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
    ) -> OpportunityResponse:
        """
        Retrieve a single opportunity owned by the user. Returns 404 for non-existent
        or other users' opportunities.
        """
        stmt = select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.user_id == user_id,
        )
        result = await db.execute(stmt)
        opp = result.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity not found")

        # Check is_saved
        saved_stmt = select(SavedOpportunity.id).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        saved_res = (await db.execute(saved_stmt)).scalar_one_or_none()

        opp_dict = {
            c.name: getattr(opp, c.name)
            for c in opp.__table__.columns
        }
        opp_dict["is_saved"] = saved_res is not None

        return OpportunityResponse.model_validate(opp_dict)

    async def create_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: OpportunityCreate,
    ) -> OpportunityResponse:
        """
        Create a new opportunity for the user. If company_id is provided,
        enforce that the company belongs to user_id.
        """
        if data.company_id:
            comp_stmt = select(Company.id).where(
                Company.id == data.company_id,
                Company.user_id == user_id,
            )
            comp = (await db.execute(comp_stmt)).scalar_one_or_none()
            if not comp:
                raise NotFoundError("Company not found")

        opp_data = data.model_dump()
        opp = Opportunity(
            user_id=user_id,
            **opp_data,
        )
        db.add(opp)
        await db.commit()
        await db.refresh(opp)

        opp_dict = {
            c.name: getattr(opp, c.name)
            for c in opp.__table__.columns
        }
        opp_dict["is_saved"] = False

        return OpportunityResponse.model_validate(opp_dict)

    async def update_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
        data: OpportunityUpdate,
    ) -> OpportunityResponse:
        """
        Update an existing opportunity owned by the user.
        """
        stmt = select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.user_id == user_id,
        )
        result = await db.execute(stmt)
        opp = result.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity not found")

        update_dict = data.model_dump(exclude_unset=True)

        if "company_id" in update_dict and update_dict["company_id"] is not None:
            comp_stmt = select(Company.id).where(
                Company.id == update_dict["company_id"],
                Company.user_id == user_id,
            )
            comp = (await db.execute(comp_stmt)).scalar_one_or_none()
            if not comp:
                raise NotFoundError("Company not found")

        for key, value in update_dict.items():
            setattr(opp, key, value)

        opp.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(opp)

        saved_stmt = select(SavedOpportunity.id).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        saved_res = (await db.execute(saved_stmt)).scalar_one_or_none()

        opp_dict = {
            c.name: getattr(opp, c.name)
            for c in opp.__table__.columns
        }
        opp_dict["is_saved"] = saved_res is not None

        return OpportunityResponse.model_validate(opp_dict)

    async def delete_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
    ) -> None:
        """
        Delete an opportunity owned by the user. Cascades to saved_opportunities.
        """
        stmt = select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.user_id == user_id,
        )
        result = await db.execute(stmt)
        opp = result.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity not found")

        await db.delete(opp)
        await db.commit()

    async def save_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
        notes: Optional[str] = None,
    ) -> SavedOpportunityResponse:
        """
        Save/bookmark an opportunity. Idempotent: repeated calls do not create duplicates.
        """
        stmt = select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.user_id == user_id,
        )
        result = await db.execute(stmt)
        opp = result.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity not found")

        saved_stmt = select(SavedOpportunity).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        existing_saved = (await db.execute(saved_stmt)).scalar_one_or_none()

        if existing_saved:
            if notes is not None:
                existing_saved.notes = notes
                await db.commit()
                await db.refresh(existing_saved)
            saved_record = existing_saved
        else:
            new_saved = SavedOpportunity(
                user_id=user_id,
                opportunity_id=opportunity_id,
                notes=notes,
            )
            db.add(new_saved)
            await db.commit()
            await db.refresh(new_saved)
            saved_record = new_saved

        opp_dict = {
            c.name: getattr(opp, c.name)
            for c in opp.__table__.columns
        }
        opp_dict["is_saved"] = True
        opp_resp = OpportunityResponse.model_validate(opp_dict)

        return SavedOpportunityResponse(
            id=saved_record.id,
            user_id=saved_record.user_id,
            opportunity_id=saved_record.opportunity_id,
            saved_at=saved_record.saved_at,
            notes=saved_record.notes,
            opportunity=opp_resp,
        )

    async def unsave_opportunity(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
    ) -> None:
        """
        Remove an opportunity from the saved queue. Idempotent.
        """
        stmt = select(Opportunity.id).where(
            Opportunity.id == opportunity_id,
            Opportunity.user_id == user_id,
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise NotFoundError("Opportunity not found")

        saved_stmt = select(SavedOpportunity).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        saved = (await db.execute(saved_stmt)).scalar_one_or_none()
        if saved:
            await db.delete(saved)
            await db.commit()

    async def list_saved_opportunities(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> SavedOpportunityListResponse:
        """
        List all saved opportunities for the user, ordered by saved_at DESC.
        """
        stmt = (
            select(SavedOpportunity)
            .options(selectinload(SavedOpportunity.opportunity))
            .where(SavedOpportunity.user_id == user_id)
            .order_by(SavedOpportunity.saved_at.desc())
        )
        result = await db.execute(stmt)
        saved_records = result.scalars().all()

        items: list[SavedOpportunityResponse] = []
        for rec in saved_records:
            opp = rec.opportunity
            opp_dict = {
                c.name: getattr(opp, c.name)
                for c in opp.__table__.columns
            }
            opp_dict["is_saved"] = True
            opp_resp = OpportunityResponse.model_validate(opp_dict)

            items.append(
                SavedOpportunityResponse(
                    id=rec.id,
                    user_id=rec.user_id,
                    opportunity_id=rec.opportunity_id,
                    saved_at=rec.saved_at,
                    notes=rec.notes,
                    opportunity=opp_resp,
                )
            )

        return SavedOpportunityListResponse(items=items, total=len(items))


opportunity_service = OpportunityService()
