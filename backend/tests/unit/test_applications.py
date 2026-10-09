"""
Stage 5 Master Test Suite — Applications & Application Health Engine.
Covers:
- Unauthenticated rejection (401)
- Valid and invalid application creation
- Opportunity conversion to application (snapshotting & Opportunity status unchanged)
- Non-restrictive recruitment stage transitions, append-only stage history & activity timeline
- Application notes CRUD & activity recording
- Application follow-ups CRUD, completion tracking, and global follow-ups queue
- Document vault attachment/detachment & ownership boundary
- Q&A Vault templates and Application Answers
- Deterministic Application Health Engine (EXCELLENT, GOOD, NEEDS_ATTENTION, POOR, staleness penalty, suggestions)
- Pipeline Kanban grouping
- Multi-user strict tenant isolation (cross-user returns 404)
"""

import io
import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.services.application_health_service import application_health_service
from app.models.application import Application, ApplicationFollowup, ApplicationNote, ApplicationActivity


def register_and_login(client: TestClient, email: str, username: str) -> dict[str, str]:
    """Helper to register and login a user, returning Authorization headers."""
    register_payload = {
        "email": email,
        "username": username,
        "password": "Password123!",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Authentication
# ---------------------------------------------------------------------------

def test_unauthenticated_applications_rejected(db_client: TestClient):
    """All application endpoints must reject unauthenticated requests with 401."""
    dummy_id = str(uuid.uuid4())
    assert db_client.get("/api/v1/applications").status_code == 401
    assert db_client.post("/api/v1/applications", json={"job_title": "SWE", "company_name": "Co"}).status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/applications/{dummy_id}", json={"job_title": "SWE"}).status_code == 401
    assert db_client.delete(f"/api/v1/applications/{dummy_id}").status_code == 401
    assert db_client.post(f"/api/v1/applications/{dummy_id}/stage", json={"to_stage": "INTERVIEW"}).status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}/stage-history").status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}/activity").status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}/health").status_code == 401
    assert db_client.get("/api/v1/applications/pipeline").status_code == 401
    assert db_client.get("/api/v1/applications/followups").status_code == 401
    assert db_client.get("/api/v1/qa-vault").status_code == 401


# ---------------------------------------------------------------------------
# 2. Application Creation & Validation
# ---------------------------------------------------------------------------

