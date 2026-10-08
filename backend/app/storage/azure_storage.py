"""
Azure Blob Storage backend for production.
Files are stored in Azure Blob Storage with private access.
"""

from typing import BinaryIO
from datetime import datetime, timedelta
from .base import StorageBackend

# Azure SDK imports (installed in production only)
try:
    from azure.storage.blob.aio import BlobServiceClient
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureStorageBackend(StorageBackend):
    """Azure Blob Storage implementation."""

    def __init__(self, connection_string: str, container_name: str):
        if not AZURE_AVAILABLE:
            raise ImportError("azure-storage-blob not installed. Run: pip install azure-storage-blob")

        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = container_name

    async def put(self, key: str, file: BinaryIO, content_type: str) -> None:
        blob_client = self.client.get_blob_client(container=self.container, blob=key)

        # Read file content
        if hasattr(file, 'read'):
            content = await file.read() if hasattr(file.read, '__await__') else file.read()
        else:
            content = file

        await blob_client.upload_blob(
            content,
            overwrite=False,
            content_settings={"content_type": content_type}
        )

    async def get_stream(self, key: str) -> BinaryIO:
        blob_client = self.client.get_blob_client(container=self.container, blob=key)
        stream = await blob_client.download_blob()
        return stream

    async def delete(self, key: str) -> None:
        blob_client = self.client.get_blob_client(container=self.container, blob=key)
        await blob_client.delete_blob()

    async def exists(self, key: str) -> bool:
        blob_client = self.client.get_blob_client(container=self.container, blob=key)
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
