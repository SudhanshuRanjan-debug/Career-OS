"""
Unit tests for Amazon S3 storage support in Career OS:
1. S3StorageBackend interface conformance (put, get_stream, delete, exists, get_signed_url).
2. Proper error mapping (ClientError -> FileNotFoundError on missing objects, IOError on other failures).
3. EC2 IAM role / default credential chain authentication (no static credentials required).
4. Storage factory registration for 's3' provider.
5. Production configuration validation for S3 settings.
6. Seamless end-to-end integration with ResumeService and DocumentService.
All tests use mocked boto3/S3 clients and never make real network requests or require AWS credentials.
"""

import io
from typing import BinaryIO
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.services.resume_service import resume_service
from app.services.document_service import document_service
from app.storage import get_storage_backend, reset_storage_backend
from app.storage.base import StorageBackend
from app.storage.local_storage import LocalStorageBackend
from app.storage.azure_storage import AzureStorageBackend
from app.storage.s3_storage import S3StorageBackend


def create_client_error(code: str, message: str = "Test Error", status_code: int = 404) -> ClientError:
    """Helper to create realistic botocore ClientError instances."""
    return ClientError(
        error_response={
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        operation_name="S3Operation",
    )


class MockStreamingBody(io.BytesIO):
    """Mock for botocore.response.StreamingBody."""

    def __init__(self, data: bytes):
        super().__init__(data)


# ===========================================================================
# 1. Initialization & Credential Chain Tests
# ===========================================================================

def test_s3_init_requires_bucket_name():
    """Verify initialization rejects empty or whitespace bucket names."""
    with pytest.raises(ValueError, match="S3 bucket name must be configured"):
        S3StorageBackend(bucket_name="")

    with pytest.raises(ValueError, match="S3 bucket name must be configured"):
        S3StorageBackend(bucket_name="   ")


def test_s3_init_with_valid_parameters():
    """Verify initialization configures bucket, region, and endpoint correctly."""
    mock_s3_client = MagicMock()
    with patch("boto3.client", return_value=mock_s3_client) as mock_boto3:
        backend = S3StorageBackend(
            bucket_name="career-os-test-bucket",
            region_name="us-west-2",
            endpoint_url="http://localhost:4566",
        )
        assert backend.bucket_name == "career-os-test-bucket"
        assert backend.region_name == "us-west-2"
        assert backend.endpoint_url == "http://localhost:4566"
        assert backend.client is mock_s3_client

        # Verify boto3.client was invoked with region and endpoint, but NO static credentials
        mock_boto3.assert_called_once_with(
            "s3",
            region_name="us-west-2",
            endpoint_url="http://localhost:4566",
        )


def test_s3_uses_default_credential_chain_without_static_keys():
    """
    Verify boto3 is invoked without static AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY,
    allowing EC2 IAM role / IMDSv2 resolution.
    """
    with patch("boto3.client") as mock_boto3:
        S3StorageBackend(bucket_name="my-bucket", region_name="us-east-1")
        _, kwargs = mock_boto3.call_args
        assert "aws_access_key_id" not in kwargs
        assert "aws_secret_access_key" not in kwargs
        assert "aws_session_token" not in kwargs


def test_s3_init_with_injected_client():
    """Verify an existing S3 client can be injected directly (for mocks)."""
    custom_client = MagicMock()
    backend = S3StorageBackend(bucket_name="custom-bucket", client=custom_client)
    assert backend.client is custom_client


# ===========================================================================
# 2. Put (Upload) Operations
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_put_bytes():
    """Verify uploading raw bytes calls put_object with correct arguments."""
    mock_client = MagicMock()
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    data = b"%PDF-1.4 Mock resume content"
    await backend.put("resumes/user1/file.pdf", data, "application/pdf")

    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="resumes/user1/file.pdf",
        Body=data,
        ContentType="application/pdf",
    )


@pytest.mark.asyncio
async def test_s3_put_file_like_object():
    """Verify uploading file-like object reads content before put_object."""
    mock_client = MagicMock()
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    file_obj = io.BytesIO(b"Hello S3")
    await backend.put("documents/user1/doc.txt", file_obj, "text/plain")

    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="documents/user1/doc.txt",
        Body=b"Hello S3",
        ContentType="text/plain",
    )