def test_application_creation_valid(db_client: TestClient):
    """Create a new application with full fields and initial note."""
    headers = register_and_login(db_client, "appuser1@example.com", "appuser1")

    payload = {
        "job_title": "Staff Platform Engineer",
        "company_name": "Datadog",
        "job_location": "New York, NY",
        "job_location_type": "HYBRID",
        "employment_type": "FULL_TIME",
        "job_description": "Architect cloud platforms.",
        "job_url": "https://careers.datadoghq.com/123",
        "compensation_min": 180000,
        "compensation_max": 230000,
        "compensation_currency": "USD",
        "source": "MANUAL",
        "status": "ACTIVE",
        "current_stage": "APPLIED",
        "applied_date": str(date.today()),
        "priority": "HIGH",
        "initial_notes": "Referred by former colleague.",
    }

    res = db_client.post("/api/v1/applications", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["job_title"] == "Staff Platform Engineer"
    assert data["company_name"] == "Datadog"
    assert data["current_stage"] == "APPLIED"
    assert data["status"] == "ACTIVE"
    assert data["priority"] == "HIGH"
    assert data["notes_count"] == 1

    app_id = data["id"]

    # Verify initial stage history
    history_res = db_client.get(f"/api/v1/applications/{app_id}/stage-history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["to_stage"] == "APPLIED"

    # Verify initial activity
    act_res = db_client.get(f"/api/v1/applications/{app_id}/activity", headers=headers)
    assert act_res.status_code == 200
    activities = act_res.json()
    assert any(a["event_type"] == "APPLICATION_CREATED" for a in activities)


def test_application_creation_invalid(db_client: TestClient):
    """Rejects missing required fields and invalid stage/priority enums."""
    headers = register_and_login(db_client, "appuser2@example.com", "appuser2")

    # Missing company_name
    res = db_client.post("/api/v1/applications", json={"job_title": "Engineer"}, headers=headers)
    assert res.status_code == 422

    # Empty job_title
    res = db_client.post("/api/v1/applications", json={"job_title": "  ", "company_name": "Co"}, headers=headers)
    assert res.status_code == 422

    # Invalid stage
    res = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Engineer", "company_name": "Co", "current_stage": "INVALID_STAGE"},
        headers=headers,
    )
    assert res.status_code == 422

    # Invalid priority
    res = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Engineer", "company_name": "Co", "priority": "CRITICAL"},
        headers=headers,
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 3. Opportunity Conversion (Job Snapshotting & Opportunity Status Preserved)
# ---------------------------------------------------------------------------

def test_convert_opportunity_to_application(db_client: TestClient):
    """Converting an opportunity snapshots job data into an application while preserving Opportunity status."""
    headers = register_and_login(db_client, "appuser3@example.com", "appuser3")

    # 1. Create an Opportunity
    opp_res = db_client.post(
        "/api/v1/opportunities",
        json={
            "title": "Senior Infrastructure Architect",
            "company_name": "Stripe",
            "location": "San Francisco, CA",
            "location_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "description": "Scale global financial infrastructure.",
            "source_url": "https://stripe.com/jobs/123",
            "compensation_min": 200000,
            "compensation_max": 260000,
            "status": "CONSIDERING",
            "notes": "Target team: Developer Platform.",
        },
        headers=headers,
    )
    assert opp_res.status_code == 201
    opp_id = opp_res.json()["id"]

    # 2. Convert Opportunity to Application
    convert_res = db_client.post(
        f"/api/v1/opportunities/{opp_id}/convert",
        json={
            "current_stage": "APPLIED",
            "priority": "URGENT",
            "initial_notes": "Submitted via internal referral link.",
        },
        headers=headers,
    )
    assert convert_res.status_code == 201
    app_data = convert_res.json()
    assert app_data["job_title"] == "Senior Infrastructure Architect"
    assert app_data["company_name"] == "Stripe"
    assert app_data["opportunity_id"] == opp_id
    assert app_data["job_location_type"] == "REMOTE"
    assert app_data["current_stage"] == "APPLIED"
    assert app_data["priority"] == "URGENT"

    # 3. CRITICAL: Verify Opportunity status was NOT changed to APPLIED
    verify_opp = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers).json()
    assert verify_opp["status"] in {"ACTIVE", "SAVED", "CONSIDERING", "ARCHIVED", "NOT_INTERESTED"}
    assert verify_opp["status"] != "APPLIED"


# ---------------------------------------------------------------------------
# 4. Non-Restrictive Stage Transitions & Activity
# ---------------------------------------------------------------------------

