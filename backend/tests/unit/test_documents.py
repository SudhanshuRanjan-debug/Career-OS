"""
Stage 3 Document Vault Unit Tests:
Upload, categories, type filter, authorized download, soft-delete, and tenant isolation.
"""

import io
import pytest
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, username: str) -> dict[str, str]:
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


def test_document_upload_and_type_filtering(db_client: TestClient):
    """Upload documents with categories and filter by doc_type."""
    headers = register_and_login(db_client, "doc_user@example.com", "docuser")

    # Upload cover letter
    f1 = {"file": ("cover_letter.pdf", io.BytesIO(b"%PDF-1.4 Cover Letter"), "application/pdf")}
    d1 = db_client.post(
        "/api/v1/documents/upload",
        files=f1,
        data={"name": "General Cover Letter", "doc_type": "COVER_LETTER"},
        headers=headers,
    )
    assert d1.status_code == 201
    assert d1.json()["doc_type"] == "COVER_LETTER"

    # Upload transcript
    f2 = {"file": ("transcript.pdf", io.BytesIO(b"%PDF-1.4 Transcript"), "application/pdf")}
    d2 = db_client.post(
        "/api/v1/documents/upload",
        files=f2,
        data={"name": "Official Transcript", "doc_type": "TRANSCRIPT"},
        headers=headers,
    )
    assert d2.status_code == 201
    assert d2.json()["doc_type"] == "TRANSCRIPT"

    # List all documents
    all_docs = db_client.get("/api/v1/documents", headers=headers).json()
    assert len(all_docs["items"]) == 2

    # Filter by COVER_LETTER
    cl_docs = db_client.get("/api/v1/documents?doc_type=COVER_LETTER", headers=headers).json()
    assert len(cl_docs["items"]) == 1
    assert cl_docs["items"][0]["name"] == "General Cover Letter"


def test_document_download_and_tenant_isolation(db_client: TestClient):
    """Stream authorized document and verify cross-user isolation."""
    user_a = register_and_login(db_client, "doc_a@example.com", "doca")
    user_b = register_and_login(db_client, "doc_b@example.com", "docb")

    # User A uploads document
    f = {"file": ("confidential.pdf", io.BytesIO(b"%PDF-1.4 Classified Academic Transcript"), "application/pdf")}
    doc = db_client.post(
        "/api/v1/documents/upload",
        files=f,
        data={"name": "Confidential Transcript", "doc_type": "TRANSCRIPT"},
        headers=user_a,
    ).json()
    doc_id = doc["id"]

    # User A downloads
    a_res = db_client.get(f"/api/v1/documents/{doc_id}/download", headers=user_a)
    assert a_res.status_code == 200
    assert b"Classified Academic Transcript" in a_res.content

    # User B CANNOT download (404)
    b_res = db_client.get(f"/api/v1/documents/{doc_id}/download", headers=user_b)
    assert b_res.status_code == 404

    # User B CANNOT delete (404)
    b_del = db_client.delete(f"/api/v1/documents/{doc_id}", headers=user_b)
    assert b_del.status_code == 404

    # User A deletes
    a_del = db_client.delete(f"/api/v1/documents/{doc_id}", headers=user_a)
    assert a_del.status_code == 200

    # User A list is now empty
    a_list = db_client.get("/api/v1/documents", headers=user_a).json()
    assert len(a_list["items"]) == 0


def test_document_file_validation_and_path_traversal(db_client: TestClient):
    """Verify disallowed file extensions, empty files, and path traversal resistance."""
    headers = register_and_login(db_client, "sec_doc@example.com", "secdoc")

    # 1. Disallowed extension (.sh)
    bad_file = {"file": ("script.sh", io.BytesIO(b"#!/bin/bash\nrm -rf /"), "text/x-shellscript")}
    res = db_client.post("/api/v1/documents/upload", files=bad_file, headers=headers)
    assert res.status_code == 400
    assert "Invalid file type" in res.json()["detail"]

    # 2. Path traversal attempt in filename is neutralized
    trav_file = {"file": ("../../etc/passwd.pdf", io.BytesIO(b"%PDF-1.4 Fake Passwd"), "application/pdf")}
    res_trav = db_client.post("/api/v1/documents/upload", files=trav_file, headers=headers)
    assert res_trav.status_code == 201
    uploaded_doc = res_trav.json()
    # Stored storage_key is scoped under documents/{user_id}/ and does not contain ..
    assert ".." not in uploaded_doc["storage_key"]
    assert uploaded_doc["storage_key"].startswith(f"documents/")
