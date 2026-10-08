"""
Storage backend abstraction.
Defines the interface that all storage implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract base class for file storage backends."""

    @abstractmethod
    async def put(self, key: str, file: BinaryIO, content_type: str) -> None:
        """
        Upload a file to storage.

        Args:
            key: Unique storage key (path)
            file: File-like object containing binary data
            content_type: MIME type of the file
        """
        pass

    @abstractmethod
    async def get_stream(self, key: str) -> BinaryIO:
        """
        Retrieve a file as a stream.

        Args:
            key: Storage key

        Returns:
            File-like object for streaming
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a file from storage.

        Args:
            key: Storage key
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists.

        Args:
            key: Storage key

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a time-limited signed URL for direct download.

        Args:
            key: Storage key
            expires_in: URL expiry time in seconds

        Returns:
            Signed URL string
        """
        pass