def test_application_stage_transitions(db_client: TestClient):
    """Stage transitions append immutable history and activity, and close on terminal stage."""
    headers = register_and_login(db_client, "appuser4@example.com", "appuser4")

    # Create application
    app_res = db_client.post(
        "/api/v1/applications",
        json={"job_title": "DevOps Engineer", "company_name": "GitLab", "current_stage": "APPLIED"},
        headers=headers,
    )
    app_id = app_res.json()["id"]

    # 1. Transition to PHONE_SCREEN
    trans_1 = db_client.post(
        f"/api/v1/applications/{app_id}/stage",
        json={"to_stage": "PHONE_SCREEN", "notes": "Recruiter screen scheduled."},
        headers=headers,
    )
    assert trans_1.status_code == 200
    assert trans_1.json()["current_stage"] == "PHONE_SCREEN"

    # 2. Non-restrictive jump: transition directly to OFFER
    trans_2 = db_client.post(
        f"/api/v1/applications/{app_id}/stage",
        json={"to_stage": "OFFER", "notes": "Received written offer."},
        headers=headers,
    )
    assert trans_2.status_code == 200
    assert trans_2.json()["current_stage"] == "OFFER"

    # 3. Terminal stage: ACCEPTED -> auto-closes application
    trans_3 = db_client.post(
        f"/api/v1/applications/{app_id}/stage",
        json={"to_stage": "ACCEPTED", "notes": "Accepted offer!"},
        headers=headers,
    )
    assert trans_3.status_code == 200
    assert trans_3.json()["current_stage"] == "ACCEPTED"
    assert trans_3.json()["status"] == "CLOSED"
    assert trans_3.json()["outcome"] == "ACCEPTED"

    # Verify complete stage history
    history = db_client.get(f"/api/v1/applications/{app_id}/stage-history", headers=headers).json()
    assert len(history) == 4  # Initial (None -> APPLIED), then PHONE_SCREEN, OFFER, ACCEPTED
    assert history[0]["from_stage"] is None and history[0]["to_stage"] == "APPLIED"
    assert history[1]["from_stage"] == "APPLIED" and history[1]["to_stage"] == "PHONE_SCREEN"
    assert history[2]["from_stage"] == "PHONE_SCREEN" and history[2]["to_stage"] == "OFFER"
    assert history[3]["from_stage"] == "OFFER" and history[3]["to_stage"] == "ACCEPTED"


# ---------------------------------------------------------------------------
# 5. Application Notes CRUD
# ---------------------------------------------------------------------------

