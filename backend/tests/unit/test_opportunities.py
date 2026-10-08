"""
Stage 4 Opportunities Unit & API Integration Tests:
Creation, Validation, URL Security, Retrieval, Update, Delete, Filtering,
Pagination, Saved Queue, Idempotency, and Strict Multi-Tenant Isolation.
"""

import uuid
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


def test_unauthenticated_opportunities_rejected(db_client: TestClient):
    """All opportunity endpoints must reject unauthenticated requests with 401."""
    dummy_id = str(uuid.uuid4())
    assert db_client.get("/api/v1/opportunities").status_code == 401
    assert db_client.post("/api/v1/opportunities", json={"title": "Test"}).status_code == 401
    assert db_client.get(f"/api/v1/opportunities/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/opportunities/{dummy_id}", json={"title": "Test"}).status_code == 401
    assert db_client.delete(f"/api/v1/opportunities/{dummy_id}").status_code == 401
    assert db_client.post(f"/api/v1/opportunities/{dummy_id}/save").status_code == 401
    assert db_client.delete(f"/api/v1/opportunities/{dummy_id}/save").status_code == 401
    assert db_client.get("/api/v1/opportunities/saved").status_code == 401


def test_opportunity_creation_valid(db_client: TestClient):
    """Create a new opportunity with all valid fields."""
    headers = register_and_login(db_client, "oppuser1@example.com", "oppuser1")

    payload = {
        "title": "Senior Cloud Engineer",
        "company_name": "Datadog",
        "source": "MANUAL",
        "source_url": "https://careers.datadoghq.com/detail/12345",
        "location": "San Francisco, CA",
        "location_type": "HYBRID",
        "employment_type": "FULL_TIME",
        "description": "Lead cloud platform engineering initiatives.",
        "requirements": "5+ years of AWS/Kubernetes experience.",
        "compensation_min": 180000.00,
        "compensation_max": 220000.00,
        "compensation_currency": "USD",
        "posted_date": "2026-09-01",
        "expiry_date": "2026-10-01",
        "status": "ACTIVE",
        "notes": "Referred by Alex from engineering.",
    }

    res = db_client.post("/api/v1/opportunities", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Senior Cloud Engineer"
    assert data["company_name"] == "Datadog"
    assert data["location_type"] == "HYBRID"
    assert data["employment_type"] == "FULL_TIME"
    assert float(data["compensation_min"]) == 180000.00
    assert float(data["compensation_max"]) == 220000.00
    assert data["is_saved"] is False
    assert "id" in data
    assert "user_id" in data


def test_opportunity_creation_validation(db_client: TestClient):
    """Verify validation rules: empty title, unsafe URLs, compensation ranges, date orders, invalid statuses."""
    headers = register_and_login(db_client, "oppval@example.com", "oppval")

    # Empty title
    res = db_client.post("/api/v1/opportunities", json={"title": "   "}, headers=headers)
    assert res.status_code == 422

    # Unsafe javascript: URL scheme
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Valid Title", "source_url": "javascript:alert('xss')"},
        headers=headers,
    )
    assert res.status_code == 422

    # Unsafe data: URL scheme
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Valid Title", "source_url": "data:text/html,<script>alert(1)</script>"},
        headers=headers,
    )
    assert res.status_code == 422

    # Unsafe file: URL scheme
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Valid Title", "source_url": "file:///etc/passwd"},
        headers=headers,
    )
    assert res.status_code == 422

    # Valid https URL scheme succeeds
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Valid Title", "source_url": "https://company.com/job/1"},
        headers=headers,
    )
    assert res.status_code == 201

    # Invalid status
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Role", "status": "UNKNOWN_STATUS"},
        headers=headers,
    )
    assert res.status_code == 422

    # compensation_min > compensation_max
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Role", "compensation_min": 250000, "compensation_max": 200000},
        headers=headers,
    )
    assert res.status_code == 422

    # posted_date > expiry_date
    res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Role", "posted_date": "2026-10-01", "expiry_date": "2026-09-01"},
        headers=headers,
    )
    assert res.status_code == 422


