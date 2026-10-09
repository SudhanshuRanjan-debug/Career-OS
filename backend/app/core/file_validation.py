"""
File validation module: deep content inspection, magic byte verification,
DOCX structure validation, zip bomb protection, and filename sanitization.
"""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# Canonical MIME mappings
CANONICAL_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain",
}

# Signatures for content detection
PDF_SIGNATURE = b"%PDF-"
DOC_OLE2_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
ZIP_SIGNATURE = b"PK\x03\x04"

# WordprocessingML content type expected in DOCX [Content_Types].xml
WORD_PROCESSING_CONTENT_TYPE = b"wordprocessingml.document"

# Zip bomb safety limits
MAX_ZIP_ENTRIES = 500
MAX_UNCOMPRESSED_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_COMPRESSION_RATIO = 100.0


@dataclass
class ValidatedFile:
    content: bytes
    mime_type: str
    original_filename: str
    safe_filename: str
    extension: str
    size_bytes: int


def sanitize_filename(filename: Optional[str], default_name: str = "document.pdf") -> str:
    """
    Sanitize filename to prevent path traversal, control character injection,
    and dangerous shell characters.
    """
    if not filename:
        return default_name

    # Extract only the base name (prevents directory traversal e.g. ../../)
    clean = Path(filename).name

    # Replace all characters except alphanumeric, dot, underscore, and hyphen
    clean = re.sub(r"[^\w\.\-\_]", "_", clean)

    # Collapse repeated dots or leading dots to avoid hidden files and extensions confusion
    clean = re.sub(r"\.{2,}", ".", clean)
    clean = clean.lstrip("._")

    return clean or default_name


def _detect_content_type(content: bytes) -> Optional[str]:
    """Detect format from leading bytes/signatures."""
    stripped = content.lstrip(b"\r\n\t\xef\xbb\xbf ")

    if stripped.startswith(PDF_SIGNATURE):
        return ".pdf"
    if content.startswith(PNG_SIGNATURE):
        return ".png"
    if content.startswith(JPEG_SIGNATURE):
        return ".jpg"
    if content.startswith(DOC_OLE2_SIGNATURE):
        return ".doc"
    if content.startswith(ZIP_SIGNATURE):
        return ".zip"  # Could be DOCX or generic zip
    return None


def _validate_pdf(content: bytes) -> None:
    """Validate PDF header signature."""
    stripped = content.lstrip(b"\r\n\t\xef\xbb\xbf ")
    if not stripped.startswith(PDF_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file: Missing or invalid PDF signature header.",
        )


def _validate_docx(content: bytes) -> None:
    """
    Validate DOCX file integrity and structure:
    1. Valid ZIP archive with local header signature.
    2. Protection against zip bombs (uncompressed ratio, file count, total size).
    3. Confirms required Word document structures ([Content_Types].xml, word/document.xml).
    4. Safe in-memory inspection without extracting files to the filesystem.
    """
    if not content.startswith(ZIP_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid DOCX file: Missing ZIP archive header signature.",
        )

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            infolist = zf.infolist()

            # 1. Check entry count
            if len(infolist) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid DOCX file: Archive is empty.",
                )
            if len(infolist) > MAX_ZIP_ENTRIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid DOCX file: Archive contains too many entries.",
                )

            # 2. Decompression bomb protection
            total_uncompressed = 0
            namelist = set(zf.namelist())

            for info in infolist:
                # Check suspicious path traversal inside archive members
                if info.filename.startswith("/") or ".." in info.filename:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid DOCX file: Malicious member path detected.",
                    )

                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_TOTAL_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid DOCX file: Uncompressed archive size exceeds safety threshold.",
                    )

                # Compression ratio check for larger items
                if info.file_size > 1024 * 1024:
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > MAX_COMPRESSION_RATIO:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid DOCX file: Excessive compression ratio detected.",
                        )

            # 3. Confirm required Word document structures
            if "[Content_Types].xml" not in namelist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid DOCX file: Missing [Content_Types].xml package definition.",
                )

            has_document_xml = "word/document.xml" in namelist
            has_word_content_type = False

            try:
                content_types_data = zf.read("[Content_Types].xml")
                if WORD_PROCESSING_CONTENT_TYPE in content_types_data:
                    has_word_content_type = True
            except Exception:
                pass

            if not (has_document_xml or has_word_content_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid DOCX file: Missing required Word document structure (word/document.xml).",
                )

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid DOCX file: Corrupted or unreadable ZIP archive.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid DOCX file: Unable to parse document archive ({str(exc)}).",
        )


