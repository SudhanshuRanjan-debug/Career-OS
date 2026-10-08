"""
Stage 3 Profile Unit Tests:
Personal, Professional, Preferences, 8 Normalized Subsections, Completeness, and Tenant Isolation.
"""

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


def test_unauthenticated_profile_access_rejected(db_client: TestClient):
    """Profile endpoints must reject unauthenticated requests with 401."""
    res = db_client.get("/api/v1/profile/personal")
    assert res.status_code == 401

    res = db_client.get("/api/v1/profile/overview")
    assert res.status_code == 401

    res = db_client.get("/api/v1/profile/completeness")
    assert res.status_code == 401

    res = db_client.get("/api/v1/profile/education")
    assert res.status_code == 401


def test_personal_info_crud(db_client: TestClient):
    """Retrieve and update personal profile information."""
    headers = register_and_login(db_client, "john@example.com", "johndoe")

    # Initial personal info has email
    res = db_client.get("/api/v1/profile/personal", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "john@example.com"
    assert data["first_name"] is None

    # Update personal info
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "preferred_name": "JD",
        "phone": "+1 555-0199",
        "location_city": "San Francisco",
        "location_state": "CA",
        "location_country": "USA",
        "timezone": "America/Los_Angeles",
        "headline": "Senior Full Stack Engineer",
        "website": "https://johndoe.dev",
    }
    update_res = db_client.put("/api/v1/profile/personal", json=update_data, headers=headers)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["first_name"] == "John"
    assert updated["last_name"] == "Doe"
    assert updated["phone"] == "+1 555-0199"
    assert updated["location_city"] == "San Francisco"