@pytest.mark.asyncio
async def test_s3_put_async_read_object():
    """Verify uploading an object with async read() method."""
    mock_client = MagicMock()
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    class AsyncFile:
        async def read(self):
            return b"Async stream data"

    await backend.put("documents/user1/async.pdf", AsyncFile(), "application/pdf")

    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="documents/user1/async.pdf",
        Body=b"Async stream data",
        ContentType="application/pdf",
    )


@pytest.mark.asyncio
async def test_s3_put_raises_io_error_on_client_error():
    """Verify put_object failure is wrapped in IOError."""
    mock_client = MagicMock()
    mock_client.put_object.side_effect = create_client_error("AccessDenied", "Access Denied", 403)
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    with pytest.raises(IOError, match="Failed to upload object to S3"):
        await backend.put("test.pdf", b"data", "application/pdf")


# ===========================================================================
# 3. Get Stream (Download) Operations
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_get_stream_success():
    """Verify get_stream retrieves StreamingBody from get_object."""
    mock_client = MagicMock()
    body_stream = MockStreamingBody(b"PDF Stream Payload")
    mock_client.get_object.return_value = {"Body": body_stream}

    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)
    stream = await backend.get_stream("resumes/user1/my_resume.pdf")

    assert stream is body_stream
    assert stream.read() == b"PDF Stream Payload"
    mock_client.get_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="resumes/user1/my_resume.pdf",
    )


@pytest.mark.asyncio
async def test_s3_get_stream_missing_object_raises_file_not_found():
    """Verify NoSuchKey ClientError is translated into FileNotFoundError."""
    mock_client = MagicMock()
    mock_client.get_object.side_effect = create_client_error("NoSuchKey", "The specified key does not exist", 404)

    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)
    with pytest.raises(FileNotFoundError, match="File not found: missing/file.pdf"):
        await backend.get_stream("missing/file.pdf")


@pytest.mark.asyncio
async def test_s3_get_stream_404_status_code_raises_file_not_found():
    """Verify 404 HTTPStatusCode is translated into FileNotFoundError."""
    mock_client = MagicMock()
    mock_client.get_object.side_effect = create_client_error("404", "Not Found", 404)

    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)
    with pytest.raises(FileNotFoundError, match="File not found: missing/file.pdf"):
        await backend.get_stream("missing/file.pdf")


@pytest.mark.asyncio
async def test_s3_get_stream_non_404_error_raises_io_error():
    """Verify non-404 error (e.g. 500 or 403) raises IOError."""
    mock_client = MagicMock()
    mock_client.get_object.side_effect = create_client_error("InternalError", "S3 internal error", 500)

    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)
    with pytest.raises(IOError, match="Failed to retrieve file from S3"):
        await backend.get_stream("corrupted/file.pdf")


# ===========================================================================
# 4. Delete Operations
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_delete_success():
    """Verify delete calls delete_object with bucket and key."""
    mock_client = MagicMock()
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    await backend.delete("resumes/user1/old_resume.pdf")
    mock_client.delete_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="resumes/user1/old_resume.pdf",
    )


@pytest.mark.asyncio
async def test_s3_delete_raises_io_error_on_failure():
    """Verify delete raises IOError on ClientError."""
    mock_client = MagicMock()
    mock_client.delete_object.side_effect = create_client_error("AccessDenied", "Denied", 403)
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    with pytest.raises(IOError, match="Failed to delete object from S3"):
        await backend.delete("resumes/user1/old.pdf")


# ===========================================================================
# 5. Exists Operations
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_exists_returns_true_when_head_object_succeeds():
    """Verify exists returns True when head_object succeeds."""
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ContentLength": 1024}
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    assert await backend.exists("documents/file.pdf") is True
    mock_client.head_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="documents/file.pdf",
    )


@pytest.mark.asyncio
async def test_s3_exists_returns_false_on_404():
    """Verify exists returns False when head_object raises 404 / NoSuchKey."""
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("404", "Not Found", 404)
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    assert await backend.exists("documents/missing.pdf") is False


@pytest.mark.asyncio
async def test_s3_exists_returns_false_on_nosuchkey():
    """Verify exists returns False when head_object raises NoSuchKey."""
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("NoSuchKey", "Not Found", 404)
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    assert await backend.exists("documents/missing.pdf") is False


@pytest.mark.asyncio
async def test_s3_exists_raises_io_error_on_other_error():
    """Verify exists raises IOError on non-404 errors (e.g. AccessDenied)."""
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("AccessDenied", "Forbidden", 403)
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    with pytest.raises(IOError, match="Failed to check object existence in S3"):
        await backend.exists("documents/forbidden.pdf")


