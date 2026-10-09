"""
Unit & Integration Tests for Two-Sided Platform Capabilities:
1. Hirer Registration & Organization Auto-Provisioning
2. Role-Based Access Control (Candidate vs Hirer)
3. Recruiter Organization Profile Management
4. Job Posting Lifecycle (Draft, Publish, Close, Archive)
5. Public & Candidate Job Discovery with Filtering
6. Candidate Save-to-Opportunities & Apply Flow
7. Candidate Data Privacy & Scoped Recruiter Applicant Review
8. Recruiter Stage Progression & Resume Streaming
9. Multi-Hirer Strict Tenant Isolation (Cross-Hirer 404)
10. Recruiter Analytics Metrics
"""

import io
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    email: str,
    username: str,
    role: str = "CANDIDATE",
    organization_name: str = None,
    password: str = "Password123!",
) -> dict:
    """Helper to register a user and return response JSON."""
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "role": role,
    }
    if organization_name:
        payload["organization_name"] = organization_name
    return client.post("/api/v1/auth/register", json=payload)


def auth_headers(
    client: TestClient,
    email: str,
    password: str = "Password123!",
) -> dict[str, str]:
    """Helper to login and return Bearer auth headers."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Hirer Registration & Role Enforcement
# ===========================================================================

def test_hirer_registration_and_org_auto_provisioning(db_client: TestClient):
    """Hirer registration must automatically create Organization with slug and return HIRER role."""
    res = register_user(
        db_client,
        email="recruiter1@acme.com",
        username="acme_recruiter",
        role="HIRER",
        organization_name="Acme Corporation",
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "HIRER"
    assert "access_token" in data

    headers = {"Authorization": f"Bearer {data['access_token']}"}

    # Verify organization profile was provisioned
    org_res = db_client.get("/api/v1/recruiter/organization", headers=headers)
    assert org_res.status_code == 200
    org_data = org_res.json()
    assert org_data["name"] == "Acme Corporation"
    assert org_data["slug"] == "acme-corporation"


def test_hirer_registration_missing_org_fails(db_client: TestClient):
    """Registering with role HIRER without organization_name must fail with 400 Bad Request."""
    res = register_user(
        db_client,
        email="no_org@recruiter.com",
        username="no_org_recruiter",
        role="HIRER",
        organization_name=None,
    )
    assert res.status_code == 400


def test_role_enforcement_candidate_cannot_access_recruiter_endpoints(db_client: TestClient):
    """Candidates must be forbidden (403) from accessing recruiter endpoints."""
    register_user(db_client, email="candidate@user.com", username="cand_user", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "candidate@user.com")

    # Attempt to access recruiter organization
    res1 = db_client.get("/api/v1/recruiter/organization", headers=cand_headers)
    assert res1.status_code == 403

    # Attempt to list recruiter jobs
    res2 = db_client.get("/api/v1/recruiter/jobs", headers=cand_headers)
    assert res2.status_code == 403

    # Attempt to create job posting
    res3 = db_client.post(
        "/api/v1/recruiter/jobs",
        json={"title": "Unauthorized Job", "description": "Desc"},
        headers=cand_headers,
    )
    assert res3.status_code == 403


def test_role_enforcement_hirer_cannot_apply_or_save(db_client: TestClient):
    """Hirers must be forbidden (403) from applying to jobs or saving opportunities."""
    register_user(
        db_client,
        email="hirer@company.com",
        username="hirer_user",
        role="HIRER",
        organization_name="Tech Recruiter",
    )
    hirer_headers = auth_headers(db_client, "hirer@company.com")
    fake_job_id = str(uuid4())

    # Attempt to apply
    apply_res = db_client.post(
        f"/api/v1/jobs/{fake_job_id}/apply",
        json={"resume_id": str(uuid4())},
        headers=hirer_headers,
    )
    assert apply_res.status_code == 403

    # Attempt to save to opportunities
    save_res = db_client.post(
        f"/api/v1/jobs/{fake_job_id}/save",
        headers=hirer_headers,
    )
    assert save_res.status_code == 403


# ===========================================================================
# 2. Recruiter Organization Profile Management
# ===========================================================================

def test_recruiter_organization_profile_update(db_client: TestClient):
    """Recruiter can update organization details."""
    register_user(
        db_client,
        email="admin@startup.io",
        username="startup_admin",
        role="HIRER",
        organization_name="Startup IO",
    )
    headers = auth_headers(db_client, "admin@startup.io")

    patch_payload = {
        "description": "Next-generation developer productivity platform.",
        "website": "https://startup.io",
        "location": "Bengaluru, India",
        "size": "STARTUP",
        "industry": "Developer Tools",
    }
    update_res = db_client.patch(
        "/api/v1/recruiter/organization",
        json=patch_payload,
        headers=headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["description"] == patch_payload["description"]
    assert data["website"] == patch_payload["website"]
    assert data["location"] == patch_payload["location"]
    assert data["size"] == "STARTUP"
    assert data["industry"] == "Developer Tools"


# ===========================================================================
# 3. Job Posting Lifecycle (Draft, Update, Publish, Close, Archive)
# ===========================================================================

def test_job_posting_lifecycle(db_client: TestClient):
    """Full lifecycle: Create Draft -> Update -> Publish -> Close -> Archive."""
    register_user(
        db_client,
        email="talent@acme.com",
        username="acme_talent",
        role="HIRER",
        organization_name="Acme Engineering",
    )
    headers = auth_headers(db_client, "talent@acme.com")

    # 1. Create Draft Job
    job_payload = {
        "title": "Senior Backend Engineer",
        "description": "We are seeking a seasoned Python backend engineer.",
        "location": "Bengaluru, Karnataka",
        "location_type": "HYBRID",
        "employment_type": "FULL_TIME",
        "experience_level": "SENIOR",
        "compensation_min": 2500000,
        "compensation_max": 3500000,
        "compensation_currency": "INR",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
    }
    create_res = db_client.post("/api/v1/recruiter/jobs", json=job_payload, headers=headers)
    assert create_res.status_code == 201
    job = create_res.json()
    job_id = job["id"]
    assert job["title"] == "Senior Backend Engineer"
    assert job["status"] == "DRAFT"
    assert job["compensation_currency"] == "INR"
    assert len(job["skills"]) == 3

    # 2. Update Draft Job
    patch_res = db_client.patch(
        f"/api/v1/recruiter/jobs/{job_id}",
        json={"title": "Staff Backend Engineer", "compensation_max": 4000000},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Staff Backend Engineer"
    assert float(patch_res.json()["compensation_max"]) == 4000000.0

    # 3. Publish Job
    pub_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/publish", headers=headers)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "PUBLISHED"
    assert pub_data["published_at"] is not None

    # 4. Close Job
    close_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # 5. Archive Job
    arch_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"


# ===========================================================================
# 4. Public Job Discovery & Filtering
# ===========================================================================

def test_public_job_discovery(db_client: TestClient):
    """Only PUBLISHED jobs should appear in public search; filtering by keyword and workplace type."""
    register_user(
        db_client,
        email="recruiter_discovery@corp.com",
        username="discovery_recruiter",
        role="HIRER",
        organization_name="Discovery Corp",
    )
    headers = auth_headers(db_client, "recruiter_discovery@corp.com")

    # Create & Publish Job A (Remote, Full-time, Python)
    res_a = db_client.post(
        "/api/v1/recruiter/jobs",
        json={
            "title": "Remote Python Developer",
            "description": "Build high throughput microservices in Python.",
            "location": "Remote",
            "location_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "experience_level": "MID",
            "skills": ["Python"],
        },
        headers=headers,
    )
    assert res_a.status_code == 201
    job_a_id = res_a.json()["id"]
    db_client.post(f"/api/v1/recruiter/jobs/{job_a_id}/publish", headers=headers)

    # Create & Publish Job B (On-site, Mumbai, React)
    res_b = db_client.post(
        "/api/v1/recruiter/jobs",
        json={
            "title": "Frontend React Specialist",
            "description": "Design sleek modern web interfaces.",
            "location": "Mumbai, Maharashtra",
            "location_type": "ON_SITE",
            "employment_type": "FULL_TIME",
            "experience_level": "SENIOR",
            "skills": ["React"],
        },
        headers=headers,
    )
    assert res_b.status_code == 201
    job_b_id = res_b.json()["id"]
    db_client.post(f"/api/v1/recruiter/jobs/{job_b_id}/publish", headers=headers)

    # Create Job C (Leave as DRAFT)
    res_c = db_client.post(
        "/api/v1/recruiter/jobs",
        json={"title": "Draft Secret Role", "description": "Unpublished"},
        headers=headers,
    )
    assert res_c.status_code == 201
    job_c_id = res_c.json()["id"]

    # Candidate or public searches jobs
    search_all = db_client.get("/api/v1/jobs")
    assert search_all.status_code == 200
    items = search_all.json()["items"]
    item_ids = [j["id"] for j in items]
    assert job_a_id in item_ids
    assert job_b_id in item_ids
    assert job_c_id not in item_ids  # DRAFT must never appear

    # Filter by keyword
    search_kw = db_client.get("/api/v1/jobs?search=Frontend")
    assert search_kw.status_code == 200
    kw_items = search_kw.json()["items"]
    assert len(kw_items) == 1
    assert kw_items[0]["id"] == job_b_id

    # Filter by location_type
    search_remote = db_client.get("/api/v1/jobs?location_type=REMOTE")
    assert search_remote.status_code == 200
    remote_items = search_remote.json()["items"]
    assert len(remote_items) == 1
    assert remote_items[0]["id"] == job_a_id

    # View Job Details
    detail_res = db_client.get(f"/api/v1/jobs/{job_a_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["title"] == "Remote Python Developer"
    assert detail["organization_name"] == "Discovery Corp"


# ===========================================================================
# 5. Candidate Application & Data Privacy Isolation
# ===========================================================================

def test_candidate_apply_and_recruiter_applicant_review(db_client: TestClient):
    """
    Test end-to-end flow:
    1. Recruiter publishes job
    2. Candidate uploads resume and applies
    3. Recruiter views scoped applicant review
    4. Recruiter advances applicant stage
    5. Privacy boundary: recruiter has no access to candidate private vault
    """
    # 1. Recruiter creates and publishes job
    register_user(
        db_client,
        email="recruiter_privacy@company.com",
        username="recruiter_priv",
        role="HIRER",
        organization_name="SecureTech",
    )
    recruiter_headers = auth_headers(db_client, "recruiter_privacy@company.com")

    job_res = db_client.post(
        "/api/v1/recruiter/jobs",
        json={"title": "Cloud Architect", "description": "Lead multi-region AWS cloud infrastructure."},
        headers=recruiter_headers,
    )
    job_id = job_res.json()["id"]
    db_client.post(f"/api/v1/recruiter/jobs/{job_id}/publish", headers=recruiter_headers)

    # 2. Candidate registers and uploads resume
    register_user(
        db_client,
        email="applicant_candidate@example.com",
        username="applicant_cand",
        role="CANDIDATE",
    )
    cand_headers = auth_headers(db_client, "applicant_candidate@example.com")

    # Set candidate profile details
    db_client.put(
        "/api/v1/profile/personal",
        json={
            "first_name": "Arjun",
            "last_name": "Sharma",
            "headline": "Senior Cloud Infrastructure Engineer",
            "location_city": "Bengaluru",
            "location_country": "India",
            "phone": "+91 98765 43210",
        },
        headers=cand_headers,
    )

    # Upload resume
    pdf_content = b"%PDF-1.5 Verified Candidate Resume For Testing"
    files = {"file": ("cloud_resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"name": "Cloud Infra Resume"}
    upload_res = db_client.post("/api/v1/resumes/upload", files=files, data=data, headers=cand_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 3. Candidate applies to the job
    apply_res = db_client.post(
        f"/api/v1/jobs/{job_id}/apply",
        json={
            "resume_id": resume_id,
            "notes": "Passionate about building resilient, automated cloud environments.",
        },
        headers=cand_headers,
    )
    assert apply_res.status_code == 201
    app_data = apply_res.json()
    application_id = app_data["id"]
    assert app_data["job_posting_id"] == job_id
    assert app_data["current_stage"] == "APPLIED"

    # 4. Duplicate application must fail with 409
    dup_apply = db_client.post(
        f"/api/v1/jobs/{job_id}/apply",
        json={"resume_id": resume_id},
        headers=cand_headers,
    )
    assert dup_apply.status_code == 409

    # 5. Recruiter lists applicants for the job
    applicants_res = db_client.get(f"/api/v1/recruiter/jobs/{job_id}/applicants", headers=recruiter_headers)
    assert applicants_res.status_code == 200
    applicant_list = applicants_res.json()["items"]
    assert len(applicant_list) == 1
    applicant = applicant_list[0]
    assert applicant["application_id"] == application_id
    assert applicant["candidate"]["full_name"] == "Arjun Sharma"
    assert applicant["candidate"]["email"] == "applicant_candidate@example.com"
    assert applicant["resume_filename"] == "cloud_resume.pdf"
    assert applicant["current_stage"] == "APPLIED"

    # 6. Recruiter gets applicant detail
    detail_res = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{application_id}",
        headers=recruiter_headers,
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["candidate"]["headline"] == "Senior Cloud Infrastructure Engineer"
    assert detail["cover_notes"] == "Passionate about building resilient, automated cloud environments."

    # 7. Recruiter advances applicant stage to INTERVIEW
    stage_res = db_client.post(
        f"/api/v1/recruiter/jobs/applications/{application_id}/stage",
        json={"to_stage": "INTERVIEW", "notes": "Impressive cloud profile, moving to tech interview."},
        headers=recruiter_headers,
    )
    assert stage_res.status_code == 200
    assert stage_res.json()["current_stage"] == "INTERVIEW"

    # Candidate sees their application stage updated
    cand_app = db_client.get(f"/api/v1/applications/{application_id}", headers=cand_headers)
    assert cand_app.status_code == 200
    assert cand_app.json()["current_stage"] == "INTERVIEW"

    # 8. Recruiter downloads applicant resume
    resume_stream = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{application_id}/resume",
        headers=recruiter_headers,
    )
    assert resume_stream.status_code == 200
    assert resume_stream.content == pdf_content


# ===========================================================================
# 6. Multi-Hirer Strict Tenant Isolation (Cross-Hirer 404)
# ===========================================================================

def test_cross_hirer_tenant_isolation(db_client: TestClient):
    """Hirer B cannot view, edit, or access Hirer A's job postings or applicants (404 Not Found)."""
    # Hirer A setup
    register_user(db_client, email="hirer_a@corp.com", username="hirer_a", role="HIRER", organization_name="Alpha Corp")
    headers_a = auth_headers(db_client, "hirer_a@corp.com")

    # Hirer B setup
    register_user(db_client, email="hirer_b@corp.com", username="hirer_b", role="HIRER", organization_name="Beta Corp")
    headers_b = auth_headers(db_client, "hirer_b@corp.com")

    # Hirer A posts a job
    job_res = db_client.post(
        "/api/v1/recruiter/jobs",
        json={"title": "Alpha Confidential Job", "description": "Secret project."},
        headers=headers_a,
    )
    job_a_id = job_res.json()["id"]

    # Hirer B attempts to access Hirer A's job -> 404
    assert db_client.get(f"/api/v1/recruiter/jobs/{job_a_id}", headers=headers_b).status_code == 404

    # Hirer B attempts to update Hirer A's job -> 404
    assert db_client.patch(
        f"/api/v1/recruiter/jobs/{job_a_id}",
        json={"title": "Hacked Title"},
        headers=headers_b,
    ).status_code == 404

    # Hirer B attempts to publish Hirer A's job -> 404
    assert db_client.post(f"/api/v1/recruiter/jobs/{job_a_id}/publish", headers=headers_b).status_code == 404

    # Hirer B attempts to list applicants for Hirer A's job -> 404
    assert db_client.get(f"/api/v1/recruiter/jobs/{job_a_id}/applicants", headers=headers_b).status_code == 404


