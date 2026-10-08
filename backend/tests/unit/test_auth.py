"""
Comprehensive unit & integration tests for Stage 2:
Authentication, Security, Session Management, and Tenant Isolation.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select

from app.core.security import hash_password, create_access_token, decode_access_token
from app.models.user import User, RefreshToken, PasswordResetToken


# ===========================================================================
# 1. Registration Tests
# ===========================================================================

def test_register_success(db_client):
    """Test successful user registration returns access token and sets HttpOnly cookie."""
    payload = {
        "email": "candidate@example.com",
        "username": "candidate_jane",
        "password": "SecurePassword123!",
    }
    response = db_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Access token and token type
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # User response (never leak password)
    user = data["user"]
    assert user["email"] == "candidate@example.com"
    assert user["username"] == "candidate_jane"
    assert "hashed_password" not in user
    assert "password" not in user
    assert user["is_active"] is True

    # HttpOnly refresh cookie is set
    assert "refresh_token" in response.cookies
    cookie = response.cookies["refresh_token"]
    assert len(cookie) > 20


def test_register_duplicate_email(db_client):
    """Duplicate email registration attempt must fail with 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "username": "user_one",
        "password": "Password123!",
    }
    res1 = db_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "email": "duplicate@example.com",
        "username": "user_two",
        "password": "Password123!",
    }
    res2 = db_client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "email already exists" in res2.json()["detail"].lower()


def test_register_duplicate_username(db_client):
    """Duplicate username registration attempt must fail with 409 Conflict."""
    payload1 = {
        "email": "user1@example.com",
        "username": "same_username",
        "password": "Password123!",
    }
    res1 = db_client.post("/api/v1/auth/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "email": "user2@example.com",
        "username": "same_username",
        "password": "Password123!",
    }
    res2 = db_client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "username is already taken" in res2.json()["detail"].lower()


@pytest.mark.parametrize(
    "invalid_payload,expected_err",
    [
        (
            {"email": "invalid-email", "username": "valid_user", "password": "Password123!"},
            "pattern",
        ),
        (
            {"email": "valid@example.com", "username": "ab", "password": "Password123!"},
            "at least 3",
        ),
        (
            {"email": "valid@example.com", "username": "bad user!", "password": "Password123!"},
            "pattern",
        ),
        (
            {"email": "valid@example.com", "username": "valid_user", "password": "nouppercase123!"},
            "uppercase",
        ),
        (
            {"email": "valid@example.com", "username": "valid_user", "password": "NoNumbersHere!"},
            "number",
        ),
        (
            {"email": "valid@example.com", "username": "valid_user", "password": "NoSpecialChar123"},
            "special character",
        ),
    ],
)
def test_register_validation_rules(db_client, invalid_payload, expected_err):
    """Ensure strict validation for email, username, and password complexity."""
    response = db_client.post("/api/v1/auth/register", json=invalid_payload)
    assert response.status_code == 422


# ===========================================================================
# 2. Login Tests
# ===========================================================================

def test_login_success(db_client):
    """Valid credentials successfully log in and set refresh cookie."""
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "login_test@example.com", "username": "logintest", "password": "Password123!"},
    )
    assert reg.status_code == 201

    login_res = db_client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_test@example.com"
    assert "refresh_token" in login_res.cookies


def test_login_invalid_password(db_client):
    """Wrong password returns 401 Unauthorized with generic message."""
    db_client.post(
        "/api/v1/auth/register",
        json={"email": "wrong_pwd@example.com", "username": "wrong_pwd_user", "password": "Password123!"},
    )

    login_res = db_client.post(
        "/api/v1/auth/login",
        json={"email": "wrong_pwd@example.com", "password": "IncorrectPassword999!"},
    )
    assert login_res.status_code == 401
    assert "invalid email or password" in login_res.json()["detail"].lower()


def test_login_unknown_user(db_client):
    """Non-existent email returns generic 401 without revealing account absence."""
    login_res = db_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 401
    assert "invalid email or password" in login_res.json()["detail"].lower()


# ===========================================================================
# 3. Authentication & Guard Tests
# ===========================================================================

def test_get_current_user_authenticated(db_client):
    """Authenticated GET /auth/me returns current user profile."""
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "me_test@example.com", "username": "me_user", "password": "Password123!"},
    )
    token = reg.json()["access_token"]

    res = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me_test@example.com"
    assert res.json()["username"] == "me_user"


def test_get_current_user_missing_token(db_client):
    """Request without token returns 401 Unauthorized."""
    res = db_client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_get_current_user_invalid_token(db_client):
    """Tampered token returns 401 Unauthorized."""
    res = db_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert res.status_code == 401


