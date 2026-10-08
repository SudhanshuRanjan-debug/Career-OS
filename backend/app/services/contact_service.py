"""
Contact Service.
Stage 6: Professional Network & Contacts.
Provides CRUD, search, filtering, company association, and linked applications
for professional contacts under strict multi-tenant isolation.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.company import CompanySummary
from app.schemas.contact import (
    ApplicationSummary,
    ContactCreate,
    ContactDetailResponse,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)


class ContactService:

    async def list_contacts(
        self,
        db: AsyncSession,
        user_id: UUID,
        search: Optional[str] = None,
        contact_type: Optional[str] = None,
        company_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ContactListResponse:
        """
        List contacts with server-side search, type filtering, company filtering, and pagination.
        Enforces strict tenant isolation on user_id.
        """
        base_query = (
            select(Contact)
            .where(Contact.user_id == user_id)
            .outerjoin(Company, Contact.company_id == Company.id)
        )

        if search:
            s = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Contact.first_name.ilike(s),
                    Contact.last_name.ilike(s),
                    Contact.email.ilike(s),
                    Contact.role.ilike(s),
                    Company.name.ilike(s),
                )
            )

        if contact_type:
            base_query = base_query.where(Contact.contact_type == contact_type.strip().upper())

        if company_id:
            base_query = base_query.where(Contact.company_id == company_id)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        # Sorting
        sort_field_map = {
            "first_name": Contact.first_name,
            "last_name": Contact.last_name,
            "created_at": Contact.created_at,
            "updated_at": Contact.updated_at,
            "role": Contact.role,
        }
        sort_col = sort_field_map.get(sort_by, Contact.created_at)
        if sort_order.lower() == "asc":
            base_query = base_query.order_by(sort_col.asc())
        else:
            base_query = base_query.order_by(sort_col.desc())

        # Pagination & Eager load company
        offset = (page - 1) * page_size
        query = (
            base_query.offset(offset)
            .limit(page_size)
            .options(selectinload(Contact.company))
        )
        result = await db.execute(query)
        contacts = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        items = [self._build_contact_response(c) for c in contacts]

        return ContactListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def create_contact(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: ContactCreate,
    ) -> ContactResponse:
        """
        Create a new professional contact.
        Validates company_id belongs to the current user.
        """
        if data.company_id:
            comp_res = await db.execute(
                select(Company).where(
                    Company.id == data.company_id,
                    Company.user_id == user_id,
                )
            )
            if not comp_res.scalar_one_or_none():
                raise NotFoundError("Referenced company not found or does not belong to user")

        contact = Contact(
            user_id=user_id,
            company_id=data.company_id,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip() if data.last_name else None,
            role=data.role.strip() if data.role else None,
            contact_type=data.contact_type or "RECRUITER",
            email=data.email,
            phone=data.phone.strip() if data.phone else None,
            linkedin_url=data.linkedin_url,
            relationship=data.relationship.strip() if data.relationship else None,
            notes=data.notes,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)

        # Reload with company
        res = await db.execute(
            select(Contact)
            .where(Contact.id == contact.id)
            .options(selectinload(Contact.company))
        )
        loaded = res.scalar_one()
        return self._build_contact_response(loaded)

    async def get_contact(
        self,
        db: AsyncSession,
        user_id: UUID,
        contact_id: UUID,
    ) -> ContactDetailResponse:
        """
        Get contact details including associated company and linked applications.
        Raises NotFoundError (HTTP 404) if contact does not exist or belongs to another user.
        """
        res = await db.execute(
            select(Contact)
            .where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
            )
            .options(selectinload(Contact.company))
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found")

        # Load linked applications belonging to this user
        app_res = await db.execute(
            select(Application)
            .where(
                Application.contact_id == contact_id,
                Application.user_id == user_id,
            )
            .order_by(Application.created_at.desc())
        )
        linked_apps = app_res.scalars().all()

        linked_app_summaries = [
            ApplicationSummary(
                id=a.id,
                job_title=a.job_title,
                company_name=a.company_name,
                current_stage=a.current_stage,
                status=a.status,
                applied_date=a.applied_date,
            )
            for a in linked_apps
        ]

        company_summary = None
        if contact.company:
            company_summary = CompanySummary.model_validate(contact.company)

        return ContactDetailResponse(
            id=contact.id,
            user_id=contact.user_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            role=contact.role,
            contact_type=contact.contact_type,
            email=contact.email,
            phone=contact.phone,
            linkedin_url=contact.linkedin_url,
            relationship=contact.relationship,
            notes=contact.notes,
            company_id=contact.company_id,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
            company=company_summary,
            linked_applications=linked_app_summaries,
        )

    async def update_contact(
        self,
        db: AsyncSession,
        user_id: UUID,
        contact_id: UUID,
        data: ContactUpdate,
    ) -> ContactResponse:
        """
        Update contact details.
        Raises NotFoundError (HTTP 404) if contact does not belong to user.
        """
        res = await db.execute(
            select(Contact)
            .where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
            )
            .options(selectinload(Contact.company))
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found")

        update_dict = data.model_dump(exclude_unset=True)

        if "company_id" in update_dict and update_dict["company_id"] is not None:
            comp_res = await db.execute(
                select(Company).where(
                    Company.id == update_dict["company_id"],
                    Company.user_id == user_id,
                )
            )
            if not comp_res.scalar_one_or_none():
                raise NotFoundError("Referenced company not found or does not belong to user")

        for field, value in update_dict.items():
            setattr(contact, field, value)

        contact.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(contact)

        # Reload with company
        reload_res = await db.execute(
            select(Contact)
            .where(Contact.id == contact.id)
            .options(selectinload(Contact.company))
        )
        loaded = reload_res.scalar_one()
        return self._build_contact_response(loaded)

    async def delete_contact(
        self,
        db: AsyncSession,
        user_id: UUID,
        contact_id: UUID,
    ) -> None:
        """
        Delete contact. Database ON DELETE SET NULL detaches any linked applications or tasks.
        Raises NotFoundError (HTTP 404) if contact does not belong to user.
        """
        res = await db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
            )
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found")

        await db.delete(contact)
        await db.commit()

    def _build_contact_response(self, contact: Contact) -> ContactResponse:
        company_summary = None
        if contact.company:
            company_summary = CompanySummary.model_validate(contact.company)

        return ContactResponse(
            id=contact.id,
            user_id=contact.user_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            role=contact.role,
            contact_type=contact.contact_type,
            email=contact.email,
            phone=contact.phone,
            linkedin_url=contact.linkedin_url,
            relationship=contact.relationship,
            notes=contact.notes,
            company_id=contact.company_id,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
            company=company_summary,
        )


contact_service = ContactService()
