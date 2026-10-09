"""
Stage 3 Resumes Unit Tests:
Upload, validation, versioning, default toggle, download stream, soft-deletion, and tenant isolation.
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


def test_resume_upload_and_listing(db_client: TestClient):
    """Upload valid resume and list resumes."""
    headers = register_and_login(db_client, "resume_user@example.com", "resumeuser")

    # Upload PDF resume
    pdf_content = b"%PDF-1.4 Mock PDF Content For Resume"
    files = {"file": ("my_resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"name": "Full Stack Resume"}

    upload_res = db_client.post("/api/v1/resumes/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 201
    resume = upload_res.json()
    assert resume["name"] == "Full Stack Resume"
    assert resume["original_filename"] == "my_resume.pdf"
    assert resume["version"] == 1
    assert resume["is_default"] is True  # First resume is automatically default
    resume_id = resume["id"]

    # List resumes
    list_res = db_client.get("/api/v1/resumes", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == resume_id


def test_resume_version_increment(db_client: TestClient):
    """Uploading a new resume with the same name increments version."""
    headers = register_and_login(db_client, "version_user@example.com", "versionuser")

    # Version 1
    files1 = {"file": ("resume_v1.pdf", io.BytesIO(b"%PDF-1.4 Version 1"), "application/pdf")}
    res1 = db_client.post("/api/v1/resumes/upload", files=files1, data={"name": "Tech Resume"}, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["version"] == 1

    # Version 2 (same name)
    files2 = {"file": ("resume_v2.pdf", io.BytesIO(b"%PDF-1.4 Version 2"), "application/pdf")}
    res2 = db_client.post("/api/v1/resumes/upload", files=files2, data={"name": "Tech Resume"}, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["version"] == 2


def test_resume_file_validation(db_client: TestClient):
    """Reject invalid file extensions, empty files, and excessive sizes."""
    headers = register_and_login(db_client, "val_user@example.com", "valuser")

    # 1. Invalid extension (.exe)
    bad_file = {"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")}
    res = db_client.post("/api/v1/resumes/upload", files=bad_file, headers=headers)
    assert res.status_code == 400
    assert "Invalid file type" in res.json()["detail"]

    # 2. Empty file
    empty_file = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res = db_client.post("/api/v1/resumes/upload", files=empty_file, headers=headers)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

    # 3. Excessive file size (> 10MB)
    huge_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    huge_file = {"file": ("huge.pdf", io.BytesIO(huge_bytes), "application/pdf")}
    res = db_client.post("/api/v1/resumes/upload", files=huge_file, headers=headers)
    assert res.status_code == 413


def test_set_default_resume(db_client: TestClient):
    """Designate resume as default switches is_default across user resumes."""
    headers = register_and_login(db_client, "def_user@example.com", "defuser")

    # Upload resume 1 (becomes default)
    f1 = {"file": ("r1.pdf", io.BytesIO(b"%PDF-1.4 R1"), "application/pdf")}
    r1 = db_client.post("/api/v1/resumes/upload", files=f1, data={"name": "Resume 1"}, headers=headers).json()
    assert r1["is_default"] is True

    # Upload resume 2 (not default)
    f2 = {"file": ("r2.pdf", io.BytesIO(b"%PDF-1.4 R2"), "application/pdf")}
    r2 = db_client.post("/api/v1/resumes/upload", files=f2, data={"name": "Resume 2"}, headers=headers).json()
    assert r2["is_default"] is False

    # Switch default to resume 2
    switch_res = db_client.post(f"/api/v1/resumes/{r2['id']}/set-default", headers=headers)
    assert switch_res.status_code == 200
    assert switch_res.json()["is_default"] is True

    # Verify resume 1 is no longer default
    list_res = db_client.get("/api/v1/resumes", headers=headers).json()["items"]
    r1_updated = next(item for item in list_res if item["id"] == r1["id"])
    assert r1_updated["is_default"] is False


def test_resume_download_streaming_and_isolation(db_client: TestClient):
    """Stream authorized resume file and verify cross-user isolation."""
    user_a = register_and_login(db_client, "res_a@example.com", "resa")
    user_b = register_and_login(db_client, "res_b@example.com", "resb")

    # User A uploads resume
    f = {"file": ("doc_a.pdf", io.BytesIO(b"%PDF-1.4 User A Secret Resume"), "application/pdf")}
    r = db_client.post("/api/v1/resumes/upload", files=f, headers=user_a).json()
    resume_id = r["id"]

    # User A can download
    download_res = db_client.get(f"/api/v1/resumes/{resume_id}/download", headers=user_a)
    assert download_res.status_code == 200
    assert b"User A Secret Resume" in download_res.content
    assert download_res.headers["content-type"] == "application/pdf"
    assert "attachment" in download_res.headers["content-disposition"]
    assert download_res.headers["x-content-type-options"] == "nosniff"

    # User B CANNOT download User A's resume (404 / access denied)
    b_res = db_client.get(f"/api/v1/resumes/{resume_id}/download", headers=user_b)
    assert b_res.status_code == 404

    # Unauthenticated user CANNOT download
    unauth_res = db_client.get(f"/api/v1/resumes/{resume_id}/download")
    assert unauth_res.status_code == 401


def test_resume_soft_delete(db_client: TestClient):
    """Soft-delete resume preserves record for application history and removes from active list."""
    headers = register_and_login(db_client, "del_res@example.com", "delresuser")

    f = {"file": ("to_delete.pdf", io.BytesIO(b"%PDF-1.4 Delete Me"), "application/pdf")}
    r = db_client.post("/api/v1/resumes/upload", files=f, headers=headers).json()
    resume_id = r["id"]

    # Delete
    del_res = db_client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert del_res.status_code == 200

    # Active listing is empty
    list_res = db_client.get("/api/v1/resumes", headers=headers).json()
    assert len(list_res["items"]) == 0


import zipfile

def _make_valid_docx_bytes(text: str = "Candidate Experience") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
            '</Types>',
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f'  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>\n'
            '</w:document>',
        )
    return buf.getvalue()


def test_resume_upload_valid_docx(db_client: TestClient):
    """Legitimate DOCX file with valid Word OpenXML structure is accepted."""
    headers = register_and_login(db_client, "docx_cand@example.com", "docxcand")
    docx_bytes = _make_valid_docx_bytes("Senior Backend Engineer with FastAPI & Postgres")

    files = {"file": ("my_resume.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = db_client.post("/api/v1/resumes/upload", files=files, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["original_filename"] == "my_resume.docx"
    assert data["mime_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Download returns safe attachment headers
    dl_res = db_client.get(f"/api/v1/resumes/{data['id']}/download", headers=headers)
    assert dl_res.status_code == 200
    assert "attachment" in dl_res.headers["content-disposition"]
    assert dl_res.headers["x-content-type-options"] == "nosniff"
    assert dl_res.content == docx_bytes


def test_resume_upload_invalid_pdf_signature(db_client: TestClient):
    """Plain text or HTML disguised with a .pdf extension is rejected."""
    headers = register_and_login(db_client, "fake_pdf@example.com", "fakepdf")

    # Plain text disguised as PDF
    fake_file = {"file": ("resume.pdf", io.BytesIO(b"<html><body>Malicious HTML</body></html>"), "application/pdf")}
    res = db_client.post("/api/v1/resumes/upload", files=fake_file, headers=headers)
    assert res.status_code == 400
    assert "invalid pdf" in res.json()["detail"].lower()


def test_resume_upload_invalid_docx_structure(db_client: TestClient):
    """Zip archive missing Word document structures is rejected."""
    headers = register_and_login(db_client, "fake_docx@example.com", "fakedocx")

    # 1. Plain text disguised as docx
    res1 = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("fake.docx", io.BytesIO(b"not a zip file at all"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res1.status_code == 400
    assert "invalid docx" in res1.json()["detail"].lower()

    # 2. Valid zip but not a Word document (missing word/document.xml and [Content_Types].xml)
    dummy_zip = io.BytesIO()
    with zipfile.ZipFile(dummy_zip, "w") as z:
        z.writestr("test.txt", "just a text file")
    res2 = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("fake_structure.docx", io.BytesIO(dummy_zip.getvalue()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "invalid docx" in res2.json()["detail"].lower()


def test_resume_upload_extension_content_mismatch(db_client: TestClient):
    """Extension and detected content mismatch is rejected."""
    headers = register_and_login(db_client, "mismatch_user@example.com", "mismatchuser")

    # Valid PDF bytes sent with .docx extension
    pdf_bytes = b"%PDF-1.4 Mock PDF"
    res = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("mismatched.docx", io.BytesIO(pdf_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res.status_code == 400
    assert "does not match" in res.json()["detail"].lower()


def test_resume_download_sanitizes_filename(db_client: TestClient):
    """Download Content-Disposition sanitizes path traversal characters and quotes."""
    headers = register_and_login(db_client, "dl_sec@example.com", "dlsec")

    f = {"file": ("../../evil\r\n\"inject.pdf", io.BytesIO(b"%PDF-1.4 Clean Content"), "application/pdf")}
    upload_res = db_client.post("/api/v1/resumes/upload", files=f, headers=headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    dl_res = db_client.get(f"/api/v1/resumes/{resume_id}/download", headers=headers)
    assert dl_res.status_code == 200
    cd = dl_res.headers["content-disposition"]
    assert "attachment" in cd
    assert ".." not in cd
    assert "\r" not in cd
    assert "\n" not in cd
    assert dl_res.headers["x-content-type-options"] == "nosniff"