def test_recruiter_resume_download_authorization_and_isolation(db_client: TestClient):
    """
    Verify recruiter resume endpoint authorization controls:
    1. Unauthenticated requests return 401 Unauthorized ("Authentication credentials were not provided").
    2. Candidate user tokens return 403 Forbidden (requires HIRER role).
    3. Cross-tenant recruiter tokens from a different organization return 404 Not Found.
    4. Non-existent application IDs return 404 Not Found.
    5. Authorized recruiter of the hiring organization successfully downloads the resume with 200 OK,
       correct Content-Disposition (filename and attachment), MIME type, and nosniff security header.
    """
    # 1. Register Hirer Org Alpha
    register_user(db_client, email="alpha_recruiter@corp.com", username="alpha_rec", role="HIRER", organization_name="Alpha Tech")
    alpha_headers = auth_headers(db_client, "alpha_recruiter@corp.com")

    # 2. Register Hirer Org Beta
    register_user(db_client, email="beta_recruiter@corp.com", username="beta_rec", role="HIRER", organization_name="Beta Tech")
    beta_headers = auth_headers(db_client, "beta_recruiter@corp.com")

    # 3. Register Candidate
    register_user(db_client, email="resume_cand@domain.com", username="res_cand", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "resume_cand@domain.com")

    # 4. Alpha posts and publishes a job
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Staff Backend Engineer", "description": "High scale role"}, headers=alpha_headers).json()
    job_id = job["id"]
    db_client.post(f"/api/v1/recruiter/jobs/{job_id}/publish", headers=alpha_headers)

    # 5. Candidate uploads resume
    resume_bytes = b"%PDF-1.4 authorized applicant resume bytes"
    files = {"file": ("alpha_applicant_resume.pdf", io.BytesIO(resume_bytes), "application/pdf")}
    res_upload = db_client.post("/api/v1/resumes/upload", files=files, data={"name": "Alpha App CV"}, headers=cand_headers)
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]

    # 6. Candidate applies to Alpha's job
    apply_res = db_client.post(
        f"/api/v1/jobs/{job_id}/apply",
        json={"resume_id": resume_id, "notes": "Interested in Alpha Tech"},
        headers=cand_headers,
    )
    assert apply_res.status_code == 201
    application_id = apply_res.json()["id"]

    # TEST 1: Unauthenticated request -> 401 Unauthorized
    res_unauth = db_client.get(f"/api/v1/recruiter/jobs/applications/{application_id}/resume")
    assert res_unauth.status_code == 401
    assert "detail" in res_unauth.json()

    # TEST 2: Candidate user -> 403 Forbidden
    res_cand = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{application_id}/resume",
        headers=cand_headers,
    )
    assert res_cand.status_code == 403

    # TEST 3: Cross-tenant recruiter (Beta) accessing Alpha's applicant resume -> 404 Not Found
    res_cross = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{application_id}/resume",
        headers=beta_headers,
    )
    assert res_cross.status_code == 404

    # TEST 4: Non-existent application ID -> 404 Not Found
    res_not_found = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{uuid4()}/resume",
        headers=alpha_headers,
    )
    assert res_not_found.status_code == 404

    # TEST 5: Authorized Alpha recruiter -> 200 OK with secure headers and correct content
    res_auth = db_client.get(
        f"/api/v1/recruiter/jobs/applications/{application_id}/resume",
        headers=alpha_headers,
    )
    assert res_auth.status_code == 200
    assert res_auth.content == resume_bytes
    assert "attachment" in res_auth.headers.get("content-disposition", "")
    assert "alpha_applicant_resume.pdf" in res_auth.headers.get("content-disposition", "")
    assert res_auth.headers.get("x-content-type-options") == "nosniff"


