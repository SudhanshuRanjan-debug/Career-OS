"""
Organization Service — manages employer/recruiter company profile.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.organization import Organization
from app.schemas.organization import OrganizationUpdate


class OrganizationService:

    async def get_by_owner_id(self, db: AsyncSession, owner_user_id: UUID) -> Organization:
        """Retrieve organization owned by recruiter user."""
        stmt = select(Organization).where(Organization.owner_user_id == owner_user_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization not found for this recruiter account")
        return org

    async def get_by_id(self, db: AsyncSession, org_id: UUID) -> Organization:
        """Retrieve organization by primary key ID."""
        stmt = select(Organization).where(Organization.id == org_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization not found")
        return org

    async def update_organization(
        self,
        db: AsyncSession,
        owner_user_id: UUID,
        data: OrganizationUpdate,
    ) -> Organization:
        """Update organization details for the authenticated recruiter."""
        org = await self.get_by_owner_id(db, owner_user_id)

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(org, field, value)

        org.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(org)
        return org


organization_service = OrganizationService()