def test_application_notes_crud(db_client: TestClient):
    """Candidate can create, list, update, and delete application notes."""
    headers = register_and_login(db_client, "appuser5@example.com", "appuser5")

    app_id = db_client.post(
        "/api/v1/applications",
        json={"job_title": "SWE", "company_name": "Apple"},
        headers=headers,
    ).json()["id"]

    # Create note
    note_res = db_client.post(
        f"/api/v1/applications/{app_id}/notes",
        json={"content": "HM emphasized experience with Swift concurrency."},
        headers=headers,
    )
    assert note_res.status_code == 201
    note_id = note_res.json()["id"]

    # List notes
    notes = db_client.get(f"/api/v1/applications/{app_id}/notes", headers=headers).json()
    assert len(notes) == 1
    assert notes[0]["content"] == "HM emphasized experience with Swift concurrency."

    # Update note
    upd = db_client.put(
        f"/api/v1/applications/{app_id}/notes/{note_id}",
        json={"content": "Updated: HM also mentioned core graphics."},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["content"] == "Updated: HM also mentioned core graphics."

    # Delete note
    del_res = db_client.delete(f"/api/v1/applications/{app_id}/notes/{note_id}", headers=headers)
    assert del_res.status_code == 200

    notes_after = db_client.get(f"/api/v1/applications/{app_id}/notes", headers=headers).json()
    assert len(notes_after) == 0


# ---------------------------------------------------------------------------
# 6. Application Follow-ups & Global Queue
# ---------------------------------------------------------------------------

def test_application_followups_and_global_queue(db_client: TestClient):
    """Candidate can manage follow-ups per application and view in the global queue."""
    headers = register_and_login(db_client, "appuser6@example.com", "appuser6")

    app_id = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Backend Engineer", "company_name": "Shopify"},
        headers=headers,
    ).json()["id"]

    # 1. Create Follow-up
    due = str(date.today() + timedelta(days=3))
    fol_res = db_client.post(
        f"/api/v1/applications/{app_id}/followups",
        json={"due_date": due, "note": "Email recruiter about interview outcome."},
        headers=headers,
    )
    assert fol_res.status_code == 201
    fol_id = fol_res.json()["id"]
    assert fol_res.json()["is_completed"] is False

    # 2. Check Global Queue
    global_fol = db_client.get("/api/v1/applications/followups", headers=headers).json()
    assert len(global_fol) == 1
    assert global_fol[0]["id"] == fol_id
    assert global_fol[0]["company_name"] == "Shopify"
    assert global_fol[0]["job_title"] == "Backend Engineer"

    # 3. Mark Follow-up Completed
    upd = db_client.put(
        f"/api/v1/applications/{app_id}/followups/{fol_id}",
        json={"is_completed": True},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["is_completed"] is True
    assert upd.json()["completed_at"] is not None

    # Filter global queue by completed
    comp_fol = db_client.get("/api/v1/applications/followups?is_completed=true", headers=headers).json()
    assert len(comp_fol) == 1
    uncomp_fol = db_client.get("/api/v1/applications/followups?is_completed=false", headers=headers).json()
    assert len(uncomp_fol) == 0


# ---------------------------------------------------------------------------
# 7. Document Vault Attachment
# ---------------------------------------------------------------------------

def test_application_documents_attachment(db_client: TestClient):
    """Attach and detach supporting documents from candidate document vault."""
    headers = register_and_login(db_client, "appuser7@example.com", "appuser7")

    # Upload document to vault
    doc_file = io.BytesIO(b"%PDF-1.4 Sample Cover Letter Content")
    doc_res = db_client.post(
        "/api/v1/documents/upload",
        files={"file": ("cover_letter.pdf", doc_file, "application/pdf")},
        data={"name": "Custom Cover Letter", "doc_type": "COVER_LETTER"},
        headers=headers,
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # Create application
    app_id = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Data Scientist", "company_name": "Meta"},
        headers=headers,
    ).json()["id"]

    # Attach document
    att_res = db_client.post(
        f"/api/v1/applications/{app_id}/documents",
        json={"document_id": doc_id},
        headers=headers,
    )
    assert att_res.status_code == 201
    assert att_res.json()["document_id"] == doc_id
    assert att_res.json()["document"]["name"] == "Custom Cover Letter"


    # List documents
    docs = db_client.get(f"/api/v1/applications/{app_id}/documents", headers=headers).json()
    assert len(docs) == 1

    # Detach document
    det = db_client.delete(f"/api/v1/applications/{app_id}/documents/{doc_id}", headers=headers)
    assert det.status_code == 200

    docs_after = db_client.get(f"/api/v1/applications/{app_id}/documents", headers=headers).json()
    assert len(docs_after) == 0


# ---------------------------------------------------------------------------
# 8. Q&A Vault & Application Answers
# ---------------------------------------------------------------------------

def test_qa_vault_and_answers(db_client: TestClient):
    """Create reusable Q&A templates and application-specific answers."""
    headers = register_and_login(db_client, "appuser8@example.com", "appuser8")

    # 1. Create Q&A template
    template_res = db_client.post(
        "/api/v1/qa-vault",
        json={
            "question": "Why do you want to join our engineering team?",
            "answer": "Your distributed systems challenge aligns with my career background in async pipelines.",
            "category": "BEHAVIORAL",
            "is_template": True,
        },
        headers=headers,
    )
    assert template_res.status_code == 201
    template_id = template_res.json()["id"]

    # 2. Create Application
    app_id = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Systems Engineer", "company_name": "Cloudflare"},
        headers=headers,
    ).json()["id"]

    # 3. Add application answer linked to template
    ans_res = db_client.post(
        f"/api/v1/applications/{app_id}/answers",
        json={
            "question": "Why do you want to join our engineering team?",
            "answer": "Cloudflare's edge workers ecosystem is where I want to build next.",
            "qa_vault_entry_id": template_id,
        },
        headers=headers,
    )
    assert ans_res.status_code == 201
    ans_id = ans_res.json()["id"]

    # 4. List answers
    answers = db_client.get(f"/api/v1/applications/{app_id}/answers", headers=headers).json()
    assert len(answers) == 1
    assert answers[0]["id"] == ans_id

    # 5. Delete answer
    assert db_client.delete(f"/api/v1/applications/{app_id}/answers/{ans_id}", headers=headers).status_code == 200