# ===========================================================================
# 7. Recruiter Analytics Dashboard
# ===========================================================================

def test_recruiter_analytics_metrics(db_client: TestClient):
    """Hirer dashboard returns active_jobs_posted and recruiter counts rather than candidate metrics."""
    register_user(
        db_client,
        email="analytics_hirer@corp.com",
        username="analytics_hirer",
        role="HIRER",
        organization_name="Analytics Corp",
    )
    headers = auth_headers(db_client, "analytics_hirer@corp.com")

    # Create 1 draft and 1 published job
    j1 = db_client.post("/api/v1/recruiter/jobs", json={"title": "Job 1", "description": "D1"}, headers=headers).json()
    j2 = db_client.post("/api/v1/recruiter/jobs", json={"title": "Job 2", "description": "D2"}, headers=headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{j2['id']}/publish", headers=headers)

    # Check analytics dashboard
    dash_res = db_client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["total_jobs_posted"] == 2
    assert dash["active_jobs_posted"] == 1
    assert dash["total_applicants"] == 0
    # Candidate specific metrics should be zero/empty
    assert dash["active_applications"] == 0


# ===========================================================================
# 8. CRIT-01: Candidate Private Notes Isolation
# ===========================================================================

def test_crit_01_candidate_private_notes_invisible_to_recruiter(db_client: TestClient):
    """Candidate private application notes must never be serialized to recruiters."""
    # 1. Hirer posts and publishes a job
    register_user(db_client, email="rec_priv@corp.com", username="rec_priv", role="HIRER", organization_name="Privacy Corp")
    rec_headers = auth_headers(db_client, "rec_priv@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Privacy Engineer", "description": "Security role"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    # 2. Candidate registers, uploads resume, applies
    register_user(db_client, email="cand_priv@user.com", username="cand_priv", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_priv@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("priv_cv.pdf", io.BytesIO(b"%PDF-1.4 privacy resume"), "application/pdf")},
        headers=cand_headers,
    )
    resume_id = res_upload.json()["id"]

    apply_res = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": resume_id, "notes": "Official cover note text"},
        headers=cand_headers,
    )
    assert apply_res.status_code == 201
    app_id = apply_res.json()["id"]

    # 3. Candidate creates a private ApplicationNote
    note_res = db_client.post(
        f"/api/v1/applications/{app_id}/notes",
        json={"content": "CONFIDENTIAL: Aiming for 200k, interviewing elsewhere."},
        headers=cand_headers,
    )
    assert note_res.status_code == 201

    # Candidate CAN see their private note
    cand_notes = db_client.get(f"/api/v1/applications/{app_id}/notes", headers=cand_headers).json()
    assert any("CONFIDENTIAL" in n["content"] for n in cand_notes)

    # 4. Recruiter reviews applicant details
    rec_view = db_client.get(f"/api/v1/recruiter/jobs/applications/{app_id}", headers=rec_headers)
    assert rec_view.status_code == 200
    rec_data = rec_view.json()

    # Recruiter applicant notes must NOT leak candidate private notes
    rec_notes = rec_data.get("notes", [])
    assert not any("CONFIDENTIAL" in n.get("content", "") for n in rec_notes)
    # Cover notes must not be overwritten by candidate private note
    assert "CONFIDENTIAL" not in (rec_data.get("cover_notes") or "")


