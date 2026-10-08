"""
Unit tests for Career Analytics & Dashboard APIs.
Stage 9: Analytics & Settings.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, username: str) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": "Password123!",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_analytics_rejected(db_client: TestClient):
    assert db_client.get("/api/v1/analytics").status_code == 401
    assert db_client.get("/api/v1/analytics/overview").status_code == 401
    assert db_client.get("/api/v1/analytics/trends").status_code == 401
    assert db_client.get("/api/v1/analytics/pipeline").status_code == 401
    assert db_client.get("/api/v1/analytics/companies").status_code == 401
    assert db_client.get("/api/v1/analytics/outcomes").status_code == 401
    assert db_client.get("/api/v1/analytics/time").status_code == 401
    assert db_client.get("/api/v1/dashboard/summary").status_code == 401


def test_analytics_empty_user(db_client: TestClient):
    headers = register_and_login(db_client, "empty_analytics@example.com", "empty_analytics_user")

    # Overview
    res = db_client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_applications"] == 0
    assert data["active_applications"] == 0
    assert data["response_rate"] == 0.0
    assert data["interview_rate"] == 0.0
    assert data["offer_rate"] == 0.0
    assert data["acceptance_rate"] == 0.0

    # Trends
    res = db_client.get("/api/v1/analytics/trends?range=30d", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_in_period"] == 0

    # Pipeline
    res = db_client.get("/api/v1/analytics/pipeline", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_applications"] == 0

    # Companies
    res = db_client.get("/api/v1/analytics/companies", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_companies"] == 0

    # Outcomes
    res = db_client.get("/api/v1/analytics/outcomes", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_outcomes"] == 0

    # Time
    res = db_client.get("/api/v1/analytics/time", headers=headers)
    assert res.status_code == 200
    time_data = res.json()
    assert time_data["avg_days_to_first_response"] is None
    assert time_data["avg_days_to_interview"] is None

    # Dashboard
    res = db_client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 200
    dash_data = res.json()
    assert dash_data["active_applications"] == 0
    assert dash_data["upcoming_interviews"] == 0


def test_analytics_populated_kpis(db_client: TestClient):
    headers = register_and_login(db_client, "populated_analytics@example.com", "pop_analytics_user")

    # 1. Create Opportunities
    db_client.post("/api/v1/opportunities", headers=headers, json={
        "title": "Staff Engineer",
        "company_name": "Google",
        "status": "SAVED",
    })
    db_client.post("/api/v1/opportunities", headers=headers, json={
        "title": "Principal Architect",
        "company_name": "Netflix",
        "status": "ACTIVE",
    })

    # 2. Create Applications
    # App 1: In progress at INTERVIEW stage
    app1_res = db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Senior Backend Engineer",
        "company_name": "Stripe",
        "current_stage": "INTERVIEW",
    })
    app1_id = app1_res.json()["id"]

    # Schedule interview for App 1
    iv_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    db_client.post("/api/v1/interviews", headers=headers, json={
        "application_id": app1_id,
        "interview_type": "TECHNICAL",
        "scheduled_at": iv_time,
    })

    # App 2: OFFER received and ACCEPTED
    app2_res = db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Lead Software Engineer",
        "company_name": "Apple",
        "current_stage": "ACCEPTED",
    })

    # App 3: REJECTED
    db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Site Reliability Engineer",
        "company_name": "Meta",
        "current_stage": "REJECTED",
    })

    # App 4: Still at initial APPLIED stage
    db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Cloud Architect",
        "company_name": "Amazon",
        "current_stage": "APPLIED",
    })

    # Verify Overview KPIs
    res = db_client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    ov = res.json()

    assert ov["total_applications"] == 4
    # App 1 is active (INTERVIEW). App 4 is active (APPLIED). App 2 is ACCEPTED (not active). App 3 is REJECTED (not active).
    assert ov["active_applications"] == 2
    assert ov["total_opportunities"] == 2
    assert ov["saved_opportunities"] == 1
    assert ov["interviews_scheduled"] == 1
    assert ov["offers_received"] == 1  # App 2 (ACCEPTED counts as received offer)
    assert ov["accepted_offers"] == 1
    assert ov["rejected_applications"] == 1
    # 3 out of 4 moved past APPLIED (Stripe, Apple, Meta) -> 75.0%
    assert ov["response_rate"] == 75.0
    # 1 app had interview scheduled out of 4 -> 25.0%
    assert ov["interview_rate"] == 25.0
    # 1 offer received out of 4 -> 25.0%
    assert ov["offer_rate"] == 25.0
    # 1 accepted out of 1 offer -> 100.0%
    assert ov["acceptance_rate"] == 100.0


def test_analytics_trends_and_validation(db_client: TestClient):
    headers = register_and_login(db_client, "trends_user@example.com", "trends_user")

    # Valid ranges
    for r in ["7d", "30d", "90d", "6m", "1y", "all"]:
        res = db_client.get(f"/api/v1/analytics/trends?range={r}", headers=headers)
        assert res.status_code == 200
        assert res.json()["range"] == r

    # Invalid range must return 422
    invalid_res = db_client.get("/api/v1/analytics/trends?range=invalid_range", headers=headers)
    assert invalid_res.status_code == 422


def test_pipeline_funnel_and_company_analytics(db_client: TestClient):
    headers = register_and_login(db_client, "funnel_user@example.com", "funnel_user")

    # Create app and transition stages
    app_res = db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Full Stack Dev",
        "company_name": "Datadog",
        "current_stage": "APPLIED",
    })
    app_id = app_res.json()["id"]

    # Transition to PHONE_SCREEN
    db_client.post(f"/api/v1/applications/{app_id}/stage", headers=headers, json={
        "to_stage": "PHONE_SCREEN",
        "notes": "Recruiter call passed",
    })
    # Transition to INTERVIEW
    db_client.post(f"/api/v1/applications/{app_id}/stage", headers=headers, json={
        "to_stage": "INTERVIEW",
        "notes": "Invited to virtual on-site",
    })

    # Test Pipeline
    pipe_res = db_client.get("/api/v1/analytics/pipeline", headers=headers)
    assert pipe_res.status_code == 200
    pipe_data = pipe_res.json()
    assert pipe_data["total_applications"] == 1

    stages_by_name = {s["stage"]: s for s in pipe_data["stages"]}
    assert stages_by_name["APPLIED"]["cumulative_count"] == 1
    assert stages_by_name["PHONE_SCREEN"]["cumulative_count"] == 1
    assert stages_by_name["INTERVIEW"]["cumulative_count"] == 1
    assert stages_by_name["OFFER"]["cumulative_count"] == 0

    # Test Companies
    comp_res = db_client.get("/api/v1/analytics/companies", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["total_companies"] == 1
    assert comp_data["companies"][0]["company_name"] == "Datadog"
    assert comp_data["companies"][0]["total_applications"] == 1


def test_multi_user_tenant_isolation_analytics(db_client: TestClient):
    headers_a = register_and_login(db_client, "user_a_analytics@example.com", "user_a_an")
    headers_b = register_and_login(db_client, "user_b_analytics@example.com", "user_b_an")

    # User A creates application
    db_client.post("/api/v1/applications", headers=headers_a, json={
        "job_title": "Security Architect",
        "company_name": "Palo Alto Networks",
        "current_stage": "OFFER",
    })

    # Verify User A sees 1 application and 1 offer
    res_a = db_client.get("/api/v1/analytics/overview", headers=headers_a)
    assert res_a.json()["total_applications"] == 1
    assert res_a.json()["offers_received"] == 1

    # Verify User B sees completely empty analytics (0 applications, 0 offers)
    res_b = db_client.get("/api/v1/analytics/overview", headers=headers_b)
    assert res_b.json()["total_applications"] == 0
    assert res_b.json()["offers_received"] == 0

    # Verify User B companies is empty
    comp_b = db_client.get("/api/v1/analytics/companies", headers=headers_b)
    assert comp_b.json()["total_companies"] == 0


def test_historical_pipeline_and_outcome_semantics(db_client: TestClient):
    headers = register_and_login(db_client, "history_funnel_user@example.com", "hist_user")

    # App 1: Starts at APPLIED, advances to INTERVIEW, then rejected
    app1 = db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Senior Infra Engineer",
        "company_name": "Snowflake",
        "current_stage": "APPLIED",
    }).json()
    app1_id = app1["id"]

    db_client.post(f"/api/v1/applications/{app1_id}/stage", headers=headers, json={
        "to_stage": "INTERVIEW",
        "notes": "Passed screen, tech rounds scheduled",
    })
    db_client.post(f"/api/v1/applications/{app1_id}/stage", headers=headers, json={
        "to_stage": "REJECTED",
        "notes": "Position filled internally",
    })

    # App 2: Starts at APPLIED, advances to OFFER (pending decision)
    app2 = db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Backend Staff",
        "company_name": "Databricks",
        "current_stage": "APPLIED",
    }).json()
    app2_id = app2["id"]

    db_client.post(f"/api/v1/applications/{app2_id}/stage", headers=headers, json={
        "to_stage": "OFFER",
        "notes": "Offer letter received",
    })

    # Verify Pipeline Funnel Cumulative Counts
    pipe = db_client.get("/api/v1/analytics/pipeline", headers=headers).json()
    assert pipe["total_applications"] == 2
    assert pipe["rejected_count"] == 1
    assert pipe["withdrawn_count"] == 0

    stages = {s["stage"]: s for s in pipe["stages"]}
    assert stages["APPLIED"]["cumulative_count"] == 2
    assert stages["PHONE_SCREEN"]["cumulative_count"] == 2
    assert stages["ASSESSMENT"]["cumulative_count"] == 2
    assert stages["INTERVIEW"]["cumulative_count"] == 2
    assert stages["OFFER"]["cumulative_count"] == 1
    assert stages["ACCEPTED"]["cumulative_count"] == 0

    assert stages["APPLIED"]["conversion_rate"] == 100.0
    assert stages["PHONE_SCREEN"]["conversion_rate"] == 100.0
    assert stages["ASSESSMENT"]["conversion_rate"] == 100.0
    assert stages["INTERVIEW"]["conversion_rate"] == 100.0
    assert stages["OFFER"]["conversion_rate"] == 50.0
    assert stages["ACCEPTED"]["conversion_rate"] == 0.0

    # Verify Outcomes Semantics (total_outcomes = closed/terminal, active_count = in-flight including offers)
    outcomes = db_client.get("/api/v1/analytics/outcomes", headers=headers).json()
    assert outcomes["total_outcomes"] == 1  # 1 terminal (REJECTED)
    assert outcomes["active_count"] == 1    # 1 in-flight (OFFER)

    outcomes_by_type = {o["outcome"]: o for o in outcomes["breakdown"]}
    assert outcomes_by_type["REJECTED"]["count"] == 1
    assert outcomes_by_type["REJECTED"]["percentage"] == 50.0  # 1 / 2 total_applications
    assert outcomes_by_type["OFFER"]["count"] == 1
    assert outcomes_by_type["OFFER"]["percentage"] == 50.0     # 1 / 2 total_applications
    assert outcomes_by_type["ACCEPTED"]["count"] == 0
    assert outcomes_by_type["ACCEPTED"]["percentage"] == 0.0
