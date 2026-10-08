"""
Local filesystem storage backend for development.
Files are stored in a local directory.
"""

import aiofiles
from pathlib import Path
from typing import BinaryIO
from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation with path traversal protection."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, key: str) -> Path:
        """Resolve path and verify it remains strictly within base_path."""
        dest = (self.base_path / key).resolve()
        try:
            dest.relative_to(self.base_path)
        except ValueError:
            raise ValueError(f"Path traversal attempt detected: {key}")
        return dest

    async def put(self, key: str, file: BinaryIO, content_type: str) -> None:
        dest = self._resolve_safe_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Read file content
        if hasattr(file, 'read'):
            content = await file.read() if hasattr(file.read, '__await__') else file.read()
        else:
            content = file

        # Write to disk
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

    async def get_stream(self, key: str) -> BinaryIO:
        path = self._resolve_safe_path(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return open(path, "rb")

    async def delete(self, key: str) -> None:
        path = self._resolve_safe_path(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        path = self._resolve_safe_path(key)
        return path.exists()

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        # In local dev, return a local API route for serving the file
        # This is never used in production
        return f"/api/v1/storage/local/{key}"