# ===========================================================================
# 9. CRIT-02: Recruiter Internal Evaluation & Stage Notes Author Identity
# ===========================================================================

def test_crit_02_recruiter_notes_invisible_to_candidate_and_author_preserved(db_client: TestClient):
    """Recruiter transition comments must not leak to candidate, and author must be the recruiter."""
    # Setup hirer & job
    register_user(db_client, email="rec_stage@corp.com", username="rec_stage", role="HIRER", organization_name="Stage Corp")
    rec_headers = auth_headers(db_client, "rec_stage@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "DevOps Engineer", "description": "K8s"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    # Setup candidate & apply
    register_user(db_client, email="cand_stage@user.com", username="cand_stage", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_stage@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("stage_cv.pdf", io.BytesIO(b"%PDF-1.4 devops resume"), "application/pdf")},
        headers=cand_headers,
    )
    resume_id = res_upload.json()["id"]

    apply_res = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": resume_id},
        headers=cand_headers,
    )
    app_id = apply_res.json()["id"]

    # Recruiter moves stage with internal evaluation notes
    trans_res = db_client.post(
        f"/api/v1/recruiter/jobs/applications/{app_id}/stage",
        json={"to_stage": "PHONE_SCREEN", "notes": "INTERNAL ONLY: Candidate needs strong grilling on Terraform."},
        headers=rec_headers,
    )
    assert trans_res.status_code == 200

    # Verify recruiter did NOT inject a note into candidate's ApplicationNotes
    cand_notes = db_client.get(f"/api/v1/applications/{app_id}/notes", headers=cand_headers).json()
    assert not any("INTERNAL ONLY" in n.get("content", "") for n in cand_notes)

    # Verify candidate querying stage history receives redacted internal notes
    cand_hist = db_client.get(f"/api/v1/applications/{app_id}/stage-history", headers=cand_headers).json()
    ps_item = next((h for h in cand_hist if h["to_stage"] == "PHONE_SCREEN"), None)
    assert ps_item is not None
    assert ps_item["notes"] is None or "INTERNAL ONLY" not in ps_item["notes"]

    # Recruiter can view the applicant history with their notes
    rec_view = db_client.get(f"/api/v1/recruiter/jobs/applications/{app_id}", headers=rec_headers).json()
    rec_hist = rec_view.get("stage_history", [])
    assert any("INTERNAL ONLY" in (h.get("notes") or "") for h in rec_hist)


