"""
Unit tests for Settings, Account, Security, Sessions & GDPR Data Export APIs.
Stage 9: Analytics & Settings.
"""

import uuid
import pytest
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, username: str, password: str = "Password123!") -> dict[str, str]:
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_settings_rejected(db_client: TestClient):
    dummy_id = str(uuid.uuid4())
    assert db_client.get("/api/v1/settings/account").status_code == 401
    assert db_client.put("/api/v1/settings/account", json={"username": "new_name"}).status_code == 401
    assert db_client.put("/api/v1/settings/security/password", json={"current_password": "a", "new_password": "b"}).status_code == 401
    assert db_client.get("/api/v1/settings/sessions").status_code == 401
    assert db_client.delete(f"/api/v1/settings/sessions/{dummy_id}").status_code == 401
    assert db_client.delete("/api/v1/settings/sessions").status_code == 401
    assert db_client.get("/api/v1/settings/notifications").status_code == 401
    assert db_client.put("/api/v1/settings/notifications", json={"in_app_alerts": False}).status_code == 401
    assert db_client.post("/api/v1/settings/data-export").status_code == 401
    assert db_client.delete("/api/v1/settings/account").status_code == 401


def test_account_details_and_update(db_client: TestClient):
    headers = register_and_login(db_client, "account_settings@example.com", "acct_user_1")

    # Get details
    res = db_client.get("/api/v1/settings/account", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "account_settings@example.com"
    assert data["username"] == "acct_user_1"

    # Update username
    up_res = db_client.put("/api/v1/settings/account", headers=headers, json={
        "username": "acct_user_updated",
    })
    assert up_res.status_code == 200
    assert up_res.json()["username"] == "acct_user_updated"

    # Duplicate username conflict test
    headers2 = register_and_login(db_client, "account_settings2@example.com", "acct_user_2")
    conflict_res = db_client.put("/api/v1/settings/account", headers=headers2, json={
        "username": "acct_user_updated",
    })
    assert conflict_res.status_code == 409


def test_password_change_flow(db_client: TestClient):
    email = "pwd_change@example.com"
    old_pwd = "OldPassword123!"
    new_pwd = "NewSecurePassword456!"
    headers = register_and_login(db_client, email, "pwd_user", password=old_pwd)

    # Wrong current password fails with 400
    bad_res = db_client.put("/api/v1/settings/security/password", headers=headers, json={
        "current_password": "WrongPassword123!",
        "new_password": new_pwd,
    })
    assert bad_res.status_code == 400

    # Short new password fails with 422
    short_res = db_client.put("/api/v1/settings/security/password", headers=headers, json={
        "current_password": old_pwd,
        "new_password": "short",
    })
    assert short_res.status_code == 422

    # Valid change succeeds
    good_res = db_client.put("/api/v1/settings/security/password", headers=headers, json={
        "current_password": old_pwd,
        "new_password": new_pwd,
    })
    assert good_res.status_code == 200

    # Old password fails login
    assert db_client.post("/api/v1/auth/login", json={"email": email, "password": old_pwd}).status_code == 401

    # New password succeeds login
    login_new = db_client.post("/api/v1/auth/login", json={"email": email, "password": new_pwd})
    assert login_new.status_code == 200


def test_sessions_management(db_client: TestClient):
    headers = register_and_login(db_client, "session_user@example.com", "sess_user")

    # Log in a second time to create a distinct active session
    db_client.post("/api/v1/auth/login", json={
        "email": "session_user@example.com",
        "password": "Password123!",
    })

    # List sessions
    res = db_client.get("/api/v1/settings/sessions", headers=headers)
    assert res.status_code == 200
    sessions = res.json()
    assert len(sessions) >= 2
    session_id_to_revoke = sessions[1]["id"]

    # Revoke specific session
    revoke_one_res = db_client.delete(f"/api/v1/settings/sessions/{session_id_to_revoke}", headers=headers)
    assert revoke_one_res.status_code == 200

    # Revoke remaining sessions
    revoke_all_res = db_client.delete("/api/v1/settings/sessions", headers=headers)
    assert revoke_all_res.status_code == 200


def test_notification_settings_crud(db_client: TestClient):
    headers = register_and_login(db_client, "notif_settings@example.com", "notif_user")

    # Get defaults
    res = db_client.get("/api/v1/settings/notifications", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["in_app_alerts"] is True
    assert data["interview_reminders"] is True

    # Update settings
    up_res = db_client.put("/api/v1/settings/notifications", headers=headers, json={
        "in_app_alerts": False,
        "task_reminders": False,
    })
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["in_app_alerts"] is False
    assert up_data["task_reminders"] is False
    assert up_data["interview_reminders"] is True

    # Verify persistence
    check_res = db_client.get("/api/v1/settings/notifications", headers=headers)
    assert check_res.json()["in_app_alerts"] is False


def test_data_export_bundle(db_client: TestClient):
    headers = register_and_login(db_client, "export_user@example.com", "export_user")

    # Seed data
    db_client.post("/api/v1/applications", headers=headers, json={
        "job_title": "Platform Lead",
        "company_name": "Cloudflare",
        "current_stage": "INTERVIEW",
    })
    db_client.post("/api/v1/tasks", headers=headers, json={
        "title": "Complete architecture doc",
        "priority": "HIGH",
    })

    # Trigger export
    res = db_client.post("/api/v1/settings/data-export", headers=headers)
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["email"] == "export_user@example.com"
    assert "data" in bundle
    assert len(bundle["data"]["applications"]) == 1
    assert bundle["data"]["applications"][0]["company_name"] == "Cloudflare"
    assert len(bundle["data"]["tasks"]) == 1
    assert bundle["data"]["tasks"][0]["title"] == "Complete architecture doc"
    assert "qa_vault" in bundle["data"]
    assert "resumes" in bundle["data"]
    assert "documents" in bundle["data"]
    assert "saved_opportunities" in bundle["data"]
    assert "achievements" in bundle["data"]
    assert "languages" in bundle["data"]
    assert "profile_links" in bundle["data"]
    assert "answers" in bundle["data"]["applications"][0]
    assert "activity" in bundle["data"]["applications"][0]
    assert "documents" in bundle["data"]["applications"][0]


def test_delete_account_lifecycle(db_client: TestClient):
    headers = register_and_login(db_client, "delete_me@example.com", "delete_user", "CorrectPassword123!")

    # Attempt with wrong password -> 400
    bad_res = db_client.request(
        "DELETE", "/api/v1/settings/account", headers=headers, json={"password": "WrongPassword!"}
    )
    assert bad_res.status_code == 400

    # Attempt with correct password -> 200
    ok_res = db_client.request(
        "DELETE", "/api/v1/settings/account", headers=headers, json={"password": "CorrectPassword123!"}
    )
    assert ok_res.status_code == 200

    # Login should now fail -> 401
    fail_login = db_client.post("/api/v1/auth/login", json={
        "email": "delete_me@example.com",
        "password": "CorrectPassword123!",
    })
    assert fail_login.status_code == 401


def test_multi_user_tenant_isolation_settings(db_client: TestClient):
    headers_a = register_and_login(db_client, "user_a_settings@example.com", "user_a_st")
    headers_b = register_and_login(db_client, "user_b_settings@example.com", "user_b_st")

    # User A gets session list
    sess_a = db_client.get("/api/v1/settings/sessions", headers=headers_a).json()
    sess_a_id = sess_a[0]["id"]

    # User B cannot revoke User A's session -> 404
    assert db_client.delete(f"/api/v1/settings/sessions/{sess_a_id}", headers=headers_b).status_code == 404

    # User B cannot see User A's account details
    acct_b = db_client.get("/api/v1/settings/account", headers=headers_b).json()
    assert acct_b["email"] == "user_b_settings@example.com"
    assert acct_b["username"] == "user_b_st"
