"""
Stage 6 Master Test Suite — Network & Professional Contacts.
Covers:
- Unauthenticated rejection (401)
- Valid and invalid contact creation
- Contact retrieval, update, and deletion
- Server-side multi-field search (name, email, role, company)
- Filtering by contact_type and company_id
- Pagination and sorting
- Company CRUD & intelligent name-based de-duplication
- Contact-Company association
- Contact-Application linking, unlinking, and linked_applications reporting
- Multi-user strict tenant isolation (cross-user attempts return 404)
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


# ---------------------------------------------------------------------------
# 1. Unauthenticated Rejection
# ---------------------------------------------------------------------------

def test_unauthenticated_contacts_and_companies_rejected(db_client: TestClient):
    """All contact and company endpoints must reject unauthenticated requests with 401."""
    dummy_id = str(uuid.uuid4())
    # Contacts
    assert db_client.get("/api/v1/contacts").status_code == 401
    assert db_client.get("/api/v1/network/contacts").status_code == 401
    assert db_client.post("/api/v1/contacts", json={"first_name": "John"}).status_code == 401
    assert db_client.get(f"/api/v1/contacts/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/contacts/{dummy_id}", json={"first_name": "John"}).status_code == 401
    assert db_client.delete(f"/api/v1/contacts/{dummy_id}").status_code == 401
    # Companies
    assert db_client.get("/api/v1/companies").status_code == 401
    assert db_client.post("/api/v1/companies", json={"name": "Stripe"}).status_code == 401
    assert db_client.get(f"/api/v1/companies/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/companies/{dummy_id}", json={"name": "Stripe"}).status_code == 401
    assert db_client.delete(f"/api/v1/companies/{dummy_id}").status_code == 401


# ---------------------------------------------------------------------------
# 2. Contact CRUD & Validation
# ---------------------------------------------------------------------------

def test_contact_creation_valid(db_client: TestClient):
    """Authenticated candidate can create a contact with all valid fields."""
    headers = register_and_login(db_client, "contact_user1@example.com", "contact_user1")

    payload = {
        "first_name": "Elena",
        "last_name": "Rostova",
        "role": "Engineering Manager",
        "contact_type": "HIRING_MANAGER",
        "email": "elena.rostova@techcorp.io",
        "phone": "+1-415-555-0199",
        "linkedin_url": "https://linkedin.com/in/elenarostova",
        "relationship": "Lead Interviewer for Backend Systems",
        "notes": "Discussed system design trade-offs in second round.",
    }

    res = db_client.post("/api/v1/contacts", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Elena"
    assert data["last_name"] == "Rostova"
    assert data["role"] == "Engineering Manager"
    assert data["contact_type"] == "HIRING_MANAGER"
    assert data["email"] == "elena.rostova@techcorp.io"
    assert data["phone"] == "+1-415-555-0199"
    assert data["linkedin_url"] == "https://linkedin.com/in/elenarostova"
    assert data["relationship"] == "Lead Interviewer for Backend Systems"
    assert data["notes"] == "Discussed system design trade-offs in second round."
    assert "id" in data
    assert "created_at" in data

    # Verify reachable via /network/contacts as well
    net_res = db_client.get(f"/api/v1/network/contacts/{data['id']}", headers=headers)
    assert net_res.status_code == 200
    assert net_res.json()["first_name"] == "Elena"


def test_contact_creation_validation(db_client: TestClient):
    """Contact creation validates empty names, invalid email formats, and dangerous URLs."""
    headers = register_and_login(db_client, "contact_val@example.com", "contact_val")

    # Empty first name
    res = db_client.post("/api/v1/contacts", json={"first_name": "   "}, headers=headers)
    assert res.status_code == 422

    # Invalid email pattern
    res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "David", "email": "not-a-valid-email"},
        headers=headers,
    )
    assert res.status_code == 422

    # Dangerous URL scheme (javascript:)
    res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "David", "linkedin_url": "javascript:alert('xss')"},
        headers=headers,
    )
    assert res.status_code == 422

    # Invalid contact type
    res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "David", "contact_type": "SUPER_HERO"},
        headers=headers,
    )
    assert res.status_code == 422


def test_contact_get_and_not_found(db_client: TestClient):
    """Retrieving contact details by ID returns 200, non-existent returns 404."""
    headers = register_and_login(db_client, "contact_get@example.com", "contact_get")

    create_res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Marcus", "role": "Senior Recruiter"},
        headers=headers,
    )
    contact_id = create_res.json()["id"]

    res = db_client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["first_name"] == "Marcus"
    assert "linked_applications" in res.json()

    # Non-existent UUID
    fake_id = str(uuid.uuid4())
    res404 = db_client.get(f"/api/v1/contacts/{fake_id}", headers=headers)
    assert res404.status_code == 404


def test_contact_update(db_client: TestClient):
    """Candidate can update contact fields and notes."""
    headers = register_and_login(db_client, "contact_upd@example.com", "contact_upd")

    create_res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Marcus", "role": "Recruiter"},
        headers=headers,
    )
    contact_id = create_res.json()["id"]

    update_payload = {
        "first_name": "Marcus",
        "last_name": "Vance",
        "role": "Director of Talent Acquisition",
        "contact_type": "RECRUITER",
        "phone": "+1-650-555-0100",
        "notes": "Promoted to Director; prefers messages on Tuesday mornings.",
    }
    upd_res = db_client.put(f"/api/v1/contacts/{contact_id}", json=update_payload, headers=headers)
    assert upd_res.status_code == 200
    data = upd_res.json()
    assert data["last_name"] == "Vance"
    assert data["role"] == "Director of Talent Acquisition"
    assert data["phone"] == "+1-650-555-0100"
    assert "Promoted to Director" in data["notes"]


def test_contact_delete(db_client: TestClient):
    """Candidate can delete contact; subsequent access returns 404."""
    headers = register_and_login(db_client, "contact_del@example.com", "contact_del")

    create_res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Temp", "last_name": "Contact"},
        headers=headers,
    )
    contact_id = create_res.json()["id"]

    del_res = db_client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert del_res.status_code == 200

    get_res = db_client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert get_res.status_code == 404


# ---------------------------------------------------------------------------
# 3. Server-side Search, Filtering, and Pagination
# ---------------------------------------------------------------------------

def test_contact_search_server_side(db_client: TestClient):
    """Search matches first name, last name, role, email, and company name."""
    headers = register_and_login(db_client, "contact_srch@example.com", "contact_srch")

    # Create company
    comp_res = db_client.post("/api/v1/companies", json={"name": "Stripe Payments"}, headers=headers)
    stripe_id = comp_res.json()["id"]

    db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Patrick", "last_name": "Collison", "role": "CEO", "email": "p@stripe.com", "company_id": stripe_id},
        headers=headers,
    )
    db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Sarah", "last_name": "Connor", "role": "Security Architect", "email": "sarah@resistance.org"},
        headers=headers,
    )

    # Search by first name
    res = db_client.get("/api/v1/contacts?search=patrick", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["first_name"] == "Patrick"

    # Search by role
    res_role = db_client.get("/api/v1/contacts?search=Security", headers=headers)
    assert len(res_role.json()["items"]) == 1
    assert res_role.json()["items"][0]["first_name"] == "Sarah"

    # Search by company name
    res_comp = db_client.get("/api/v1/contacts?search=Stripe", headers=headers)
    assert len(res_comp.json()["items"]) == 1
    assert res_comp.json()["items"][0]["first_name"] == "Patrick"


def test_contact_filtering_by_type_and_company(db_client: TestClient):
    """Filters by contact_type and company_id compose deterministically."""
    headers = register_and_login(db_client, "contact_fltr@example.com", "contact_fltr")

    comp1 = db_client.post("/api/v1/companies", json={"name": "Alpha Corp"}, headers=headers).json()["id"]
    comp2 = db_client.post("/api/v1/companies", json={"name": "Beta LLC"}, headers=headers).json()["id"]

    db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Alice", "contact_type": "RECRUITER", "company_id": comp1},
        headers=headers,
    )
    db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Bob", "contact_type": "HIRING_MANAGER", "company_id": comp1},
        headers=headers,
    )
    db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Charlie", "contact_type": "REFERRAL", "company_id": comp2},
        headers=headers,
    )

    # Filter by contact_type
    rec_res = db_client.get("/api/v1/contacts?contact_type=RECRUITER", headers=headers)
    assert len(rec_res.json()["items"]) == 1
    assert rec_res.json()["items"][0]["first_name"] == "Alice"

    # Filter by company_id
    comp1_res = db_client.get(f"/api/v1/contacts?company_id={comp1}", headers=headers)
    assert len(comp1_res.json()["items"]) == 2

    # Combined filter
    comb_res = db_client.get(f"/api/v1/contacts?company_id={comp1}&contact_type=HIRING_MANAGER", headers=headers)
    assert len(comb_res.json()["items"]) == 1
    assert comb_res.json()["items"][0]["first_name"] == "Bob"


def test_contact_pagination_and_sorting(db_client: TestClient):
    """Pagination and sorting return paginated slice and total counts."""
    headers = register_and_login(db_client, "contact_page@example.com", "contact_page")

    for i in range(5):
        db_client.post(
            "/api/v1/contacts",
            json={"first_name": f"Contact_{i:02d}", "role": f"Engineer {i}"},
            headers=headers,
        )

    res = db_client.get("/api/v1/contacts?page=1&page_size=2&sort_by=first_name&sort_order=asc", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3
    assert len(data["items"]) == 2
    assert data["items"][0]["first_name"] == "Contact_00"
    assert data["items"][1]["first_name"] == "Contact_01"


# ---------------------------------------------------------------------------
# 4. Company CRUD & Name-Based De-Duplication
# ---------------------------------------------------------------------------

def test_company_crud_and_deduplication(db_client: TestClient):
    """Company CRUD operates smoothly and reuses existing records when matching by name."""
    headers = register_and_login(db_client, "company_test@example.com", "company_test")

    # Create company
    c_res = db_client.post(
        "/api/v1/companies",
        json={"name": "Vercel", "website": "https://vercel.com", "industry": "Cloud Infrastructure", "size": "MEDIUM"},
        headers=headers,
    )
    assert c_res.status_code == 201
    vercel_id = c_res.json()["id"]

    # Re-post same company name (case-insensitive) -> should reuse existing record without creating duplicate
    c_dup = db_client.post(
        "/api/v1/companies",
        json={"name": "vercel", "location": "San Francisco, CA"},
        headers=headers,
    )
    assert c_dup.status_code == 201
    assert c_dup.json()["id"] == vercel_id  # Reused same ID!
    assert c_dup.json()["location"] == "San Francisco, CA"

    # List companies -> count should still be 1
    list_res = db_client.get("/api/v1/companies", headers=headers)
    assert list_res.json()["total"] == 1

    # Update company
    upd_res = db_client.put(f"/api/v1/companies/{vercel_id}", json={"industry": "Developer Tools"}, headers=headers)
    assert upd_res.status_code == 200
    assert upd_res.json()["industry"] == "Developer Tools"

    # Delete company
    del_res = db_client.delete(f"/api/v1/companies/{vercel_id}", headers=headers)
    assert del_res.status_code == 200
    assert db_client.get(f"/api/v1/companies/{vercel_id}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# 5. Contact ↔ Application Linking & Health Engine Integration
# ---------------------------------------------------------------------------

def test_contact_application_linking_and_unlinking(db_client: TestClient):
    """
    Test linking a contact to an application:
    - Application creation/update accepts contact_id
    - Application detail returns contact summary
    - Health Engine suggestion turns green
    - Contact detail lists linked applications
    - Unlinking removes association cleanly
    """
    headers = register_and_login(db_client, "link_test@example.com", "link_test")

    # 1. Create contact
    c_res = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "Rachel", "last_name": "Zane", "role": "Senior Recruiter", "email": "rachel@pearson.law"},
        headers=headers,
    )
    contact_id = c_res.json()["id"]

    # 2. Create application linked to contact
    app_res = db_client.post(
        "/api/v1/applications",
        json={
            "job_title": "Associate Counsel",
            "company_name": "Pearson Hardman",
            "contact_id": contact_id,
            "current_stage": "INTERVIEW",
        },
        headers=headers,
    )
    assert app_res.status_code == 201
    app_data = app_res.json()
    app_id = app_data["id"]
    assert app_data["contact_id"] == contact_id
    assert app_data["contact"]["first_name"] == "Rachel"

    # 3. Check health score: sug_contact_linked should pass
    health_res = db_client.get(f"/api/v1/applications/{app_id}/health", headers=headers)
    checks = {c["check_id"]: c for c in health_res.json()["checks"]}
    assert checks["sug_contact_linked"]["passed"] is True

    # 4. Check contact details: linked_applications should include this application
    contact_detail_res = db_client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert contact_detail_res.status_code == 200
    linked_apps = contact_detail_res.json()["linked_applications"]
    assert len(linked_apps) == 1
    assert linked_apps[0]["id"] == app_id
    assert linked_apps[0]["job_title"] == "Associate Counsel"

    # 5. Unlink contact via application update
    un_res = db_client.put(f"/api/v1/applications/{app_id}", json={"contact_id": None}, headers=headers)
    assert un_res.status_code == 200
    assert un_res.json()["contact_id"] is None
    assert un_res.json()["contact"] is None

    # Verify contact details now has 0 linked applications
    updated_contact_res = db_client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert len(updated_contact_res.json()["linked_applications"]) == 0


# ---------------------------------------------------------------------------
# 6. Multi-User Strict Tenant Isolation
# ---------------------------------------------------------------------------

def test_multi_user_tenant_isolation_contacts_and_companies(db_client: TestClient):
    """
    Strict tenant isolation:
    - User B cannot read, update, or delete User A's contacts (HTTP 404)
    - User B cannot read, update, or delete User A's companies (HTTP 404)
    - User B cannot associate their contact with User A's company (HTTP 404)
    - User B cannot associate their application with User A's contact (HTTP 404)
    """
    user_a_headers = register_and_login(db_client, "user_a_net@example.com", "user_a_net")
    user_b_headers = register_and_login(db_client, "user_b_net@example.com", "user_b_net")

    # User A creates Company and Contact
    comp_a = db_client.post(
        "/api/v1/companies",
        json={"name": "User A Private Company"},
        headers=user_a_headers,
    ).json()["id"]

    contact_a = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "PrivateContactA", "company_id": comp_a},
        headers=user_a_headers,
    ).json()["id"]

    # 1. User B cannot access User A's Contact
    assert db_client.get(f"/api/v1/contacts/{contact_a}", headers=user_b_headers).status_code == 404
    assert db_client.put(f"/api/v1/contacts/{contact_a}", json={"first_name": "Hacked"}, headers=user_b_headers).status_code == 404
    assert db_client.delete(f"/api/v1/contacts/{contact_a}", headers=user_b_headers).status_code == 404

    # 2. User B cannot access User A's Company
    assert db_client.get(f"/api/v1/companies/{comp_a}", headers=user_b_headers).status_code == 404
    assert db_client.put(f"/api/v1/companies/{comp_a}", json={"name": "Hacked Co"}, headers=user_b_headers).status_code == 404
    assert db_client.delete(f"/api/v1/companies/{comp_a}", headers=user_b_headers).status_code == 404

    # 3. User B cannot attach User A's Company to their contact
    res_illegal_comp = db_client.post(
        "/api/v1/contacts",
        json={"first_name": "UserBContact", "company_id": comp_a},
        headers=user_b_headers,
    )
    assert res_illegal_comp.status_code == 404

    # 4. User B cannot attach User A's Contact to their application
    res_illegal_app = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Engineer", "company_name": "Acme", "contact_id": contact_a},
        headers=user_b_headers,
    )
    assert res_illegal_app.status_code == 404

    # 5. User B contact list does not leak User A's contact
    b_list = db_client.get("/api/v1/contacts", headers=user_b_headers).json()
    assert b_list["total"] == 0
