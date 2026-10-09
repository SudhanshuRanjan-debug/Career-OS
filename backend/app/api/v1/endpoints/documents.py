"""
Document Vault API: list, upload, stream download, and soft-delete.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_storage, require_candidate
from app.core.file_download import create_secure_file_download_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_service import document_service
from app.storage.base import StorageBackend

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    doc_type: Optional[str] = Query(None, description="Optional document type filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await document_service.list_documents(db, current_user.id, doc_type=doc_type)
    return DocumentListResponse(items=items, total=len(items))


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    name: str | None = Form(None),
    doc_type: str = Form("OTHER"),
    description: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    return await document_service.upload_document(
        db=db,
        storage=storage,
        user_id=current_user.id,
        file=file,
        name=name,
        doc_type=doc_type,
        description=description,
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    document, file_stream = await document_service.get_document_for_download(
        db=db,
        storage=storage,
        user_id=current_user.id,
        doc_id=doc_id,
    )

    mime_type = document.mime_type or "application/octet-stream"
    filename = document.original_filename or f"{document.name}.pdf"

    return create_secure_file_download_response(
        file_stream=file_stream,
        filename=filename,
        media_type=mime_type,
    )



@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await document_service.delete_document(
        db=db,
        user_id=current_user.id,
        doc_id=doc_id,
    )
    return MessageResponse(message="Document deleted successfully")