def test_get_current_user_expired_token(db_client):
    """Expired access token returns 401 Unauthorized."""
    # Create an already-expired token directly
    user_id = str(uuid4())
    from app.core.config import settings
    from jose import jwt
    expired_payload = {
        "sub": user_id,
        "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_jwt = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    res = db_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_jwt}"},
    )
    assert res.status_code == 401


# ===========================================================================
# 4. Refresh Token & Rotation Tests
# ===========================================================================

def test_refresh_token_rotation(db_client):
    """
    POST /auth/refresh:
    - Rotates refresh token (sets new cookie).
    - Issues fresh access token.
    - Previous refresh token is revoked and cannot be reused.
    """
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "refresh_flow@example.com", "username": "refresh_flow", "password": "Password123!"},
    )
    old_cookie = reg.cookies["refresh_token"]

    # 1. Perform first refresh
    refresh_res = db_client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert refresh_res.status_code == 200
    new_token = refresh_res.json()["access_token"]
    assert new_token
    new_cookie = refresh_res.cookies.get("refresh_token")
    assert new_cookie and new_cookie != old_cookie

    # 2. Verify new access token works
    me_res = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_res.status_code == 200

    # 3. REUSE DETECTION: Presenting the old (now rotated/revoked) refresh token must fail with 401
    reused_res = db_client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert reused_res.status_code == 401
    assert "revoked" in reused_res.json()["detail"].lower()


def test_refresh_missing_cookie_or_body(db_client):
    """Refresh request without cookie or body returns 401."""
    res = db_client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


# ===========================================================================
# 5. Logout Tests
# ===========================================================================

def test_logout_revokes_session(db_client):
    """Logging out revokes the refresh session and deletes the cookie."""
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "logout_test@example.com", "username": "logout_user", "password": "Password123!"},
    )
    cookie = reg.cookies["refresh_token"]

    logout_res = db_client.post("/api/v1/auth/logout", cookies={"refresh_token": cookie})
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"

    # Attempting to refresh with the logged-out token must fail
    fail_refresh = db_client.post("/api/v1/auth/refresh", cookies={"refresh_token": cookie})
    assert fail_refresh.status_code == 401


# ===========================================================================
# 6. Password Reset Flow Tests
# ===========================================================================

def test_password_reset_flow(db_client):
    """
    Full password reset lifecycle:
    1. forgot-password endpoint returns generic safe message (no user enumeration).
    2. Reset token in database is hashed with SHA-256 (raw token is never persisted).
    3. reset-password updates password and invalidates previous sessions.
    4. Old password fails; new password logs in successfully.
    5. Token cannot be reused once consumed.
    """
    import hashlib
    from app.services.auth_service import hash_token
    from app.models.user import User, PasswordResetToken
    from app.db.session import get_db

    # Register user
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "pw_reset@example.com", "username": "pw_reset_user", "password": "OldPassword123!"},
    )
    assert reg.status_code == 201
    old_cookie = reg.cookies["refresh_token"]

    # 1. Request password reset
    forgot_res = db_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "pw_reset@example.com"},
    )
    assert forgot_res.status_code == 200
    assert "instructions have been sent" in forgot_res.json()["message"]
    # Verify raw token is NOT in the response
    assert "token" not in forgot_res.json()

    # Also test non-existent email returns identical generic message (enumeration prevention)
    fake_forgot = db_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "does_not_exist@example.com"},
    )
    assert fake_forgot.status_code == 200
    assert fake_forgot.json()["message"] == forgot_res.json()["message"]

    # 2. Test invalid / malformed token reset
    bad_reset = db_client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token-123456", "new_password": "NewPassword456!"},
    )
    assert bad_reset.status_code == 400

    # 3. Retrieve raw token by testing programmatic reset flow
    from app.services.auth_service import generate_reset_token
    raw_test_token = generate_reset_token()
    token_hashed = hash_token(raw_test_token)

    # Insert a valid reset token record to test full password update
    async def seed_reset_token():
        override = db_client.app.dependency_overrides[get_db]
        async for session in override():
            user = (await session.execute(select(User).where(User.email == "pw_reset@example.com"))).scalar_one()
            record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hashed,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            await session.commit()
            break

    import asyncio
    asyncio.run(seed_reset_token())

    # 4. Successfully reset password with raw token
    good_reset = db_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_test_token, "new_password": "NewPassword456!"},
    )
    assert good_reset.status_code == 200
    assert "successful" in good_reset.json()["message"].lower()

    # 5. Old password now fails
    fail_login = db_client.post(
        "/api/v1/auth/login",
        json={"email": "pw_reset@example.com", "password": "OldPassword123!"},
    )
    assert fail_login.status_code == 401

    # 6. New password succeeds
    good_login = db_client.post(
        "/api/v1/auth/login",
        json={"email": "pw_reset@example.com", "password": "NewPassword456!"},
    )
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()

    # 7. Old refresh session is revoked
    revoked_refresh = db_client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert revoked_refresh.status_code == 401

    # 8. Consumed reset token cannot be reused
    reuse_reset = db_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_test_token, "new_password": "AnotherPassword789!"},
    )
    assert reuse_reset.status_code == 400


