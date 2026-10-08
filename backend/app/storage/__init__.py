"""
Storage backend factory.
Returns the appropriate storage backend based on configuration.
"""

from app.core.config import settings
from .base import StorageBackend
from .local_storage import LocalStorageBackend
from .azure_storage import AzureStorageBackend

_storage_instance: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    """
    Get or create the storage backend singleton.
    Backend is determined by STORAGE_BACKEND setting.
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    if settings.STORAGE_BACKEND == "local":
        _storage_instance = LocalStorageBackend(base_path=settings.STORAGE_LOCAL_PATH)
    elif settings.STORAGE_BACKEND == "azure":
        _storage_instance = AzureStorageBackend(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container_name=settings.AZURE_STORAGE_CONTAINER
        )
    else:
        raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")

    return _storage_instance


__all__ = ["StorageBackend", "get_storage_backend"]
