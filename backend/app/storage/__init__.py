"""
Storage backend factory.
Returns the appropriate storage backend based on configuration.
"""

from app.core.config import settings
from .base import StorageBackend
from .local_storage import LocalStorageBackend
from .azure_storage import AzureStorageBackend
from .s3_storage import S3StorageBackend

_storage_instance: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    """
    Get or create the storage backend singleton.
    Backend is determined by STORAGE_BACKEND setting.
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    backend_type = (settings.STORAGE_BACKEND or "local").strip().lower()

    if backend_type == "local":
        _storage_instance = LocalStorageBackend(base_path=settings.STORAGE_LOCAL_PATH)
    elif backend_type == "azure":
        _storage_instance = AzureStorageBackend(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container_name=settings.AZURE_STORAGE_CONTAINER
        )
    elif backend_type == "s3":
        _storage_instance = S3StorageBackend(
            bucket_name=settings.S3_BUCKET_NAME,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
        )
    else:
        raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")

    return _storage_instance


def reset_storage_backend() -> None:
    """Reset the singleton instance (primarily for test isolation)."""
    global _storage_instance
    _storage_instance = None


__all__ = ["StorageBackend", "get_storage_backend", "reset_storage_backend", "LocalStorageBackend", "AzureStorageBackend", "S3StorageBackend"]
