"""
Amazon S3 storage backend for production and cloud deployments.
Integrates with AWS S3 using boto3's default credential chain (supporting EC2 IAM roles,
ECS task roles, and environment credentials without requiring static secrets).
"""

import asyncio
from typing import Any, BinaryIO
from .base import StorageBackend

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception  # type: ignore


class S3StorageBackend(StorageBackend):
    """
    Amazon S3 storage implementation following the StorageBackend interface.
    
    Authenticates automatically via the boto3 default credential provider chain:
    1. Environment variables
    2. Shared credentials file (~/.aws/credentials)
    3. AWS config file (~/.aws/config)
    4. ECS container credentials
    5. EC2 Instance Profile IAM role (IMDSv2)
    """

    def __init__(
        self,
        bucket_name: str,
        region_name: str | None = None,
        endpoint_url: str | None = None,
        client: Any | None = None,
    ):
        if not BOTO3_AVAILABLE and client is None:
            raise ImportError("boto3 is not installed. Run: pip install boto3")

        bucket = (bucket_name or "").strip()
        if not bucket:
            raise ValueError("S3 bucket name must be configured for S3StorageBackend")

        self.bucket_name = bucket
        self.region_name = region_name.strip() if region_name else None
        self.endpoint_url = endpoint_url.strip() if endpoint_url else None

        if client is not None:
            self.client = client
        else:
            client_kwargs: dict[str, Any] = {}
            if self.region_name:
                client_kwargs["region_name"] = self.region_name
            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url
            self.client = boto3.client("s3", **client_kwargs)

    async def put(self, key: str, file: BinaryIO | bytes, content_type: str) -> None:
        """
        Upload a file or stream to S3 bucket.
        """
        if hasattr(file, "read"):
            content = file.read()
            if hasattr(content, "__await__"):
                content = await content
        else:
            content = file

        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except ClientError as e:
            raise IOError(f"Failed to upload object to S3 ({key}): {e}") from e

    async def get_stream(self, key: str) -> BinaryIO:
        """
        Retrieve an S3 object as a readable stream.
        Raises FileNotFoundError if object does not exist.
        """
        try:
            response = await asyncio.to_thread(
                self.client.get_object,
                Bucket=self.bucket_name,
                Key=key,
            )
            return response["Body"]
        except ClientError as e:
            error_code = str(e.response.get("Error", {}).get("Code", ""))
            status_code = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if error_code in ("NoSuchKey", "404", "NotFound") or status_code == 404:
                raise FileNotFoundError(f"File not found: {key}") from e
            raise IOError(f"Failed to retrieve file from S3 ({key}): {e}") from e

    async def delete(self, key: str) -> None:
        """
        Delete an object from S3 bucket.
        """
        try:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=self.bucket_name,
                Key=key,
            )
        except ClientError as e:
            raise IOError(f"Failed to delete object from S3 ({key}): {e}") from e

    async def exists(self, key: str) -> bool:
        """
        Check if an object exists in S3 bucket using head_object.
        """
        try:
            await asyncio.to_thread(
                self.client.head_object,
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except ClientError as e:
            error_code = str(e.response.get("Error", {}).get("Code", ""))
            status_code = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if error_code in ("404", "NoSuchKey", "NotFound") or status_code == 404:
                return False
            raise IOError(f"Failed to check object existence in S3 ({key}): {e}") from e

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a time-limited presigned S3 download URL.
        """
        try:
            url = await asyncio.to_thread(
                self.client.generate_presigned_url,
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return str(url)
        except ClientError as e:
            raise IOError(f"Failed to generate presigned S3 URL ({key}): {e}") from e
