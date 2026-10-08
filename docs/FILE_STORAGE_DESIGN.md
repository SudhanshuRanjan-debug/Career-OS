# File Storage Design
## Career & Job Application Management Platform

**Version:** 1.0.0
**Date:** 2026-09-07

---

## 1. Design Goals

1. No binary file data stored in PostgreSQL.
2. PostgreSQL stores only metadata (owner, type, filename, storage_key, size, MIME type, timestamps).
3. File access always requires ownership verification — no public URLs.
4. The storage layer is abstracted so local dev and production use the same interface.
5. Historical resume references in applications must remain valid even if the user "deletes" a resume.
6. Storage keys are immutable once assigned to a file record.

---

## 2. Storage Abstraction Interface

```python
# backend/app/storage/base.py

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):

    @abstractmethod
    async def put(self, key: str, file: BinaryIO, content_type: str) -> None:
        """Upload a file to the storage backend."""
        ...

    @abstractmethod
    async def get_stream(self, key: str) -> BinaryIO:
        """Return a readable stream for the file at key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the file at key from storage."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists at key."""
        ...

    @abstractmethod
    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a time-limited URL for direct download (production use)."""
        ...
```

---

## 3. Storage Key Convention

```
Pattern: {user_id}/{entity_type}/{uuid}.{extension}

Examples:
  resumes/   550e8400-e29b-41d4-a716-446655440000/resumes/a1b2c3d4-....pdf
  documents/ 550e8400-e29b-41d4-a716-446655440000/documents/f9e8d7c6-....docx

Key generation:
  import uuid
  storage_key = f"{user_id}/{entity_type}/{uuid.uuid4()}.{ext}"
```

Keys are generated at upload time and never changed.

---

## 4. Local Development Storage

```python
# backend/app/storage/local_storage.py

import os
import aiofiles
from pathlib import Path
from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """
    Stores files on the local filesystem under STORAGE_LOCAL_PATH.
    Intended for local development only.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, file, content_type: str) -> None:
        dest = self.base_path / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(dest, "wb") as f:
            content = await file.read()
            await f.write(content)

    async def get_stream(self, key: str):
        path = self.base_path / key
        return open(path, "rb")   # returns file-like object for streaming

    async def delete(self, key: str) -> None:
        path = self.base_path / key
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return (self.base_path / key).exists()

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        # In local dev, we return a local API route for serving files.
        # This is never used in production.
        return f"/dev-storage/{key}"
```

---

## 5. Production Storage (Azure Blob)

```python
# backend/app/storage/azure_storage.py

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from .base import StorageBackend


class AzureStorageBackend(StorageBackend):
    """
    Stores files in Azure Blob Storage.
    Container is PRIVATE — no public access.
    Files are served via SAS URLs with expiry.
    """

    def __init__(self, connection_string: str, container_name: str):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = container_name

    async def put(self, key: str, file, content_type: str) -> None:
        blob_client = self.client.get_blob_client(
            container=self.container, blob=key
        )
        content = await file.read()
        await blob_client.upload_blob(
            content, overwrite=False,
            content_settings={"content_type": content_type}
        )

    async def get_stream(self, key: str):
        blob_client = self.client.get_blob_client(
            container=self.container, blob=key
        )
        stream = await blob_client.download_blob()
        return stream

    async def delete(self, key: str) -> None:
        blob_client = self.client.get_blob_client(
            container=self.container, blob=key
        )
        await blob_client.delete_blob()

    async def exists(self, key: str) -> bool:
        blob_client = self.client.get_blob_client(
            container=self.container, blob=key
        )
        return await blob_client.exists()

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container,
            blob_name=key,
            account_key=self.client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        return f"https://{self.client.account_name}.blob.core.windows.net/{self.container}/{key}?{sas_token}"
```

---

## 6. Storage Backend Selection

