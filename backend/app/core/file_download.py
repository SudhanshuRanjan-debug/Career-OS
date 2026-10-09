"""
File download security: safe Content-Disposition headers, filename sanitization,
nosniff enforcement, and sandbox isolation headers for user-supplied file streams.
"""

import re
import urllib.parse
from pathlib import Path
from typing import BinaryIO, Optional
from fastapi.responses import StreamingResponse


def sanitize_download_filename(filename: Optional[str], default_name: str = "download.pdf") -> str:
    """
    Sanitize filename for HTTP Content-Disposition headers:
    1. Removes directory components to prevent path traversal.
    2. Strips quotes, semicolons, backslashes, and control characters (CRLF).
    3. Normalizes whitespace and returns a clean, safe filename.
    """
    if not filename:
        return default_name

    # Strip directory paths
    base_name = Path(filename).name

    # Remove CRLF, null bytes, quotes, semicolons, backslashes, and forward slashes
    safe = re.sub(r'[\r\n\t\x00"\\;/\\]', "_", base_name)

    # Remove non-printable / control characters
    safe = "".join(ch for ch in safe if ch.isprintable())

    # Collapse multiple spaces or underscores
    safe = re.sub(r"[ _]{2,}", "_", safe).strip(" ._")

    return safe or default_name


def create_secure_file_download_response(
    file_stream: BinaryIO,
    filename: str,
    media_type: str = "application/octet-stream",
) -> StreamingResponse:
    """
    Stream a file download with robust security headers:
    1. Content-Disposition: attachment (never inline execution in browser origin).
    2. X-Content-Type-Options: nosniff (prohibits MIME confusion).
    3. Content-Security-Policy: default-src 'none'; sandbox (prohibits active scripting).
    4. Cache-Control: private, no-cache, no-store, must-revalidate (prevents proxy caching).
    5. Clean, sanitized filename with RFC 5987 / RFC 6266 encoding.
    """
    clean_filename = sanitize_download_filename(filename)
    ascii_filename = re.sub(r"[^\w\.\-\_]", "_", clean_filename) or "download.pdf"
    encoded_filename = urllib.parse.quote(clean_filename)

    # Use standard attachment disposition with ASCII fallback and UTF-8 filename*
    content_disposition = (
        f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    )

    def iter_file():
        try:
            while chunk := file_stream.read(64 * 1024):
                yield chunk
        finally:
            if hasattr(file_stream, "close"):
                file_stream.close()

    headers = {
        "Content-Disposition": content_disposition,
        "Content-Type": media_type,
        "X-Content-Type-Options": "nosniff",
        "X-Download-Options": "noopen",
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "Cache-Control": "private, no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
    }

    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        headers=headers,
    )
