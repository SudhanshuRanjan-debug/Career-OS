"""
Resume service — versioned resume tracking, upload validation, secure storage, and soft-deletion.
Preserves historical application version integrity.
"""

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_validation import validate_uploaded_file, sanitize_filename
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.storage.base import StorageBackend

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Fallback for some browsers, checked with extension
}


class ResumeService:
    """Service layer for resume vault operations."""

    async def list_resumes(self, db: AsyncSession, user_id: UUID) -> list[ResumeResponse]:
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
            .order_by(Resume.is_default.desc(), Resume.uploaded_at.desc())
        )
        resumes = result.scalars().all()
        return [ResumeResponse.model_validate(r) for r in resumes]

    async def upload_resume(
        self,
        db: AsyncSession,
        storage: StorageBackend,
        user_id: UUID,
        file: UploadFile,
        name: str | None = None,
    ) -> ResumeResponse:
        # Validate file content, magic bytes, DOCX structure, and size
        validated = await validate_uploaded_file(
            file=file,
            allowed_extensions=ALLOWED_EXTENSIONS,
            max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        )

        # Default name if none provided
        display_name = name.strip() if name and name.strip() else Path(validated.safe_filename).stem

        # 4. Version calculation
        version_query = await db.execute(
            select(func.max(Resume.version)).where(
                Resume.user_id == user_id,
                Resume.name == display_name,
            )
        )
        max_v = version_query.scalar()
        version = (max_v + 1) if max_v is not None else 1

        # 5. Check if user has existing active resumes (if none, mark this default)
        count_query = await db.execute(
            select(func.count(Resume.id)).where(
                Resume.user_id == user_id,
                Resume.deleted_at.is_(None),
            )
        )
        active_count = count_query.scalar() or 0
        is_default = active_count == 0

        # 6. Generate secure, unique storage key
        file_uuid = uuid.uuid4()
        storage_key = f"resumes/{user_id}/{file_uuid}_{validated.safe_filename}"

        # 7. Write to storage backend
        await storage.put(storage_key, validated.content, validated.mime_type)

        # 8. Record in database
        resume = Resume(
            user_id=user_id,
            name=display_name,
            original_filename=validated.original_filename,
            storage_key=storage_key,
            file_size_bytes=validated.size_bytes,
            mime_type=validated.mime_type,
            version=version,
            is_default=is_default,
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)

        return ResumeResponse.model_validate(resume)

    async def update_resume_name(
        self, db: AsyncSession, user_id: UUID, resume_id: UUID, new_name: str
    ) -> ResumeResponse:
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.deleted_at.is_(None),
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied",
            )

        resume.name = new_name.strip()
        await db.commit()
        await db.refresh(resume)
        return ResumeResponse.model_validate(resume)

    async def set_default_resume(
        self, db: AsyncSession, user_id: UUID, resume_id: UUID
    ) -> ResumeResponse:
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.deleted_at.is_(None),
            )
        )
        target_resume = result.scalar_one_or_none()
        if not target_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied",
            )

        # Unset all other default resumes for this user
        await db.execute(
            update(Resume)
            .where(Resume.user_id == user_id)
            .values(is_default=False)
        )

        target_resume.is_default = True
        await db.commit()
        await db.refresh(target_resume)
        return ResumeResponse.model_validate(target_resume)

    async def get_resume_for_download(
        self, db: AsyncSession, storage: StorageBackend, user_id: UUID, resume_id: UUID
    ) -> tuple[Resume, any]:
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied",
            )

        try:
            file_stream = await storage.get_stream(resume.storage_key)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file not found on storage",
            )

        return resume, file_stream

    async def delete_resume(
        self, db: AsyncSession, user_id: UUID, resume_id: UUID
    ) -> None:
        """Soft-delete resume preserving historical application records."""
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.deleted_at.is_(None),
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied",
            )

        was_default = resume.is_default
        resume.deleted_at = datetime.now(timezone.utc)
        resume.is_default = False

        # If deleted resume was default, appoint the next most recent active resume as default
        if was_default:
            next_active = await db.execute(
                select(Resume)
                .where(
                    Resume.user_id == user_id,
                    Resume.deleted_at.is_(None),
                    Resume.id != resume.id,
                )
                .order_by(Resume.uploaded_at.desc())
                .limit(1)
            )
            new_default = next_active.scalar_one_or_none()
            if new_default:
                new_default.is_default = True

        await db.commit()


resume_service = ResumeService()