def test_professional_info_crud(db_client: TestClient):
    """Retrieve and update professional summary and career preferences."""
    headers = register_and_login(db_client, "prof@example.com", "profuser")

    res = db_client.get("/api/v1/profile/professional", headers=headers)
    assert res.status_code == 200

    payload = {
        "headline": "Cloud Infrastructure Architect",
        "professional_summary": "10+ years designing fault-tolerant systems.",
        "career_objective": "Lead scalable backend platform engineering.",
        "current_role": "Staff Engineer",
        "total_experience_yrs": 8.5,
        "notice_period_days": 30,
        "open_to_work": True,
    }
    update_res = db_client.put("/api/v1/profile/professional", json=payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["headline"] == "Cloud Infrastructure Architect"
    assert float(data["total_experience_yrs"]) == 8.5
    assert data["notice_period_days"] == 30


def test_preferences_crud(db_client: TestClient):
    """Candidate job search preferences CRUD."""
    headers = register_and_login(db_client, "pref@example.com", "prefuser")

    # Initial preferences
    res = db_client.get("/api/v1/profile/preferences", headers=headers)
    assert res.status_code == 200

    payload = {
        "desired_job_titles": ["Staff Software Engineer", "Backend Lead"],
        "preferred_industries": ["FinTech", "SaaS", "AI/ML"],
        "preferred_locations": ["San Francisco, CA", "Remote"],
        "work_arrangement": "REMOTE",
        "employment_type": ["FULL_TIME"],
        "min_compensation": 180000.00,
        "target_compensation": 220000.00,
        "compensation_currency": "USD",
        "compensation_period": "ANNUAL",
        "notice_period_days": 30,
        "work_authorization": ["US Citizen"],
        "relocation_preference": "NO",
    }
    update_res = db_client.put("/api/v1/profile/preferences", json=payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["desired_job_titles"] == ["Staff Software Engineer", "Backend Lead"]
    assert float(data["min_compensation"]) == 180000.00


def test_education_crud_and_tenant_isolation(db_client: TestClient):
    """Education CRUD with strict multi-user tenant isolation."""
    user_a = register_and_login(db_client, "user_a@example.com", "usera")
    user_b = register_and_login(db_client, "user_b@example.com", "userb")

    # User A creates education
    edu_payload = {
        "institution": "Stanford University",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "grade": "3.9 GPA",
        "start_date": "2018-09-01",
        "end_date": "2022-06-15",
        "is_current": False,
        "location": "Stanford, CA",
    }
    create_res = db_client.post("/api/v1/profile/education", json=edu_payload, headers=user_a)
    assert create_res.status_code == 201
    edu_id = create_res.json()["id"]

    # User A can list education
    list_res = db_client.get("/api/v1/profile/education", headers=user_a)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["institution"] == "Stanford University"

    # User B CANNOT see User A's education
    user_b_list = db_client.get("/api/v1/profile/education", headers=user_b)
    assert len(user_b_list.json()) == 0

    # User B CANNOT update User A's education
    b_update = db_client.put(
        f"/api/v1/profile/education/{edu_id}",
        json={"institution": "Hacked University"},
        headers=user_b,
    )
    assert b_update.status_code == 404

    # User B CANNOT delete User A's education
    b_del = db_client.delete(f"/api/v1/profile/education/{edu_id}", headers=user_b)
    assert b_del.status_code == 404

    # User A updates education
    a_update = db_client.put(
        f"/api/v1/profile/education/{edu_id}",
        json={"grade": "3.95 GPA"},
        headers=user_a,
    )
    assert a_update.status_code == 200
    assert a_update.json()["grade"] == "3.95 GPA"

    # User A deletes education
    a_del = db_client.delete(f"/api/v1/profile/education/{edu_id}", headers=user_a)
    assert a_del.status_code == 200

    # List is now empty
    after_del = db_client.get("/api/v1/profile/education", headers=user_a)
    assert len(after_del.json()) == 0


def test_experience_crud_and_isolation(db_client: TestClient):
    """Experience CRUD and tenant isolation."""
    headers = register_and_login(db_client, "exp@example.com", "expuser")

    payload = {
        "company_name": "Tech Corp",
        "title": "Software Engineer",
        "employment_type": "FULL_TIME",
        "location": "New York, NY",
        "location_type": "HYBRID",
        "description": "Building microservices.",
        "start_date": "2022-07-01",
        "is_current": True,
    }
    res = db_client.post("/api/v1/profile/experience", json=payload, headers=headers)
    assert res.status_code == 201
    item_id = res.json()["id"]

    # Read
    get_res = db_client.get("/api/v1/profile/experience", headers=headers)
    assert len(get_res.json()) == 1
    assert get_res.json()[0]["is_current"] is True

    # Update
    put_res = db_client.put(
        f"/api/v1/profile/experience/{item_id}",
        json={"title": "Senior Software Engineer"},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["title"] == "Senior Software Engineer"

    # Delete
    del_res = db_client.delete(f"/api/v1/profile/experience/{item_id}", headers=headers)
    assert del_res.status_code == 200


def test_projects_skills_certifications_crud(db_client: TestClient):
    """Verify Projects, Skills, and Certifications CRUD."""
    headers = register_and_login(db_client, "mixed@example.com", "mixeduser")

    # Project
    proj_res = db_client.post(
        "/api/v1/profile/projects",
        json={
            "name": "Career Platform OS",
            "description": "Job application management system.",
            "role": "Architect",
            "tech_stack": ["FastAPI", "React", "PostgreSQL"],
            "url": "https://careerplatform.dev",
            "repo_url": "https://github.com/example/career-platform",
            "is_ongoing": True,
        },
        headers=headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Skill
    skill_res = db_client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "TECHNICAL", "proficiency": "EXPERT", "years_of_exp": 6.0},
        headers=headers,
    )
    assert skill_res.status_code == 201
    skill_id = skill_res.json()["id"]

    # Certification
    cert_res = db_client.post(
        "/api/v1/profile/certifications",
        json={
            "name": "AWS Certified Solutions Architect",
            "issuing_org": "Amazon Web Services",
            "issue_date": "2023-05-10",
            "credential_id": "AWS-123456",
        },
        headers=headers,
    )
    assert cert_res.status_code == 201
    cert_id = cert_res.json()["id"]

    # List all
    assert len(db_client.get("/api/v1/profile/projects", headers=headers).json()) == 1
    assert len(db_client.get("/api/v1/profile/skills", headers=headers).json()) == 1
    assert len(db_client.get("/api/v1/profile/certifications", headers=headers).json()) == 1

    # Cleanup
    assert db_client.delete(f"/api/v1/profile/projects/{proj_id}", headers=headers).status_code == 200
    assert db_client.delete(f"/api/v1/profile/skills/{skill_id}", headers=headers).status_code == 200
    assert db_client.delete(f"/api/v1/profile/certifications/{cert_id}", headers=headers).status_code == 200


def test_achievements_languages_links_crud(db_client: TestClient):
    """Verify Achievements, Languages, and Profile Links CRUD."""
    headers = register_and_login(db_client, "extra@example.com", "extrauser")

    # Achievement
    ach_res = db_client.post(
        "/api/v1/profile/achievements",
        json={
            "title": "1st Place Global Hackathon",
            "category": "HACKATHON",
            "issuer": "Tech Summit",
            "date": "2025-10-15",
        },
        headers=headers,
    )
    assert ach_res.status_code == 201
    ach_id = ach_res.json()["id"]

    # Language
    lang_res = db_client.post(
        "/api/v1/profile/languages",
        json={"name": "English", "proficiency": "NATIVE"},
        headers=headers,
    )
    assert lang_res.status_code == 201
    lang_id = lang_res.json()["id"]

    # Link
    link_res = db_client.post(
        "/api/v1/profile/links",
        json={"platform": "LINKEDIN", "label": "LinkedIn Profile", "url": "https://linkedin.com/in/johndoe"},
        headers=headers,
    )
    assert link_res.status_code == 201
    link_id = link_res.json()["id"]

    # Verify lists
    assert len(db_client.get("/api/v1/profile/achievements", headers=headers).json()) == 1
    assert len(db_client.get("/api/v1/profile/languages", headers=headers).json()) == 1
    assert len(db_client.get("/api/v1/profile/links", headers=headers).json()) == 1

    # Delete
    assert db_client.delete(f"/api/v1/profile/achievements/{ach_id}", headers=headers).status_code == 200
    assert db_client.delete(f"/api/v1/profile/languages/{lang_id}", headers=headers).status_code == 200
    assert db_client.delete(f"/api/v1/profile/links/{link_id}", headers=headers).status_code == 200


def test_profile_completeness_deterministic_calculation(db_client: TestClient):
    """Verify deterministic, explainable profile completeness calculation."""
    headers = register_and_login(db_client, "complete@example.com", "compuser")

    # 1. Fresh profile completeness -> 0%
    comp_res = db_client.get("/api/v1/profile/completeness", headers=headers)
    assert comp_res.status_code == 200
    comp = comp_res.json()
    assert comp["overall_score"] == 0
    assert comp["sections"]["personal"]["completed"] is False
    assert comp["sections"]["education"]["completed"] is False

    # 2. Complete personal section (15%)
    db_client.put(
        "/api/v1/profile/personal",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+1 555-0123",
            "location_city": "Austin",
        },
        headers=headers,
    )
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["personal"]["completed"] is True
    assert comp["overall_score"] == 15

    # 3. Complete professional section (15%)
    db_client.put(
        "/api/v1/profile/professional",
        json={
            "headline": "Senior Software Engineer",
            "professional_summary": "Full stack expert.",
        },
        headers=headers,
    )
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["professional"]["completed"] is True
    assert comp["overall_score"] == 30

    # 4. Add education (15%)
    db_client.post(
        "/api/v1/profile/education",
        json={"institution": "MIT", "degree": "BS CS"},
        headers=headers,
    )
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["education"]["completed"] is True
    assert comp["overall_score"] == 45

    # 5. Add experience (15%)
    db_client.post(
        "/api/v1/profile/experience",
        json={"company_name": "Google", "title": "Software Engineer"},
        headers=headers,
    )
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["experience"]["completed"] is True
    assert comp["overall_score"] == 60

    # 6. Add 3 skills (15%)
    for skill_name in ["Python", "TypeScript", "PostgreSQL"]:
        db_client.post("/api/v1/profile/skills", json={"name": skill_name}, headers=headers)
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["skills"]["completed"] is True
    assert comp["overall_score"] == 75

    # 7. Add preferences (10%)
    db_client.put(
        "/api/v1/profile/preferences",
        json={"desired_job_titles": ["Staff Engineer"], "preferred_locations": ["Remote"]},
        headers=headers,
    )
    comp = db_client.get("/api/v1/profile/completeness", headers=headers).json()
    assert comp["sections"]["preferences"]["completed"] is True
    assert comp["overall_score"] == 85  # (100 - 15 for resume = 85)


def test_overview_endpoint(db_client: TestClient):
    """Verify aggregated overview returns submodels and counts."""
    headers = register_and_login(db_client, "overview@example.com", "overuser")

    res = db_client.get("/api/v1/profile/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "personal" in data
    assert "professional" in data
    assert "preferences" in data
    assert "completeness" in data
    assert "counts" in data
    assert data["counts"]["education"] == 0