# ===========================================================================
# 10. HIGH-02: Backend Candidate RBAC — Hirer Cannot Call Candidate APIs
# ===========================================================================

def test_high_02_hirer_cannot_call_candidate_apis(db_client: TestClient):
    """Hirer users must be rejected with 403 Forbidden on all candidate-only endpoints."""
    register_user(db_client, email="hirer_rbac@corp.com", username="hirer_rbac", role="HIRER", organization_name="RBAC Corp")
    hirer_headers = auth_headers(db_client, "hirer_rbac@corp.com")

    # 1. POST applications
    app_res = db_client.post(
        "/api/v1/applications",
        json={"company_name": "Test Co", "job_title": "SWE", "status": "ACTIVE"},
        headers=hirer_headers,
    )
    assert app_res.status_code == 403

    # 2. POST resumes/upload
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        headers=hirer_headers,
    )
    assert res_upload.status_code == 403

    # 3. POST opportunities
    opp_res = db_client.post(
        "/api/v1/opportunities",
        json={"company_name": "Target Co", "title": "Lead", "status": "SAVED"},
        headers=hirer_headers,
    )
    assert opp_res.status_code == 403

    # 4. PUT profile
    prof_res = db_client.put(
        "/api/v1/profile/personal",
        json={"first_name": "Hacked"},
        headers=hirer_headers,
    )
    assert prof_res.status_code == 403

    # 5. POST interviews
    int_res = db_client.post(
        "/api/v1/interviews",
        json={"application_id": str(uuid4()), "round_type": "BEHAVIORAL", "interview_type": "VIDEO"},
        headers=hirer_headers,
    )
    assert int_res.status_code == 403


# ===========================================================================
# 11. HIGH-03: Candidate Cannot Advance Platform Application Stages
# ===========================================================================