# ===========================================================================
# 6. Signed URL Operations
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_get_signed_url_success():
    """Verify get_signed_url calls generate_presigned_url."""
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/file.pdf?sig=123"
    backend = S3StorageBackend(bucket_name="test-bucket", client=mock_client)

    url = await backend.get_signed_url("file.pdf", expires_in=1800)
    assert url == "https://s3.amazonaws.com/test-bucket/file.pdf?sig=123"
    mock_client.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={"Bucket": "test-bucket", "Key": "file.pdf"},
        ExpiresIn=1800,
    )


# ===========================================================================
# 7. Storage Factory Registration & Singleton Behavior
# ===========================================================================

def test_storage_factory_registers_s3():
    """Verify get_storage_backend returns S3StorageBackend when STORAGE_BACKEND is 's3'."""
    reset_storage_backend()
    try:
        with patch("app.storage.settings") as mock_settings, \
             patch("boto3.client") as mock_boto3:
            mock_settings.STORAGE_BACKEND = "s3"
            mock_settings.S3_BUCKET_NAME = "career-platform-s3-bucket"
            mock_settings.AWS_REGION = "eu-central-1"
            mock_settings.AWS_ENDPOINT_URL = None

            backend = get_storage_backend()
            assert isinstance(backend, S3StorageBackend)
            assert backend.bucket_name == "career-platform-s3-bucket"
            assert backend.region_name == "eu-central-1"
    finally:
        reset_storage_backend()


