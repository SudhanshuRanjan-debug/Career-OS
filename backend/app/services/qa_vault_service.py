"""
Q&A Vault Service.
Stage 5 Master Implementation.
Provides CRUD for candidate reusable Q&A templates.
Strict tenant isolation: scoped solely to user_id.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.qa_vault import QAVaultEntry
from app.schemas.qa_vault import QAVaultEntryCreate, QAVaultEntryResponse, QAVaultEntryUpdate, QAVaultListResponse


class QAVaultService:
    async def list_entries(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: Optional[str] = None,
    ) -> QAVaultListResponse:
        query = select(QAVaultEntry).where(QAVaultEntry.user_id == user_id)
        if category:
            query = query.where(QAVaultEntry.category == category)
        query = query.order_by(QAVaultEntry.created_at.desc())

        result = await db.execute(query)
        items = list(result.scalars().all())
        return QAVaultListResponse(
            items=[QAVaultEntryResponse.model_validate(item) for item in items],
            total=len(items),
        )

    async def get_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> QAVaultEntry:
        query = select(QAVaultEntry).where(
            QAVaultEntry.id == entry_id,
            QAVaultEntry.user_id == user_id,
        )
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        if not entry:
            raise NotFoundError("Q&A Vault entry not found")
        return entry

    async def create_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: QAVaultEntryCreate,
    ) -> QAVaultEntryResponse:
        entry = QAVaultEntry(
            user_id=user_id,
            question=data.question,
            answer=data.answer,
            category=data.category,
            is_template=data.is_template,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return QAVaultEntryResponse.model_validate(entry)

    async def update_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
        data: QAVaultEntryUpdate,
    ) -> QAVaultEntryResponse:
        entry = await self.get_entry(db=db, user_id=user_id, entry_id=entry_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        await db.commit()
        await db.refresh(entry)
        return QAVaultEntryResponse.model_validate(entry)

    async def delete_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        entry = await self.get_entry(db=db, user_id=user_id, entry_id=entry_id)
        await db.delete(entry)
        await db.commit()


qa_vault_service = QAVaultService()
