"""
Q&A Vault API Router.
Stage 5 Master Implementation.
Provides endpoints for managing reusable Q&A templates.
Strict authentication and tenant isolation.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.qa_vault import (
    QAVaultEntryCreate,
    QAVaultEntryResponse,
    QAVaultEntryUpdate,
    QAVaultListResponse,
)
from app.services.qa_vault_service import qa_vault_service

router = APIRouter()


@router.get("", response_model=QAVaultListResponse)
async def list_qa_vault_entries(
    category: Optional[str] = Query(None, description="Filter by category (GENERAL, BEHAVIORAL, TECHNICAL, etc.)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List reusable Q&A answer templates for the current authenticated user.
    """
    return await qa_vault_service.list_entries(
        db=db,
        user_id=current_user.id,
        category=category,
    )


@router.post("", response_model=QAVaultEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_qa_vault_entry(
    data: QAVaultEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new reusable Q&A template.
    """
    return await qa_vault_service.create_entry(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.put("/{entry_id}", response_model=QAVaultEntryResponse)
async def update_qa_vault_entry(
    entry_id: UUID,
    data: QAVaultEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing Q&A template.
    Returns 404 if not found or belongs to another user.
    """
    return await qa_vault_service.update_entry(
        db=db,
        user_id=current_user.id,
        entry_id=entry_id,
        data=data,
    )


@router.delete("/{entry_id}", response_model=MessageResponse)
async def delete_qa_vault_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a reusable Q&A template.
    """
    await qa_vault_service.delete_entry(
        db=db,
        user_id=current_user.id,
        entry_id=entry_id,
    )
    return MessageResponse(message="Q&A template deleted successfully")
