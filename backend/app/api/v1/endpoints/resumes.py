"""
Resumes API: list, upload, rename, set default, download stream, and soft-delete.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_storage, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.resume import ResumeListResponse, ResumeResponse, ResumeUpdate
from app.services.resume_service import resume_service
from app.storage.base import StorageBackend

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await resume_service.list_resumes(db, current_user.id)
    return ResumeListResponse(items=items, total=len(items))


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    name: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    return await resume_service.upload_resume(
        db=db,
        storage=storage,
        user_id=current_user.id,
        file=file,
        name=name,
    )


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    payload: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await resume_service.update_resume_name(
        db=db,
        user_id=current_user.id,
        resume_id=resume_id,
        new_name=payload.name,
    )


@router.post("/{resume_id}/set-default", response_model=ResumeResponse)
async def set_default_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await resume_service.set_default_resume(
        db=db,
        user_id=current_user.id,
        resume_id=resume_id,
    )


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    resume, file_stream = await resume_service.get_resume_for_download(
        db=db,
        storage=storage,
        user_id=current_user.id,
        resume_id=resume_id,
    )

    mime_type = resume.mime_type or "application/pdf"
    filename = resume.original_filename or f"{resume.name}.pdf"

    def iter_file():
        try:
            while chunk := file_stream.read(64 * 1024):
                yield chunk
        finally:
            file_stream.close()

    return StreamingResponse(
        iter_file(),
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Type": mime_type,
        },
    )



@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await resume_service.delete_resume(
        db=db,
        user_id=current_user.id,
        resume_id=resume_id,
    )
    return MessageResponse(message="Resume soft-deleted successfully (historical applications preserved)")