def _validate_doc(content: bytes) -> None:
    """Validate legacy Microsoft Word 97-2004 binary format (OLE2 Compound File)."""
    if not content.startswith(DOC_OLE2_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid DOC file: Missing or invalid Word binary document signature.",
        )


def _validate_png(content: bytes) -> None:
    """Validate PNG signature."""
    if not content.startswith(PNG_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PNG file: Missing or invalid PNG signature.",
        )


def _validate_jpeg(content: bytes) -> None:
    """Validate JPEG signature."""
    if not content.startswith(JPEG_SIGNATURE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JPEG file: Missing or invalid JPEG signature.",
        )


def _validate_txt(content: bytes) -> None:
    """Validate text file content."""
    # Check for null bytes or executable headers
    if b"\x00" in content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text file: Binary null bytes detected.",
        )
    if content.startswith(b"MZ") or content.startswith(b"\x7fELF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text file: Executable binary header detected.",
        )
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text file: Unable to decode text content.",
            )


async def validate_uploaded_file(
    file: UploadFile,
    allowed_extensions: set[str],
    max_size_bytes: int = settings.MAX_UPLOAD_SIZE_BYTES,
) -> ValidatedFile:
    """
    Validate an uploaded file:
    1. Sanitizes filename and checks allowed extension.
    2. Enforces non-empty content and size limits.
    3. Performs deep magic-byte and structure inspection.
    4. Detects extension/content mismatches.
    5. Returns ValidatedFile with canonical MIME type.
    """
    original_filename = file.filename or "file.pdf"
    safe_name = sanitize_filename(original_filename)
    extension = Path(safe_name).suffix.lower()

    if not extension or extension not in allowed_extensions:
        formats = ", ".join(ext.upper().lstrip(".") for ext in sorted(allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{extension}'. Allowed formats: {formats}",
        )

    # Read content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(content) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb}MB",
        )

    # Detect content format
    detected_ext = _detect_content_type(content)

    # Extension vs Detected format check (Mismatch check)
    if extension == ".pdf":
        if detected_ext and detected_ext != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.pdf' does not match detected file content '{detected_ext}'.",
            )
        _validate_pdf(content)
    elif extension == ".docx":
        if detected_ext and detected_ext not in (".zip", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.docx' does not match detected file content '{detected_ext}'.",
            )
        _validate_docx(content)
    elif extension == ".doc":
        if detected_ext and detected_ext != ".doc":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.doc' does not match detected file content '{detected_ext}'.",
            )
        _validate_doc(content)
    elif extension == ".png":
        if detected_ext and detected_ext != ".png":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.png' does not match detected file content '{detected_ext}'.",
            )
        _validate_png(content)
    elif extension in (".jpg", ".jpeg"):
        if detected_ext and detected_ext != ".jpg":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{extension}' does not match detected file content.",
            )
        _validate_jpeg(content)
    elif extension == ".txt":
        if detected_ext is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.txt' contains binary data detected as '{detected_ext}'.",
            )
        _validate_txt(content)

    # Assign canonical MIME type
    canonical_mime = CANONICAL_MIME_TYPES.get(extension, "application/octet-stream")

    return ValidatedFile(
        content=content,
        mime_type=canonical_mime,
        original_filename=original_filename,
        safe_filename=safe_name,
        extension=extension,
        size_bytes=len(content),
    )