```python
# backend/app/storage/__init__.py

from app.core.config import settings
from .local_storage import LocalStorageBackend
from .azure_storage import AzureStorageBackend
from .base import StorageBackend


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend(base_path=settings.STORAGE_LOCAL_PATH)
    elif settings.STORAGE_BACKEND == "azure":
        return AzureStorageBackend(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container_name=settings.AZURE_STORAGE_CONTAINER
        )
    raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")


# Singleton used by dependency injection
storage: StorageBackend = get_storage_backend()
```

---

## 7. Upload Flow (Resume Example)

```
1. Client sends:
   POST /resumes
   Content-Type: multipart/form-data
   Body: file=<binary>, name="My Resume v3"

2. FastAPI endpoint:
   - Validates MIME type (PDF, DOC, DOCX only)
   - Validates file size (max 10MB)
   - Generates storage_key = f"{user_id}/resumes/{uuid4()}.pdf"
   - Calls storage.put(storage_key, file, content_type)
   - Creates resumes row in PostgreSQL:
       { user_id, name, original_filename, storage_key,
         file_size_bytes, mime_type, version, is_default=False }
   - Returns resume metadata (NO raw file URL, NO storage_key exposed to client)

3. Response:
   { "id": "uuid", "name": "My Resume v3", "uploaded_at": "...", "is_default": false }
```

---

## 8. Download Flow

```
1. Client sends:
   GET /resumes/:id/download
   Authorization: Bearer <token>

2. FastAPI endpoint:
   - Resolves resume record by ID
   - Verifies resume.user_id == current_user.id (403 if mismatch)
   - Calls storage.get_stream(resume.storage_key)
   - Streams response with headers:
       Content-Type: application/pdf
       Content-Disposition: attachment; filename="<original_filename>"

3. Storage key is NEVER exposed in API responses.
   Client cannot construct download URLs without going through the API.
```

---

## 9. Resume Deletion and Historical Integrity

```
Delete flow:
   DELETE /resumes/:id

   Service checks:
   - Does this resume have active application references?
   - If yes: warn user ("This resume is used by 3 active applications")
   - If user confirms delete:
       resumes.deleted_at = now()   ← SOFT DELETE only
       The storage_key is NOT deleted from storage
       The storage object is NOT deleted

   Result:
   - Resume no longer appears in user's resume list (filtered by deleted_at IS NULL)
   - Existing application records still have resume_id pointing to this row
   - Application can still download the resume via /resumes/:id/download
     (soft-deleted resumes are still accessible for download if referenced by an application
      owned by the same user)

Hard delete policy:
   Physical file deletion from storage only occurs when:
   - No application references the resume (application_id FK check)
   - AND user confirms hard delete
   - This is a future admin/cleanup operation
```

---

## 10. Allowed File Types

| Entity | Allowed MIME Types | Max Size |
|--------|--------------------|----------|
| Resume | application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document | 10 MB |
| Document (cover letter, certificate, etc.) | application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document, image/jpeg, image/png | 10 MB |
| Profile Photo | image/jpeg, image/png, image/webp | 2 MB |

---

## 11. Security Rules

1. Storage keys are UUIDs — not guessable.
2. The Azure container has NO public access — all blobs are private.
3. SAS URLs are time-limited (default 1 hour).
4. Every download endpoint verifies `resource.user_id == current_user.id`.
5. Storage keys are never returned in API responses — clients can only trigger downloads through authenticated API routes.
6. MIME type validation is performed server-side (not trusting the client's Content-Type header alone — actual file content is validated).

---

## 12. Environment Variables for Storage

```env
# .env
STORAGE_BACKEND=local                     # local | azure

# Local storage
STORAGE_LOCAL_PATH=./storage/local

# Azure Blob Storage (production)
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_STORAGE_CONTAINER=career-platform-files
```

---

## 13. Storage Directory Layout (Local Dev)

```
storage/local/
├── {user_id}/
│   ├── resumes/
│   │   ├── {uuid}.pdf
│   │   └── {uuid}.docx
│   ├── documents/
│   │   ├── {uuid}.pdf
│   │   └── {uuid}.pdf
│   └── profile/
│       └── {uuid}.jpg
```
