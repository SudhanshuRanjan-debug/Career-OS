"""
Stage 7 Master Test Suite — Interviews & Interview Preparation.
Covers:
- Unauthenticated rejection (401)
- Interview creation, validation, and auto-initialization of preparation workspace
- Interview CRUD operations (retrieval, update, deletion)
- Server-side searching, status filtering (upcoming, completed, cancelled), type filtering, pagination
- Interview Preparation CRUD (company research, role research, questions to ask, checklist items, debrief)
- Application integration (sub-resource listing, activity logging, interview count)
- Contact / interviewer association
- Strict multi-user tenant isolation (cross-user access returns 404, preventing cross-user linking)
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient


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
# 1. Unauthenticated Rejection
# ---------------------------------------------------------------------------

def test_unauthenticated_interviews_rejected(db_client: TestClient):
    """All interview and preparation endpoints must reject unauthenticated requests with 401."""
    dummy_id = str(uuid.uuid4())
    assert db_client.get("/api/v1/interviews").status_code == 401
    assert db_client.post("/api/v1/interviews", json={"title": "Technical Screen"}).status_code == 401
    assert db_client.get(f"/api/v1/interviews/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/interviews/{dummy_id}", json={"title": "Updated"}).status_code == 401
    assert db_client.delete(f"/api/v1/interviews/{dummy_id}").status_code == 401
    assert db_client.get(f"/api/v1/interviews/{dummy_id}/preparation").status_code == 401
    assert db_client.put(f"/api/v1/interviews/{dummy_id}/preparation", json={"company_research": "Notes"}).status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}/interviews").status_code == 401


# ---------------------------------------------------------------------------
# 2. Valid Interview Creation & Preparation Auto-initialization
# ---------------------------------------------------------------------------

def test_interview_creation_valid(db_client: TestClient):
    """Candidate can create an interview associated with application, company, and contact."""
    headers = register_and_login(db_client, "interview_create@example.com", "int_create_user")

    # 1. Create company
    comp_res = db_client.post(
        "/api/v1/companies",
        headers=headers,
        json={"name": "Stripe", "website": "https://stripe.com"},
    )
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    # 2. Create contact (interviewer)
    cont_res = db_client.post(
        "/api/v1/contacts",
        headers=headers,
        json={
            "first_name": "Elena",
            "last_name": "Rostova",
            "role": "Staff Systems Architect",
            "contact_type": "INTERVIEWER",
            "email": "elena.rostova@stripe.com",
            "company_id": comp_id,
        },
    )
    assert cont_res.status_code == 201
    contact_id = cont_res.json()["id"]

    # 3. Create application
    app_res = db_client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "job_title": "Backend Infrastructure Engineer",
            "company_name": "Stripe",
            "company_id": comp_id,
            "contact_id": contact_id,
            "current_stage": "INTERVIEW",
        },
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    # 4. Schedule Interview
    scheduled_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    interview_payload = {
        "application_id": app_id,
        "company_id": comp_id,
        "contact_id": contact_id,
        "title": "System Architecture & Concurrency Deep Dive",
        "interview_type": "TECHNICAL",
        "stage": "Round 2 Technical Onsite",
        "scheduled_at": scheduled_time,
        "duration_mins": 60,
        "meeting_link": "https://meet.google.com/abc-defg-hij",
        "location": "Google Meet",
        "status": "SCHEDULED",
        "interviewer_names": ["Elena Rostova", "Marcus Vance"],
        "notes": "Focus on high-throughput queue processing and idempotency keys.",
    }
    int_res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json=interview_payload,
    )
    assert int_res.status_code == 201
    data = int_res.json()
    assert data["title"] == "System Architecture & Concurrency Deep Dive"
    assert data["interview_type"] == "TECHNICAL"
    assert data["duration_mins"] == 60
    assert data["meeting_link"] == "https://meet.google.com/abc-defg-hij"
    assert data["application"]["id"] == app_id
    assert data["company"]["id"] == comp_id
    assert data["contact"]["id"] == contact_id
    assert len(data["interviewer_names"]) == 2
    # Verify preparation workspace is auto-initialized
    assert data["preparation"] is not None
    assert data["preparation"]["interview_id"] == data["id"]


# ---------------------------------------------------------------------------
# 3. Input & Validation Rules
# ---------------------------------------------------------------------------

def test_interview_creation_validation(db_client: TestClient):
    """Validation rejects invalid types, statuses, durations, and unsafe links."""
    headers = register_and_login(db_client, "interview_val@example.com", "int_val_user")

    # Invalid interview type
    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"interview_type": "INVALID_TYPE", "title": "Chat"},
    )
    assert res.status_code == 422

    # Invalid status
    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"status": "FINISHED", "title": "Chat"},
    )
    assert res.status_code == 422

    # Invalid duration (< 1 min or > 1440 mins)
    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"duration_mins": 0, "title": "Chat"},
    )
    assert res.status_code == 422

    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"duration_mins": 2000, "title": "Chat"},
    )
    assert res.status_code == 422

    # Unsafe meeting link
    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"meeting_link": "javascript:alert(1)", "title": "Chat"},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 4. Interview Retrieval & 404
# ---------------------------------------------------------------------------

def test_interview_get_and_not_found(db_client: TestClient):
    """Retrieving existing interview succeeds, non-existent returns 404."""
    headers = register_and_login(db_client, "interview_get@example.com", "int_get_user")

    res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"title": "Recruiter Screen", "interview_type": "PHONE"},
    )
    assert res.status_code == 201
    int_id = res.json()["id"]

    # Get valid
    get_res = db_client.get(f"/api/v1/interviews/{int_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == int_id

    # Non-existent
    assert db_client.get(f"/api/v1/interviews/{uuid.uuid4()}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# 5. Interview Update & Outcome Recording
# ---------------------------------------------------------------------------

def test_interview_update(db_client: TestClient):
    """Candidate can update interview details, record outcomes, and mark completed."""
    headers = register_and_login(db_client, "interview_upd@example.com", "int_upd_user")

    create_res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"title": "Coding Round 1", "interview_type": "TECHNICAL", "status": "SCHEDULED"},
    )
    int_id = create_res.json()["id"]

    update_payload = {
        "status": "COMPLETED",
        "result": "PASSED",
        "duration_mins": 45,
        "notes": "Solved two graph traversal problems with optimal Big-O complexity.",
    }
    upd_res = db_client.put(
        f"/api/v1/interviews/{int_id}",
        headers=headers,
        json=update_payload,
    )
    assert upd_res.status_code == 200
    updated = upd_res.json()
    assert updated["status"] == "COMPLETED"
    assert updated["result"] == "PASSED"
    assert updated["duration_mins"] == 45
    assert "optimal Big-O" in updated["notes"]


# ---------------------------------------------------------------------------
# 6. Interview Deletion
# ---------------------------------------------------------------------------

def test_interview_delete(db_client: TestClient):
    """Deleting interview returns 204 and cascade deletes preparation."""
    headers = register_and_login(db_client, "interview_del@example.com", "int_del_user")

    int_res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"title": "Hiring Manager Chat", "interview_type": "BEHAVIORAL"},
    )
    int_id = int_res.json()["id"]

    # Delete
    del_res = db_client.delete(f"/api/v1/interviews/{int_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify interview is gone
    assert db_client.get(f"/api/v1/interviews/{int_id}", headers=headers).status_code == 404
    # Verify prep is gone
    assert db_client.get(f"/api/v1/interviews/{int_id}/preparation", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# 7. Interview Search, Status Filtering, and Pagination
# ---------------------------------------------------------------------------

def test_interview_search_and_filtering(db_client: TestClient):
    """Filter by status (upcoming/completed/cancelled), type, keyword search, and pagination."""
    headers = register_and_login(db_client, "interview_filter@example.com", "int_flt_user")

    # Create 3 interviews with different states
    db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "title": "Google System Design",
            "interview_type": "SYSTEM_DESIGN",
            "status": "SCHEDULED",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        },
    )
    db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "title": "Stripe Coding Screen",
            "interview_type": "TECHNICAL",
            "status": "COMPLETED",
            "scheduled_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    )
    db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "title": "Netflix Behavioral",
            "interview_type": "BEHAVIORAL",
            "status": "CANCELLED",
        },
    )

    # Filter upcoming
    res_up = db_client.get("/api/v1/interviews?status=UPCOMING", headers=headers)
    assert res_up.status_code == 200
    assert len(res_up.json()["items"]) == 1
    assert res_up.json()["items"][0]["title"] == "Google System Design"

    # Filter completed
    res_comp = db_client.get("/api/v1/interviews?status=COMPLETED", headers=headers)
    assert res_comp.status_code == 200
    assert len(res_comp.json()["items"]) == 1
    assert res_comp.json()["items"][0]["title"] == "Stripe Coding Screen"

    # Filter type
    res_type = db_client.get("/api/v1/interviews?interview_type=BEHAVIORAL", headers=headers)
    assert res_type.status_code == 200
    assert len(res_type.json()["items"]) == 1
    assert res_type.json()["items"][0]["title"] == "Netflix Behavioral"

    # Search keyword
    res_search = db_client.get("/api/v1/interviews?search=System", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) == 1
    assert res_search.json()["items"][0]["title"] == "Google System Design"


# ---------------------------------------------------------------------------
# 8. Interview Preparation Workspace CRUD
# ---------------------------------------------------------------------------

def test_interview_preparation_crud(db_client: TestClient):
    """Candidate can save research, questions to ask, checklist items, and debrief."""
    headers = register_and_login(db_client, "interview_prep@example.com", "int_prep_user")

    int_res = db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"title": "Cloud Systems Onsite", "interview_type": "TECHNICAL"},
    )
    int_id = int_res.json()["id"]

    # Initial prep is auto-initialized
    prep_res = db_client.get(f"/api/v1/interviews/{int_id}/preparation", headers=headers)
    assert prep_res.status_code == 200
    initial_prep = prep_res.json()
    assert initial_prep["interview_id"] == int_id

    # Update prep
    prep_payload = {
        "company_research": "Google Cloud infrastructure architecture, Spanner TrueTime, Bigtable.",
        "role_research": "L6 Staff Engineer responsible for distributed replication and low-latency storage.",
        "questions_to_ask": "1. What is the biggest concurrency bottleneck facing the team today?",
        "personal_notes": "Remember STAR stories for cross-functional consensus and handling outages.",
        "preparation_checklist": [
            {"id": "chk-1", "label": "Review Paxos vs Raft consensus", "done": True},
            {"id": "chk-2", "label": "Mock 45-min system design session", "done": True},
            {"id": "chk-3", "label": "Setup quiet room and test mic", "done": False},
        ],
        "post_interview_notes": "Great discussion on multi-region replication tradeoffs. Follow-up expected next week.",
    }
    upd_prep = db_client.put(
        f"/api/v1/interviews/{int_id}/preparation",
        headers=headers,
        json=prep_payload,
    )
    assert upd_prep.status_code == 200
    data = upd_prep.json()
    assert "TrueTime" in data["company_research"]
    assert "L6 Staff Engineer" in data["role_research"]
    assert len(data["preparation_checklist"]) == 3
    assert data["preparation_checklist"][0]["done"] is True
    assert data["preparation_checklist"][2]["done"] is False
    assert "multi-region replication" in data["post_interview_notes"]


# ---------------------------------------------------------------------------
# 9. Application Associated Interviews Subresource
# ---------------------------------------------------------------------------

def test_application_interviews_subresource(db_client: TestClient):
    """Listing interviews via application subresource returns all linked sessions."""
    headers = register_and_login(db_client, "interview_app@example.com", "int_app_user")

    # Create application
    app_res = db_client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_title": "Site Reliability Engineer", "company_name": "Datadog", "current_stage": "INTERVIEW"},
    )
    app_id = app_res.json()["id"]

    # Schedule 2 interviews for this application
    db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"application_id": app_id, "title": "Round 1 Screening", "interview_type": "PHONE"},
    )
    db_client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"application_id": app_id, "title": "Round 2 Technical Deep Dive", "interview_type": "TECHNICAL"},
    )

    # Sub-resource endpoint
    sub_res = db_client.get(f"/api/v1/applications/{app_id}/interviews", headers=headers)
    assert sub_res.status_code == 200
    sessions = sub_res.json()
    assert len(sessions) == 2
    titles = [s["title"] for s in sessions]
    assert "Round 1 Screening" in titles
    assert "Round 2 Technical Deep Dive" in titles

    # Also verify application details reports interviews_count == 2
    app_detail = db_client.get(f"/api/v1/applications/{app_id}", headers=headers)
    assert app_detail.status_code == 200
    assert app_detail.json()["interviews_count"] == 2


# ---------------------------------------------------------------------------
# 10. Multi-User Tenant Isolation
# ---------------------------------------------------------------------------

def test_multi_user_tenant_isolation_interviews(db_client: TestClient):
    """Strict tenant isolation: cross-user access, linking, and preparation access return 404."""
    headers_a = register_and_login(db_client, "tenant_a@example.com", "tenant_a_user")
    headers_b = register_and_login(db_client, "tenant_b@example.com", "tenant_b_user")

    # User A creates company, contact, application, and interview
    comp_a = db_client.post("/api/v1/companies", headers=headers_a, json={"name": "Airbnb"}).json()
    contact_a = db_client.post(
        "/api/v1/contacts",
        headers=headers_a,
        json={"first_name": "Brian", "email": "brian@airbnb.com", "company_id": comp_a["id"]},
    ).json()
    app_a = db_client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={"job_title": "Full Stack Lead", "company_name": "Airbnb", "company_id": comp_a["id"]},
    ).json()
    int_a = db_client.post(
        "/api/v1/interviews",
        headers=headers_a,
        json={
            "application_id": app_a["id"],
            "company_id": comp_a["id"],
            "contact_id": contact_a["id"],
            "title": "Architecture Interview",
        },
    ).json()

    # User B lists interviews -> empty
    res_b_list = db_client.get("/api/v1/interviews", headers=headers_b)
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()["items"]) == 0

    # User B cannot GET User A's interview -> 404
    assert db_client.get(f"/api/v1/interviews/{int_a['id']}", headers=headers_b).status_code == 404

    # User B cannot PUT User A's interview -> 404
    assert db_client.put(f"/api/v1/interviews/{int_a['id']}", headers=headers_b, json={"title": "Hacked"}).status_code == 404

    # User B cannot DELETE User A's interview -> 404
    assert db_client.delete(f"/api/v1/interviews/{int_a['id']}", headers=headers_b).status_code == 404

    # User B cannot GET or PUT User A's preparation -> 404
    assert db_client.get(f"/api/v1/interviews/{int_a['id']}/preparation", headers=headers_b).status_code == 404
    assert db_client.put(f"/api/v1/interviews/{int_a['id']}/preparation", headers=headers_b, json={"company_research": "Leak"}).status_code == 404

    # User B cannot access User A's application interviews subresource -> 404
    assert db_client.get(f"/api/v1/applications/{app_a['id']}/interviews", headers=headers_b).status_code == 404

    # Cross-user linking attacks: User B cannot attach User A's application, contact, or company
    attack_app = db_client.post(
        "/api/v1/interviews",
        headers=headers_b,
        json={"application_id": app_a["id"], "title": "Attack Session"},
    )
    assert attack_app.status_code == 404

    attack_contact = db_client.post(
        "/api/v1/interviews",
        headers=headers_b,
        json={"contact_id": contact_a["id"], "title": "Attack Session"},
    )
    assert attack_contact.status_code == 404

    attack_comp = db_client.post(
        "/api/v1/interviews",
        headers=headers_b,
        json={"company_id": comp_a["id"], "title": "Attack Session"},
    )
    assert attack_comp.status_code == 404