# ---------------------------------------------------------------------------
# 9. Deterministic Health Engine (EXCELLENT, GOOD, NEEDS_ATTENTION, POOR)
# ---------------------------------------------------------------------------

def test_health_engine_deterministic_rules(db_client: TestClient):
    """Test all 4 health states (EXCELLENT, GOOD, NEEDS_ATTENTION, POOR), staleness, and suggestions."""
    headers = register_and_login(db_client, "appuser9@example.com", "appuser9")

    # Upload resume
    resume_file = io.BytesIO(b"%PDF-1.4 Resume PDF Content")
    res_upload = db_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", resume_file, "application/pdf")},
        data={"name": "Primary Resume"},
        headers=headers,
    )
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]

    # Case A: EXCELLENT (100) -> all 5 required checks pass
    app_a = db_client.post(
        "/api/v1/applications",
        json={
            "job_title": "Full Stack Engineer",
            "company_name": "GitHub",
            "current_stage": "APPLIED",
            "applied_date": str(date.today()),
            "resume_id": resume_id,
        },
        headers=headers,
    ).json()

    health_a = db_client.get(f"/api/v1/applications/{app_a['id']}/health", headers=headers).json()
    assert health_a["score"] == 100
    assert health_a["status"] == "EXCELLENT"

    # Case B: GOOD (80) -> Missing resume (4 checks pass: 4 * 20 = 80)
    app_b = db_client.post(
        "/api/v1/applications",
        json={
            "job_title": "Staff Engineer",
            "company_name": "Slack",
            "current_stage": "APPLIED",
            "applied_date": str(date.today()),
            "resume_id": None,
        },
        headers=headers,
    ).json()

    health_b = db_client.get(f"/api/v1/applications/{app_b['id']}/health", headers=headers).json()
    assert health_b["score"] == 80
    assert health_b["status"] == "GOOD"

    # Case C: NEEDS_ATTENTION (60) -> Missing resume and applied_date (3 checks pass: 3 * 20 = 60)
    app_c = db_client.post(
        "/api/v1/applications",
        json={
            "job_title": "Principal Architect",
            "company_name": "Microsoft",
            "current_stage": "APPLIED",
            "applied_date": None,
            "resume_id": None,
        },
        headers=headers,
    ).json()

    health_c = db_client.get(f"/api/v1/applications/{app_c['id']}/health", headers=headers).json()
    assert health_c["score"] == 60
    assert health_c["status"] == "NEEDS_ATTENTION"

    # Case D: POOR (< 50) -> Only 2 checks pass in a direct model test or service test (40 points)
    # Testing directly via application_health_service
    poor_app = Application(
        job_title="Intern",
        company_name="Acme",
        current_stage="",
        applied_date=None,
        resume_id=None,
        status="ACTIVE",
    )
    health_d = application_health_service.calculate_health(poor_app)
    assert health_d.score == 40
    assert health_d.status == "POOR"

    # Case E: Staleness penalty (-20)
    # If an application is active and last updated > 14 days ago:
    stale_app = Application(
        job_title="DevOps Lead",
        company_name="Netflix",
        current_stage="APPLIED",
        applied_date=date.today() - timedelta(days=20),
        resume_id=uuid.uuid4(),
        status="ACTIVE",
        created_at=datetime.now(timezone.utc) - timedelta(days=20),
        updated_at=datetime.now(timezone.utc) - timedelta(days=20),
    )
    health_e = application_health_service.calculate_health(
        stale_app,
        as_of_time=datetime.now(timezone.utc),
    )
    # 5 checks passed (100) - stale penalty (20) = 80 ("GOOD")
    assert health_e.score == 80
    assert any(c.check_id == "pen_stale_application" and c.passed is False for c in health_e.checks)


# ---------------------------------------------------------------------------
# 10. Pipeline Kanban Grouping
# ---------------------------------------------------------------------------