def test_high_03_candidate_cannot_advance_platform_application_stages(db_client: TestClient):
    """Candidates cannot modify recruitment progression on platform jobs (except WITHDRAWN)."""
    register_user(db_client, email="rec_stage_auth@corp.com", username="rec_stage_auth", role="HIRER", organization_name="StageAuth Corp")
    rec_headers = auth_headers(db_client, "rec_stage_auth@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Staff Engineer", "description": "Staff role"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    register_user(db_client, email="cand_stage_auth@user.com", username="cand_stage_auth", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_stage_auth@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("staff_cv.pdf", io.BytesIO(b"%PDF-1.4 staff resume"), "application/pdf")},
        headers=cand_headers,
    )
    app = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": res_upload.json()["id"]},
        headers=cand_headers,
    ).json()
    app_id = app["id"]

    # Candidate attempts to advance to INTERVIEW via transition endpoint -> 403
    t_res = db_client.post(
        f"/api/v1/applications/{app_id}/stage",
        json={"to_stage": "INTERVIEW"},
        headers=cand_headers,
    )
    assert t_res.status_code == 403

    # Candidate attempts to set OFFER via update endpoint -> 403
    p_res = db_client.put(
        f"/api/v1/applications/{app_id}",
        json={"current_stage": "OFFER"},
        headers=cand_headers,
    )
    assert p_res.status_code == 403

    # Candidate CAN withdraw
    w_res = db_client.post(
        f"/api/v1/applications/{app_id}/stage",
        json={"to_stage": "WITHDRAWN"},
        headers=cand_headers,
    )
    assert w_res.status_code == 200
    assert w_res.json()["current_stage"] == "WITHDRAWN"


# ===========================================================================
# 12. HIGH-04: Platform Application Deletion Prohibited
# ===========================================================================

def test_high_04_candidate_cannot_hard_delete_platform_applications(db_client: TestClient):
    """Platform applications must not be hard deleted by candidate (must withdraw)."""
    register_user(db_client, email="rec_del@corp.com", username="rec_del", role="HIRER", organization_name="Delete Corp")
    rec_headers = auth_headers(db_client, "rec_del@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Security Analyst", "description": "SOC"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    register_user(db_client, email="cand_del@user.com", username="cand_del", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_del@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("sec_cv.pdf", io.BytesIO(b"%PDF-1.4 sec resume"), "application/pdf")},
        headers=cand_headers,
    )
    app = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": res_upload.json()["id"]},
        headers=cand_headers,
    ).json()
    app_id = app["id"]

    # Attempt hard-delete platform application -> 400
    del_res = db_client.delete(f"/api/v1/applications/{app_id}", headers=cand_headers)
    assert del_res.status_code == 400
    assert "withdraw" in del_res.json()["detail"].lower()

    # Manual candidate-only application CAN be deleted
    man_app = db_client.post(
        "/api/v1/applications",
        json={"company_name": "External Startup", "job_title": "Consultant", "status": "ACTIVE"},
        headers=cand_headers,
    ).json()
    assert db_client.delete(f"/api/v1/applications/{man_app['id']}", headers=cand_headers).status_code == 200


# ===========================================================================
# 13. HIGH-05: Organization Slug Collision Handling
# ===========================================================================

def test_high_05_organization_slug_collision_handled_gracefully(db_client: TestClient):
    """Duplicate organization names must generate unique slugs without 500 error."""
    # Hirer 1 with Org 'Innovatech'
    res1 = register_user(
        db_client,
        email="hirer1@innovatech.com",
        username="innovatech_1",
        role="HIRER",
        organization_name="Innovatech",
    )
    assert res1.status_code == 201
    h1_headers = auth_headers(db_client, "hirer1@innovatech.com")
    org1 = db_client.get("/api/v1/recruiter/organization", headers=h1_headers).json()
    assert org1["slug"] == "innovatech"

    # Hirer 2 with duplicate Org 'Innovatech'
    res2 = register_user(
        db_client,
        email="hirer2@innovatech.com",
        username="innovatech_2",
        role="HIRER",
        organization_name="Innovatech",
    )
    assert res2.status_code == 201
    h2_headers = auth_headers(db_client, "hirer2@innovatech.com")
    org2 = db_client.get("/api/v1/recruiter/organization", headers=h2_headers).json()
    assert org2["slug"].startswith("innovatech-")
    assert org2["slug"] != org1["slug"]


# ===========================================================================
# 14. MED-01: Opportunity job_posting_id Serialization
# ===========================================================================

def test_med_01_opportunity_job_posting_id_serialization(db_client: TestClient):
    """Saved opportunity must persist and serialize job_posting_id in API response."""
    register_user(db_client, email="rec_opp@corp.com", username="rec_opp", role="HIRER", organization_name="Opp Corp")
    rec_headers = auth_headers(db_client, "rec_opp@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Frontend Architect", "description": "React"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    register_user(db_client, email="cand_opp@user.com", username="cand_opp", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_opp@user.com")

    # Save job
    save_res = db_client.post(f"/api/v1/jobs/{job['id']}/save", headers=cand_headers)
    assert save_res.status_code == 201
    opp_data = save_res.json()
    assert opp_data.get("job_posting_id") == job["id"]

    # Verify in list
    list_res = db_client.get("/api/v1/opportunities", headers=cand_headers)
    assert list_res.status_code == 200
    opps = list_res.json().get("items", [])
    found = next((o for o in opps if o["id"] == opp_data["id"]), None)
    assert found is not None
    assert found.get("job_posting_id") == job["id"]

    # Verify in detail
    detail_res = db_client.get(f"/api/v1/opportunities/{opp_data['id']}", headers=cand_headers)
    assert detail_res.status_code == 200
    assert detail_res.json().get("job_posting_id") == job["id"]


# ===========================================================================
# 15. MED-02: Expired Job Application Rejection
# ===========================================================================

def test_med_02_expired_job_rejects_new_applications(db_client: TestClient):
    """Applications to jobs past their deadline date must be rejected with 400."""
    register_user(db_client, email="rec_exp@corp.com", username="rec_exp", role="HIRER", organization_name="Expire Corp")
    rec_headers = auth_headers(db_client, "rec_exp@corp.com")

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    job = db_client.post(
        "/api/v1/recruiter/jobs",
        json={"title": "Expired Job", "description": "Past deadline", "deadline_date": yesterday},
        headers=rec_headers,
    ).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    register_user(db_client, email="cand_exp@user.com", username="cand_exp", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_exp@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("exp_cv.pdf", io.BytesIO(b"%PDF-1.4 exp resume"), "application/pdf")},
        headers=cand_headers,
    )

    # Attempt apply -> 400
    apply_res = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": res_upload.json()["id"]},
        headers=cand_headers,
    )
    assert apply_res.status_code == 400
    assert "deadline" in apply_res.json()["detail"].lower()