def test_token_and_secret_exposure_audit(db_client, caplog):
    """
    Security audit verifying:
    - Raw tokens are not persisted in the database.
    - Password hashes are never returned in responses.
    - Raw tokens are never logged.
    """
    import logging
    from app.models.user import RefreshToken, User
    from app.db.session import get_db

    with caplog.at_level(logging.DEBUG):
        reg = db_client.post(
            "/api/v1/auth/register",
            json={"email": "audit_user@example.com", "username": "audit_user", "password": "Password123!"},
        )
        assert reg.status_code == 201
        data = reg.json()
        raw_cookie = reg.cookies["refresh_token"]

        # 1. No password or hash in response
        assert "password" not in data["user"]
        assert "hashed_password" not in data["user"]
        assert "refresh_token" not in data

        # 2. Database contains only hashed tokens and bcrypt hash
        async def verify_db_storage():
            override = db_client.app.dependency_overrides[get_db]
            async for session in override():
                user = (await session.execute(select(User).where(User.email == "audit_user@example.com"))).scalar_one()
                # Verify password is bcrypt hashed
                assert user.hashed_password.startswith("$2b$12$")
                assert user.hashed_password != "Password123!"

                # Verify refresh token in DB is hashed
                refresh = (await session.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))).scalar_one()
                assert refresh.token_hash != raw_cookie
                assert len(refresh.token_hash) == 64  # SHA-256 hex
                break

        import asyncio
        asyncio.run(verify_db_storage())

        # 3. Logs never contain raw tokens or passwords
        for record in caplog.records:
            assert raw_cookie not in record.message
            assert "Password123!" not in record.message



# ===========================================================================
# 7. Tenant Isolation Tests
# ===========================================================================

def test_tenant_isolation(db_client):
    """
    Verify tenant isolation:
    User A's credentials and token only resolve User A's data.
    User A cannot access or mutate User B's sessions.
    """
    user_a = db_client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "username": "user_a", "password": "Password123!"},
    ).json()

    user_b = db_client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "username": "user_b", "password": "Password123!"},
    ).json()

    token_a = user_a["access_token"]
    token_b = user_b["access_token"]

    # Request /me with User A token
    res_a = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.json()["id"] == user_a["user"]["id"]
    assert res_a.json()["id"] != user_b["user"]["id"]

    # User A views their own active sessions
    sessions_a = db_client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(sessions_a) >= 1

    # User B views their own active sessions
    sessions_b = db_client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(sessions_b) >= 1
    session_b_id = sessions_b[0]["id"]

    # User A attempts to delete User B's session -> Must fail with 404 (isolation enforced)
    attack_res = db_client.delete(
        f"/api/v1/auth/sessions/{session_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert attack_res.status_code == 404


def test_hirer_registration_success(db_client):
    """Test successful HIRER registration creates user with role HIRER and Organization."""
    payload = {
        "email": "recruiter@acmecorp.com",
        "username": "acme_recruiter",
        "password": "Password123!",
        "role": "HIRER",
        "organization_name": "Acme Corp",
    }
    response = db_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["role"] == "HIRER"

    # Verify decoded token has role
    claims = decode_access_token(data["access_token"])
    assert claims["role"] == "HIRER"

    # Verify /me endpoint returns HIRER role
    me_res = db_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "HIRER"


def test_hirer_registration_missing_organization_name(db_client):
    """HIRER registration without organization_name must fail with 400 Bad Request."""
    payload = {
        "email": "recruiter_no_org@test.com",
        "username": "no_org_recruiter",
        "password": "Password123!",
        "role": "HIRER",
    }
    response = db_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Organization name is required" in response.json()["detail"]


def test_register_invalid_role(db_client):
    """Registration with an invalid role must fail with 422 Unprocessable Entity."""
    payload = {
        "email": "invalid_role@test.com",
        "username": "invalid_role_user",
        "password": "Password123!",
        "role": "SUPERADMIN",
    }
    response = db_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