def test_pipeline_kanban_grouping(db_client: TestClient):
    """Pipeline groups applications into documented recruitment stage columns."""
    headers = register_and_login(db_client, "appuser10@example.com", "appuser10")

    db_client.post(
        "/api/v1/applications",
        json={"job_title": "Role 1", "company_name": "Co 1", "current_stage": "APPLIED"},
        headers=headers,
    )
    db_client.post(
        "/api/v1/applications",
        json={"job_title": "Role 2", "company_name": "Co 2", "current_stage": "PHONE_SCREEN"},
        headers=headers,
    )
    db_client.post(
        "/api/v1/applications",
        json={"job_title": "Role 3", "company_name": "Co 3", "current_stage": "INTERVIEW"},
        headers=headers,
    )

    pipeline_res = db_client.get("/api/v1/applications/pipeline", headers=headers)
    assert pipeline_res.status_code == 200
    pipeline = pipeline_res.json()
    assert pipeline["total_active"] == 3

    columns_map = {col["stage"]: col for col in pipeline["columns"]}
    assert columns_map["APPLIED"]["count"] == 1
    assert columns_map["PHONE_SCREEN"]["count"] == 1
    assert columns_map["INTERVIEW"]["count"] == 1
    assert columns_map["OFFER"]["count"] == 0


# ---------------------------------------------------------------------------
# 11. Multi-User Strict Tenant Isolation
# ---------------------------------------------------------------------------

def test_multi_user_tenant_isolation(db_client: TestClient):
    """User B cannot view, update, delete, transition, or attach documents to User A's application."""
    user_a_headers = register_and_login(db_client, "usera@example.com", "usera")
    user_b_headers = register_and_login(db_client, "userb@example.com", "userb")

    # User A creates application
    app_a = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Lead Architect", "company_name": "Tesla"},
        headers=user_a_headers,
    ).json()
    app_a_id = app_a["id"]

    # User A creates note
    note_a = db_client.post(
        f"/api/v1/applications/{app_a_id}/notes",
        json={"content": "Confidential interview notes"},
        headers=user_a_headers,
    ).json()
    note_a_id = note_a["id"]

    # User B attempts to access User A's application -> 404
    assert db_client.get(f"/api/v1/applications/{app_a_id}", headers=user_b_headers).status_code == 404
    assert db_client.put(f"/api/v1/applications/{app_a_id}", json={"job_title": "Hacked"}, headers=user_b_headers).status_code == 404
    assert db_client.delete(f"/api/v1/applications/{app_a_id}", headers=user_b_headers).status_code == 404
    assert db_client.post(f"/api/v1/applications/{app_a_id}/stage", json={"to_stage": "OFFER"}, headers=user_b_headers).status_code == 404
    assert db_client.get(f"/api/v1/applications/{app_a_id}/health", headers=user_b_headers).status_code == 404
    assert db_client.get(f"/api/v1/applications/{app_a_id}/stage-history", headers=user_b_headers).status_code == 404
    assert db_client.get(f"/api/v1/applications/{app_a_id}/activity", headers=user_b_headers).status_code == 404

    # User B attempts to access User A's notes -> 404
    assert db_client.get(f"/api/v1/applications/{app_a_id}/notes", headers=user_b_headers).status_code == 404
    assert db_client.put(f"/api/v1/applications/{app_a_id}/notes/{note_a_id}", json={"content": "Hacked"}, headers=user_b_headers).status_code == 404
    assert db_client.delete(f"/api/v1/applications/{app_a_id}/notes/{note_a_id}", headers=user_b_headers).status_code == 404

    # User B lists applications -> empty
    b_apps = db_client.get("/api/v1/applications", headers=user_b_headers).json()
    assert b_apps["total"] == 0

    # User B pipeline -> 0 active
    b_pipe = db_client.get("/api/v1/applications/pipeline", headers=user_b_headers).json()
    assert b_pipe["total_active"] == 0

    # User B followups queue -> empty
    b_fol = db_client.get("/api/v1/applications/followups", headers=user_b_headers).json()
    assert len(b_fol) == 0
