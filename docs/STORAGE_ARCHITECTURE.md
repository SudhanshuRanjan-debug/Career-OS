# Storage Architecture & Document Vault Specification
## Career & Job Application Management Platform — File & Document Storage

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Storage Principles & Privacy Requirements

1. **No Binary Data in PostgreSQL**: Database tables store only file metadata (file size, MIME type, original filename, upload timestamp, version, and unique `storage_key`). Binary file streams are handled strictly by the storage layer.
2. **Zero Public Access**: Candidate documents (resumes, cover letters, transcripts, certificates) are strictly private. No public storage bucket or unauthenticated URL exists.
3. **Pluggable Storage Abstraction**: Business logic interacts exclusively with an abstract `StorageService` interface, allowing seamless switching between local development storage and Azure Blob Storage in production.
4. **Immutable Storage Keys**: Storage keys are generated as UUIDv4-based strings. When a file is uploaded, its storage key is permanent. Replacing a resume creates a new record and new storage key, preserving historical application links.

---

## 2. Storage Service Abstraction

```python
# backend/app/storage/base.py
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Tuple

class StorageService(ABC):
    """Abstract interface for file storage operations."""

    @abstractmethod
    async def put(
        self,
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str
    ) -> int:
        """Store a file and return bytes written."""
        pass

    @abstractmethod
    async def get_stream(
        self,
        storage_key: str
    ) -> Tuple[BinaryIO, str, int]:
        """Retrieve a file stream with content_type and content_length."""
        pass

    @abstractmethod
    async def get_signed_url(
        self,
        storage_key: str,
        expires_in_seconds: int = 300
    ) -> str:
        """Generate a time-limited authorized download URL."""
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Delete a file from the underlying storage."""
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Check if a file exists."""
        pass
```

---

## 3. Storage Providers

### 3.1 LocalStorageProvider (Development & Local Docker)
- **Root Path**: Configurable via `STORAGE_LOCAL_ROOT` (defaults to `./storage/private`).
- **Structure**:
  ```
  storage/private/
  ├── resumes/
  │   └── {user_id}/{storage_key}.pdf
  ├── documents/
  │   └── {user_id}/{storage_key}.pdf
  └── photos/
      └── {user_id}/{storage_key}.webp
  ```
- **Security**: Directory permissions restricted; files served only via authenticated FastAPI streaming endpoints (`StreamingResponse`).

### 3.2 AzureBlobStorageProvider (Staging & Production)
- **Service**: Azure Blob Storage Private Container.
- **Authentication**: Managed Identity (Azure Container Apps) or connection string via Azure Key Vault.
- **Container Name**: Configurable via `AZURE_STORAGE_CONTAINER` (defaults to `career-documents-private`).
- **Access Model**:
  - Small to medium documents: Streamed securely through FastAPI backend.
  - Large downloads: Generated short-lived Shared Access Signature (SAS) URLs (valid for 5–15 minutes).

---

## 4. File Validation & Constraints

| Document Type | Allowed Extensions | Allowed MIME Types | Max File Size |
|:--------------|:-------------------|:-------------------|:-------------:|
| **Resume** | `.pdf`, `.doc`, `.docx` | `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 10 MB |
| **Cover Letter** | `.pdf`, `.doc`, `.docx`, `.txt` | `application/pdf`, `application/msword`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 5 MB |
| **Certificate / Transcript** | `.pdf`, `.png`, `.jpg`, `.jpeg` | `application/pdf`, `image/png`, `image/jpeg` | 10 MB |
| **Profile Photo** | `.png`, `.jpg`, `.jpeg`, `.webp` | `image/png`, `image/jpeg`, `image/webp` | 2 MB |

---

## 5. Historical Versioning & Application Pinning

When a candidate applies to a job, the platform must preserve the exact document version used:

```
Step 1: User uploads "FullStack_Resume_v1.pdf"
        → DB row in `resumes`: ID = R1, version = 1, storage_key = "resumes/u1/k1.pdf"

Step 2: User applies to Company A
        → DB row in `applications`: ID = A1, resume_id = R1

Step 3: Two weeks later, user updates resume with new skills:
        → User uploads "FullStack_Resume_v2.pdf"
        → DB row in `resumes`: ID = R2, version = 2, storage_key = "resumes/u1/k2.pdf"
        → Old row R1 is marked `is_default = FALSE` (NOT overwritten or deleted)

Step 4: User inspects Application A1:
        → A1 still references R1. Download streams file at "resumes/u1/k1.pdf"
        → Historical accuracy is completely preserved.
```

---

## 6. Cross-Tenant Download Authorization (Dual-Sided Access)

Document vaults are strictly private to the candidate by default. A recruiter is never granted broad access to a candidate's file vault.

### Authorization Matrix for Resume / Document Streaming

1. **Candidate Own Access (`/api/v1/resumes/:id/download`, `/api/v1/documents/:id/download`)**:
   - Authorized if `file.user_id == current_user.id`.
   - Returns 404/403 if requested by any other user.

2. **Recruiter Application-Scoped Access (`/api/v1/recruiter/applications/:id/resume`)**:
   - Authorized if and only if:
     - `current_user.role == 'HIRER'`
     - `application.job_posting.organization.owner_user_id == current_user.id`
     - The stream served corresponds strictly to `application.resume_id` submitted with that application.
   - If the application does not belong to the recruiter's organization, 404 / 403 Forbidden is returned.
   - The recruiter has zero access to other versions in `resumes` or unattached records in `documents`.