def test_opportunity_get_and_not_found(db_client: TestClient):
    """Retrieve an opportunity and verify 404 for missing IDs."""
    headers = register_and_login(db_client, "oppget@example.com", "oppget")

    create_res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Staff Engineer", "company_name": "Stripe"},
        headers=headers,
    )
    opp_id = create_res.json()["id"]

    res = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Staff Engineer"

    # Non-existent UUID
    fake_id = str(uuid.uuid4())
    res_fake = db_client.get(f"/api/v1/opportunities/{fake_id}", headers=headers)
    assert res_fake.status_code == 404


def test_opportunity_update(db_client: TestClient):
    """Update opportunity details and status."""
    headers = register_and_login(db_client, "oppupdate@example.com", "oppupdate")

    create_res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Junior Dev", "status": "ACTIVE", "location": "Austin, TX"},
        headers=headers,
    )
    opp_id = create_res.json()["id"]

    update_payload = {
        "title": "Intermediate Dev",
        "status": "CONSIDERING",
        "location": "Remote",
        "notes": "Had preliminary recruiter chat.",
    }
    update_res = db_client.put(
        f"/api/v1/opportunities/{opp_id}",
        json=update_payload,
        headers=headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "Intermediate Dev"
    assert data["status"] == "CONSIDERING"
    assert data["location"] == "Remote"
    assert data["notes"] == "Had preliminary recruiter chat."


def test_opportunity_delete(db_client: TestClient):
    """Delete an opportunity and verify it is no longer retrievable."""
    headers = register_and_login(db_client, "oppdel@example.com", "oppdel")

    create_res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Ephemeral Role"},
        headers=headers,
    )
    opp_id = create_res.json()["id"]

    del_res = db_client.delete(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Opportunity deleted successfully"

    get_res = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert get_res.status_code == 404


def test_opportunity_search_filtering_and_pagination(db_client: TestClient):
    """Test keyword search, filters (status, location_type, employment_type), and pagination."""
    headers = register_and_login(db_client, "oppsearch@example.com", "oppsearch")

    # Create 3 distinct opportunities
    db_client.post(
        "/api/v1/opportunities",
        json={
            "title": "Backend Architect",
            "company_name": "Cloudflare",
            "location_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "status": "ACTIVE",
            "description": "Distributed Rust and Go microservices.",
        },
        headers=headers,
    )
    db_client.post(
        "/api/v1/opportunities",
        json={
            "title": "Frontend Lead",
            "company_name": "Vercel",
            "location_type": "HYBRID",
            "employment_type": "FULL_TIME",
            "status": "CONSIDERING",
            "description": "Next.js ecosystem and React compiler.",
        },
        headers=headers,
    )
    db_client.post(
        "/api/v1/opportunities",
        json={
            "title": "Site Reliability Intern",
            "company_name": "Cloudflare",
            "location_type": "ON_SITE",
            "employment_type": "INTERNSHIP",
            "status": "ARCHIVED",
            "description": "Observability and alerting systems.",
        },
        headers=headers,
    )

    # Search keyword matching title
    res = db_client.get("/api/v1/opportunities?search=Architect", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Backend Architect"

    # Search keyword matching company
    res = db_client.get("/api/v1/opportunities?search=Cloudflare", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # Filter by status
    res = db_client.get("/api/v1/opportunities?status=CONSIDERING", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "Frontend Lead"

    # Filter by location_type
    res = db_client.get("/api/v1/opportunities?location_type=REMOTE", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # Filter by employment_type
    res = db_client.get("/api/v1/opportunities?employment_type=INTERNSHIP", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # Pagination test
    res = db_client.get("/api/v1/opportunities?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    paged_data = res.json()
    assert paged_data["total"] == 3
    assert len(paged_data["items"]) == 2
    assert paged_data["total_pages"] == 2


def test_saved_opportunity_lifecycle_and_idempotency(db_client: TestClient):
    """Test saving, unsaving, duplicate save idempotency, and saved listing."""
    headers = register_and_login(db_client, "oppsaved@example.com", "oppsaved")

    create_res = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Principal Architect", "company_name": "Figma"},
        headers=headers,
    )
    opp_id = create_res.json()["id"]

    # Initially is_saved is False
    get_res = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert get_res.json()["is_saved"] is False

    # Save opportunity
    save_res = db_client.post(
        f"/api/v1/opportunities/{opp_id}/save",
        json={"notes": "High compensation target"},
        headers=headers,
    )
    assert save_res.status_code == 200
    saved_data = save_res.json()
    assert saved_data["opportunity_id"] == opp_id
    assert saved_data["notes"] == "High compensation target"
    assert saved_data["opportunity"]["is_saved"] is True

    # Now get_opportunity shows is_saved == True
    get_res = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert get_res.json()["is_saved"] is True

    # Repeated save call is idempotent (no error, doesn't duplicate)
    save_repeat = db_client.post(
        f"/api/v1/opportunities/{opp_id}/save",
        json={"notes": "Updated note"},
        headers=headers,
    )
    assert save_repeat.status_code == 200

    # List saved opportunities
    list_saved = db_client.get("/api/v1/opportunities/saved", headers=headers)
    assert list_saved.status_code == 200
    saved_list = list_saved.json()
    assert saved_list["total"] == 1
    assert saved_list["items"][0]["opportunity_id"] == opp_id

    # Filter opportunities by is_saved=true
    filter_saved = db_client.get("/api/v1/opportunities?is_saved=true", headers=headers)
    assert filter_saved.status_code == 200
    assert filter_saved.json()["total"] == 1

    # Unsave opportunity
    unsave_res = db_client.delete(f"/api/v1/opportunities/{opp_id}/save", headers=headers)
    assert unsave_res.status_code == 200
    assert unsave_res.json()["message"] == "Opportunity unsaved successfully"

    # Now is_saved is False
    get_res2 = db_client.get(f"/api/v1/opportunities/{opp_id}", headers=headers)
    assert get_res2.json()["is_saved"] is False

    # Saved queue is now empty
    list_saved2 = db_client.get("/api/v1/opportunities/saved", headers=headers)
    assert list_saved2.json()["total"] == 0

    # Repeated unsave is idempotent
    unsave_repeat = db_client.delete(f"/api/v1/opportunities/{opp_id}/save", headers=headers)
    assert unsave_repeat.status_code == 200


def test_opportunity_tenant_isolation(db_client: TestClient):
    """
    CRITICAL SECURITY CHECK:
    Verify strict tenant isolation between User A and User B.
    User B must NEVER be able to read, update, delete, save, or unsave User A's opportunities.
    All cross-tenant access attempts must return 404 (preventing enumeration/information leakage).
    """
    headers_a = register_and_login(db_client, "usera_opp@example.com", "usera_opp")
    headers_b = register_and_login(db_client, "userb_opp@example.com", "userb_opp")

    # User A creates an opportunity and saves it
    res_a = db_client.post(
        "/api/v1/opportunities",
        json={"title": "Confidential Executive Role", "company_name": "Stealth AI"},
        headers=headers_a,
    )
    assert res_a.status_code == 201
    opp_a_id = res_a.json()["id"]

    db_client.post(f"/api/v1/opportunities/{opp_a_id}/save", headers=headers_a)

    # User B attempts GET on User A's opportunity -> 404
    assert db_client.get(f"/api/v1/opportunities/{opp_a_id}", headers=headers_b).status_code == 404

    # User B attempts PUT on User A's opportunity -> 404
    assert db_client.put(
        f"/api/v1/opportunities/{opp_a_id}",
        json={"title": "Hacked Title"},
        headers=headers_b,
    ).status_code == 404

    # User B attempts DELETE on User A's opportunity -> 404
    assert db_client.delete(f"/api/v1/opportunities/{opp_a_id}", headers=headers_b).status_code == 404

    # User B attempts to save User A's opportunity -> 404
    assert db_client.post(f"/api/v1/opportunities/{opp_a_id}/save", headers=headers_b).status_code == 404

    # User B attempts to unsave User A's opportunity -> 404
    assert db_client.delete(f"/api/v1/opportunities/{opp_a_id}/save", headers=headers_b).status_code == 404

    # User B's opportunity list does not contain User A's opportunity
    list_b = db_client.get("/api/v1/opportunities", headers=headers_b).json()
    assert list_b["total"] == 0

    # User B's saved list does not contain User A's saved opportunity
    saved_b = db_client.get("/api/v1/opportunities/saved", headers=headers_b).json()
    assert saved_b["total"] == 0

    # Confirm User A's opportunity was not modified by User B's attempts
    res_a_check = db_client.get(f"/api/v1/opportunities/{opp_a_id}", headers=headers_a)
    assert res_a_check.status_code == 200
    assert res_a_check.json()["title"] == "Confidential Executive Role"
    assert res_a_check.json()["is_saved"] is True
