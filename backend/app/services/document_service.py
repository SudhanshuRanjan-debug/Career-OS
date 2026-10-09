"""
Document Vault service — private document storage, categorisation, and retrieval.
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_validation import validate_uploaded_file, sanitize_filename
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.storage.base import StorageBackend

ALLOWED_DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}
VALID_DOC_TYPES = {
    "COVER_LETTER",
    "CERTIFICATE",
    "TRANSCRIPT",
    "PORTFOLIO",
    "RECOMMENDATION",
    "OTHER",
}


class DocumentService:
    """Service layer for private document vault."""

    async def list_documents(
        self, db: AsyncSession, user_id: UUID, doc_type: str | None = None
    ) -> list[DocumentResponse]:
        query = select(Document).where(Document.user_id == user_id, Document.deleted_at.is_(None))
        if doc_type:
            query = query.where(Document.doc_type == doc_type.upper())
        query = query.order_by(Document.uploaded_at.desc())

        result = await db.execute(query)
        documents = result.scalars().all()
        return [DocumentResponse.model_validate(d) for d in documents]

    async def upload_document(
        self,
        db: AsyncSession,
        storage: StorageBackend,
        user_id: UUID,
        file: UploadFile,
        name: str | None = None,
        doc_type: str = "OTHER",
        description: str | None = None,
    ) -> DocumentResponse:
        # 1. Normalize doc type
        normalized_doc_type = doc_type.upper() if doc_type else "OTHER"
        if normalized_doc_type not in VALID_DOC_TYPES:
            normalized_doc_type = "OTHER"

        # 2. Deep content validation, magic byte checking, and size limits
        validated = await validate_uploaded_file(
            file=file,
            allowed_extensions=ALLOWED_DOC_EXTENSIONS,
            max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        )

        display_name = name.strip() if name and name.strip() else Path(validated.safe_filename).stem

        # 3. Storage key
        file_uuid = uuid.uuid4()
        storage_key = f"documents/{user_id}/{file_uuid}_{validated.safe_filename}"

        # 4. Write to storage
        await storage.put(storage_key, validated.content, validated.mime_type)

        # 5. Database record
        document = Document(
            user_id=user_id,
            name=display_name,
            doc_type=normalized_doc_type,
            original_filename=validated.original_filename,
            storage_key=storage_key,
            file_size_bytes=validated.size_bytes,
            mime_type=validated.mime_type,
            description=description,
            version=1,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return DocumentResponse.model_validate(document)

    async def get_document_for_download(
        self, db: AsyncSession, storage: StorageBackend, user_id: UUID, doc_id: UUID
    ) -> tuple[Document, any]:
        result = await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.user_id == user_id,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied",
            )

        try:
            file_stream = await storage.get_stream(document.storage_key)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found in storage",
            )

        return document, file_stream

    async def delete_document(self, db: AsyncSession, user_id: UUID, doc_id: UUID) -> None:
        result = await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied",
            )

        doc.deleted_at = datetime.now(timezone.utc)
        await db.commit()


document_service = DocumentService()