# ===========================================================================
# 16. MED-03: Archived Job Terminal Lifecycle
# ===========================================================================

def test_med_03_archived_job_cannot_be_modified_or_republished(db_client: TestClient):
    """Archived job postings cannot be edited, republished, or closed."""
    register_user(db_client, email="rec_arch@corp.com", username="rec_arch", role="HIRER", organization_name="Archive Corp")
    rec_headers = auth_headers(db_client, "rec_arch@corp.com")

    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Old Legacy Role", "description": "Legacy"}, headers=rec_headers).json()
    job_id = job["id"]

    # Archive the job
    arch_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/archive", headers=rec_headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"

    # Attempt to edit
    edit_res = db_client.patch(f"/api/v1/recruiter/jobs/{job_id}", json={"title": "Updated Title"}, headers=rec_headers)
    assert edit_res.status_code == 400
    assert "archived" in edit_res.json()["detail"].lower()

    # Attempt to republish
    pub_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/publish", headers=rec_headers)
    assert pub_res.status_code == 400
    assert "archived" in pub_res.json()["detail"].lower()

    # Attempt to close
    close_res = db_client.post(f"/api/v1/recruiter/jobs/{job_id}/close", headers=rec_headers)
    assert close_res.status_code == 400
    assert "archived" in close_res.json()["detail"].lower()


# ===========================================================================
# 17. MED-04 & MED-05: Hirer Dashboard & Application Deduplication
# ===========================================================================

def test_med_04_hirer_dashboard_summary_metrics(db_client: TestClient):
    """Dashboard summary for HIRER returns role-specific metrics."""
    register_user(db_client, email="hirer_dash@corp.com", username="hirer_dash", role="HIRER", organization_name="Dashboard Corp")
    rec_headers = auth_headers(db_client, "hirer_dash@corp.com")

    # Create job & publish
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Fullstack Dev", "description": "TS/Py"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    # Candidate applies
    register_user(db_client, email="cand_dash@user.com", username="cand_dash", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_dash@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("dash_cv.pdf", io.BytesIO(b"%PDF-1.4 dash resume"), "application/pdf")},
        headers=cand_headers,
    )
    apply_res = db_client.post(
        f"/api/v1/jobs/{job['id']}/apply",
        json={"resume_id": res_upload.json()["id"]},
        headers=cand_headers,
    )
    app_id = apply_res.json()["id"]

    # Move to INTERVIEW
    db_client.post(
        f"/api/v1/recruiter/jobs/applications/{app_id}/stage",
        json={"to_stage": "INTERVIEW"},
        headers=rec_headers,
    )

    # Request dashboard
    dash = db_client.get("/api/v1/dashboard/summary", headers=rec_headers).json()
    assert dash["role"] == "HIRER"
    assert dash["total_jobs_posted"] == 1
    assert dash["active_jobs_posted"] == 1
    assert dash["total_applicants"] == 1
    assert dash["total_interviews"] == 1
    assert dash["active_applications"] == 0


def test_med_05_duplicate_platform_application_prevention(db_client: TestClient):
    """Submitting duplicate application to same job posting raises 409 Conflict."""
    register_user(db_client, email="rec_dup@corp.com", username="rec_dup", role="HIRER", organization_name="Dup Corp")
    rec_headers = auth_headers(db_client, "rec_dup@corp.com")
    job = db_client.post("/api/v1/recruiter/jobs", json={"title": "Data Engineer", "description": "ETL"}, headers=rec_headers).json()
    db_client.post(f"/api/v1/recruiter/jobs/{job['id']}/publish", headers=rec_headers)

    register_user(db_client, email="cand_dup@user.com", username="cand_dup", role="CANDIDATE")
    cand_headers = auth_headers(db_client, "cand_dup@user.com")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("dup_cv.pdf", io.BytesIO(b"%PDF-1.4 dup resume"), "application/pdf")},
        headers=cand_headers,
    )
    resume_id = res_upload.json()["id"]

    # First apply -> 201
    res1 = db_client.post(f"/api/v1/jobs/{job['id']}/apply", json={"resume_id": resume_id}, headers=cand_headers)
    assert res1.status_code == 201

    # Second apply -> 409 Conflict
    res2 = db_client.post(f"/api/v1/jobs/{job['id']}/apply", json={"resume_id": resume_id}, headers=cand_headers)
    assert res2.status_code == 409


# ===========================================================================
# 18. Phase 16: Strict Tenant Isolation Test Matrix (4 Users)
# ===========================================================================