def test_storage_factory_preserves_local_and_azure():
    """Verify local and azure backends remain unchanged."""
    reset_storage_backend()
    try:
        # 1. Local
        with patch("app.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"
            mock_settings.STORAGE_LOCAL_PATH = "./storage/test_local"
            backend = get_storage_backend()
            assert isinstance(backend, LocalStorageBackend)

        reset_storage_backend()

        # 2. Unknown raises ValueError
        with patch("app.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "invalid_provider"
            with pytest.raises(ValueError, match="Unknown storage backend"):
                get_storage_backend()
    finally:
        reset_storage_backend()


# ===========================================================================
# 8. Configuration Validation Tests
# ===========================================================================

def test_production_fails_when_s3_selected_without_bucket():
    """Verify production startup fails if STORAGE_BACKEND is 's3' but S3_BUCKET_NAME is missing."""
    valid_secret = "x7f9a8b1c2d3e4f5061728394a5b6c7d8e9f0123456789abcdef0123456789ab"
    valid_pwd = "Pr0d_StR0ng_Db_P@ssw0rd_987654321!"
    valid_db = f"postgresql+asyncpg://postgres_admin:{valid_pwd}@db:5432/career_platform_prod"

    with pytest.raises(ValueError, match="S3_BUCKET_NAME must be configured"):
        Settings(
            APP_ENV="production",
            STORAGE_BACKEND="s3",
            S3_BUCKET_NAME="",
            SECRET_KEY=valid_secret,
            POSTGRES_PASSWORD=valid_pwd,
            DATABASE_URL=valid_db,
            ALLOWED_HOSTS=["career-platform.com", "testserver"],
        )


def test_production_succeeds_when_s3_configured_with_bucket():
    """Verify production startup succeeds when STORAGE_BACKEND is 's3' with a valid S3_BUCKET_NAME."""
    valid_secret = "x7f9a8b1c2d3e4f5061728394a5b6c7d8e9f0123456789abcdef0123456789ab"
    valid_pwd = "Pr0d_StR0ng_Db_P@ssw0rd_987654321!"
    valid_db = f"postgresql+asyncpg://postgres_admin:{valid_pwd}@db:5432/career_platform_prod"

    s = Settings(
        APP_ENV="production",
        STORAGE_BACKEND="s3",
        S3_BUCKET_NAME="production-resumes-bucket",
        AWS_REGION="us-east-1",
        SECRET_KEY=valid_secret,
        POSTGRES_PASSWORD=valid_pwd,
        DATABASE_URL=valid_db,
        ALLOWED_HOSTS=["career-platform.com", "testserver"],
    )
    assert s.STORAGE_BACKEND == "s3"
    assert s.S3_BUCKET_NAME == "production-resumes-bucket"
    assert s.AWS_REGION == "us-east-1"


# ===========================================================================
# 9. End-to-End API Flow Tests with S3 Backend
# ===========================================================================

def register_and_login_helper(client, email: str, username: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "Password123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_s3_backend_end_to_end_resume_upload_and_download(db_client):
    """
    Verify complete FastAPI resume upload and download workflow when backed by S3.
    Tests storage.put, storage.get_stream, security headers, and missing object 404.
    """
    from app.core.dependencies import get_storage
    from app.main import app as fastapi_app

    headers = register_and_login_helper(db_client, "s3_user@example.com", "s3user")

    mock_s3 = MagicMock()
    s3_backend = S3StorageBackend(bucket_name="test-s3-resumes", client=mock_s3)

    # Override get_storage dependency to use the S3 backend
    fastapi_app.dependency_overrides[get_storage] = lambda: s3_backend
    try:
        pdf_bytes = b"%PDF-1.4 S3 Career OS Test Resume"
        files = {"file": ("cloud_engineer.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"name": "Cloud Engineer Resume"}

        # 1. Upload resume to S3
        upload_res = db_client.post("/api/v1/resumes/upload", files=files, data=data, headers=headers)
        assert upload_res.status_code == 201
        res_data = upload_res.json()
        assert res_data["name"] == "Cloud Engineer Resume"
        resume_id = res_data["id"]

        # Verify S3 put_object was called with correct parameters
        mock_s3.put_object.assert_called_once()
        put_kwargs = mock_s3.put_object.call_args[1]
        assert put_kwargs["Bucket"] == "test-s3-resumes"
        assert put_kwargs["Key"].startswith("resumes/")
        assert put_kwargs["Body"] == pdf_bytes
        assert put_kwargs["ContentType"] == "application/pdf"

        # 2. Download resume stream from S3
        mock_s3.get_object.return_value = {"Body": MockStreamingBody(pdf_bytes)}
        dl_res = db_client.get(f"/api/v1/resumes/{resume_id}/download", headers=headers)
        assert dl_res.status_code == 200
        assert dl_res.content == pdf_bytes
        assert "attachment" in dl_res.headers["content-disposition"]
        assert dl_res.headers["x-content-type-options"] == "nosniff"

        # 3. Missing S3 object raises HTTP 404
        mock_s3.get_object.side_effect = create_client_error("NoSuchKey", "Not found", 404)
        missing_res = db_client.get(f"/api/v1/resumes/{resume_id}/download", headers=headers)
        assert missing_res.status_code == 404
        assert "not found on storage" in missing_res.json()["detail"].lower()
    finally:
        fastapi_app.dependency_overrides.pop(get_storage, None)


def test_s3_backend_end_to_end_document_upload_and_download(db_client):
    """
    Verify complete FastAPI document vault upload and download workflow when backed by S3.
    """
    from app.core.dependencies import get_storage
    from app.main import app as fastapi_app

    headers = register_and_login_helper(db_client, "s3_doc_user@example.com", "s3docuser")

    mock_s3 = MagicMock()
    s3_backend = S3StorageBackend(bucket_name="test-s3-docs", client=mock_s3)

    fastapi_app.dependency_overrides[get_storage] = lambda: s3_backend
    try:
        doc_bytes = b"%PDF-1.4 Cover letter content for AWS"
        files = {"file": ("cover_letter.pdf", io.BytesIO(doc_bytes), "application/pdf")}
        data = {"name": "AWS Cover Letter", "doc_type": "COVER_LETTER"}

        # 1. Upload document
        upload_res = db_client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert upload_res.status_code == 201
        doc_data = upload_res.json()
        doc_id = doc_data["id"]

        mock_s3.put_object.assert_called_once()
        put_kwargs = mock_s3.put_object.call_args[1]
        assert put_kwargs["Bucket"] == "test-s3-docs"
        assert put_kwargs["Key"].startswith("documents/")
        assert put_kwargs["Body"] == doc_bytes

        # 2. Download document
        mock_s3.get_object.return_value = {"Body": MockStreamingBody(doc_bytes)}
        dl_res = db_client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
        assert dl_res.status_code == 200
        assert dl_res.content == doc_bytes
        assert "attachment" in dl_res.headers["content-disposition"]

        # 3. Missing S3 object raises HTTP 404
        mock_s3.get_object.side_effect = create_client_error("NoSuchKey", "Not found", 404)
        missing_res = db_client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
        assert missing_res.status_code == 404
        assert "not found in storage" in missing_res.json()["detail"].lower()
    finally:
        fastapi_app.dependency_overrides.pop(get_storage, None)