def test_tenant_isolation_matrix_four_users(db_client: TestClient):
    """
    Complete Phase 16 Tenant Isolation Matrix:
    - Candidate A
    - Candidate B
    - Hirer C
    - Hirer D
    """
    # 1. Register users
    register_user(db_client, email="cand_a@matrix.com", username="cand_a", role="CANDIDATE")
    headers_cand_a = auth_headers(db_client, "cand_a@matrix.com")

    register_user(db_client, email="cand_b@matrix.com", username="cand_b", role="CANDIDATE")
    headers_cand_b = auth_headers(db_client, "cand_b@matrix.com")

    register_user(db_client, email="hirer_c@matrix.com", username="hirer_c", role="HIRER", organization_name="Company C")
    headers_hirer_c = auth_headers(db_client, "hirer_c@matrix.com")

    register_user(db_client, email="hirer_d@matrix.com", username="hirer_d", role="HIRER", organization_name="Company D")
    headers_hirer_d = auth_headers(db_client, "hirer_d@matrix.com")

    # 2. Hirer C creates Job 1 and publishes it
    job_res = db_client.post("/api/v1/recruiter/jobs", json={"title": "Cloud Architect", "description": "AWS/GCP"}, headers=headers_hirer_c)
    assert job_res.status_code == 201
    job_1_id = job_res.json()["id"]
    db_client.post(f"/api/v1/recruiter/jobs/{job_1_id}/publish", headers=headers_hirer_c)

    # 3. Candidate A uploads resume, applies to Job 1, adds private note
    resume_bytes = b"%PDF-1.4 candidate a confidential resume"
    cv_res = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cand_a.pdf", io.BytesIO(resume_bytes), "application/pdf")},
        headers=headers_cand_a,
    )
    resume_a_id = cv_res.json()["id"]

    apply_res = db_client.post(
        f"/api/v1/jobs/{job_1_id}/apply",
        json={"resume_id": resume_a_id, "notes": "Candidate A cover letter text"},
        headers=headers_cand_a,
    )
    assert apply_res.status_code == 201
    app_a_id = apply_res.json()["id"]

    # Candidate A creates private note
    db_client.post(
        f"/api/v1/applications/{app_a_id}/notes",
        json={"content": "CANDIDATE_A_PRIVATE_SALARY_TARGET: 180k"},
        headers=headers_cand_a,
    )

    # ==========================================
    # Verification: Candidate A
    # ==========================================
    # YES -> own application
    assert db_client.get(f"/api/v1/applications/{app_a_id}", headers=headers_cand_a).status_code == 200
    # YES -> own submitted resume
    assert db_client.get(f"/api/v1/resumes/{resume_a_id}/download", headers=headers_cand_a).status_code == 200
    # YES -> own private notes
    cand_a_notes = db_client.get(f"/api/v1/applications/{app_a_id}/notes", headers=headers_cand_a).json()
    assert any("CANDIDATE_A_PRIVATE_SALARY_TARGET" in n["content"] for n in cand_a_notes)
    # YES -> Job 1 on public board
    assert db_client.get(f"/api/v1/jobs/{job_1_id}", headers=headers_cand_a).status_code == 200
    # NO -> recruiter management APIs
    assert db_client.get("/api/v1/recruiter/jobs", headers=headers_cand_a).status_code == 403

    # ==========================================
    # Verification: Hirer C
    # ==========================================
    # YES -> Job 1
    assert db_client.get(f"/api/v1/recruiter/jobs/{job_1_id}", headers=headers_hirer_c).status_code == 200
    # YES -> Candidate A application
    rec_app = db_client.get(f"/api/v1/recruiter/jobs/applications/{app_a_id}", headers=headers_hirer_c)
    assert rec_app.status_code == 200
    # YES -> submitted application resume
    stream_res = db_client.get(f"/api/v1/recruiter/jobs/applications/{app_a_id}/resume", headers=headers_hirer_c)
    assert stream_res.status_code == 200
    assert stream_res.content == resume_bytes
    # YES -> authorized applicant information
    assert rec_app.json()["candidate"]["email"] == "cand_a@matrix.com"
    # NO -> Candidate A private notes
    assert not any("CANDIDATE_A_PRIVATE_SALARY_TARGET" in n.get("content", "") for n in rec_app.json().get("notes", []))
    # NO -> arbitrary candidate private profile/vault
    assert db_client.get(f"/api/v1/resumes/{resume_a_id}/download", headers=headers_hirer_c).status_code == 403

    # ==========================================
    # Verification: Candidate B
    # ==========================================
    # NO -> Candidate A application
    assert db_client.get(f"/api/v1/applications/{app_a_id}", headers=headers_cand_b).status_code == 404
    # NO -> Candidate A resume
    assert db_client.get(f"/api/v1/resumes/{resume_a_id}/download", headers=headers_cand_b).status_code == 404
    # NO -> Candidate A notes
    assert db_client.get(f"/api/v1/applications/{app_a_id}/notes", headers=headers_cand_b).status_code == 404

    # ==========================================
    # Verification: Hirer D
    # ==========================================
    # NO -> Hirer C jobs
    assert db_client.get(f"/api/v1/recruiter/jobs/{job_1_id}", headers=headers_hirer_d).status_code == 404
    # NO -> Hirer C applicants
    assert db_client.get(f"/api/v1/recruiter/jobs/{job_1_id}/applicants", headers=headers_hirer_d).status_code == 404
    # NO -> Candidate A application
    assert db_client.get(f"/api/v1/recruiter/jobs/applications/{app_a_id}", headers=headers_hirer_d).status_code == 404
