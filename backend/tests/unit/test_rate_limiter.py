"""
Unit tests for authentication rate limiting:
- Brute-force protection on /login
- Shared network resilience (composite keying)
- Rate limiting on /register, /refresh, /forgot-password, /security/password
- HTTP 429 Too Many Requests response format and Retry-After header
- Limiter reset functionality
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limiter import limiter


def test_login_rate_limiting_and_retry_after(db_client: TestClient):
    """Exceeding login attempts for an account triggers HTTP 429 with Retry-After header."""
    limiter.reset()

    # Register target user
    db_client.post(
        "/api/v1/auth/register",
        json={"email": "target@example.com", "username": "targetuser", "password": "Password123!"},
    )

    client_headers = {"X-Forwarded-For": "198.51.100.1"}

    # Attempt login up to the configured limit
    max_attempts = settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS
    for i in range(max_attempts):
        res = db_client.post(
            "/api/v1/auth/login",
            json={"email": "target@example.com", "password": "WrongPassword!"},
            headers=client_headers,
        )
        assert res.status_code == 401

    # Next attempt must trigger HTTP 429
    blocked_res = db_client.post(
        "/api/v1/auth/login",
        json={"email": "target@example.com", "password": "Password123!"},
        headers=client_headers,
    )
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert int(blocked_res.headers["Retry-After"]) >= 1
    assert "too many requests" in blocked_res.json()["detail"].lower()


def test_login_shared_network_isolation(db_client: TestClient):
    """
    Legitimate users sharing the same NAT/proxy IP are not locked out
    when an attacker targets a single account from that IP.
    """
    limiter.reset()

    shared_ip_headers = {"X-Forwarded-For": "203.0.113.50"}

    # Register Alice and Bob
    db_client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "Password123!"},
        headers=shared_ip_headers,
    )
    db_client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "Password123!"},
        headers=shared_ip_headers,
    )

    # Exhaust login attempts for Alice from shared IP
    for _ in range(settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS):
        res = db_client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "WrongPassword!"},
            headers=shared_ip_headers,
        )
        assert res.status_code == 401

    # Alice is now rate-limited
    alice_blocked = db_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password123!"},
        headers=shared_ip_headers,
    )
    assert alice_blocked.status_code == 429

    # Bob from the EXACT SAME IP can still log in successfully!
    bob_login = db_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "Password123!"},
        headers=shared_ip_headers,
    )
    assert bob_login.status_code == 200
    assert "access_token" in bob_login.json()


def test_register_rate_limit(db_client: TestClient):
    """Rapid account registrations from the same IP are rate-limited with 429."""
    limiter.reset()
    headers = {"X-Forwarded-For": "198.51.100.22"}

    max_reg = settings.RATE_LIMIT_REGISTER_MAX_ATTEMPTS
    for i in range(max_reg):
        res = db_client.post(
            "/api/v1/auth/register",
            json={"email": f"spam_{i}@example.com", "username": f"spam_{i}", "password": "Password123!"},
            headers=headers,
        )
        assert res.status_code == 201

    # Next attempt is blocked
    blocked = db_client.post(
        "/api/v1/auth/register",
        json={"email": "spam_blocked@example.com", "username": "spamblocked", "password": "Password123!"},
        headers=headers,
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_refresh_token_rate_limit(db_client: TestClient):
    """Rapid refresh-token attempts are rate-limited with 429."""
    limiter.reset()
    headers = {"X-Forwarded-For": "198.51.100.33"}

    max_refresh = settings.RATE_LIMIT_REFRESH_MAX_ATTEMPTS
    for _ in range(max_refresh):
        res = db_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_or_missing_token"},
            headers=headers,
        )
        # Even on 401, the rate limiter records the attempt
        assert res.status_code == 401

    blocked = db_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"},
        headers=headers,
    )
    assert blocked.status_code == 429


def test_forgot_password_rate_limit(db_client: TestClient):
    """Forgot-password endpoint enforces rate limiting against email and IP flooding."""
    limiter.reset()
    headers = {"X-Forwarded-For": "198.51.100.44"}

    max_attempts = settings.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS
    for _ in range(max_attempts):
        res = db_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "victim@example.com"},
            headers=headers,
        )
        assert res.status_code == 200

    blocked = db_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "victim@example.com"},
        headers=headers,
    )
    assert blocked.status_code == 429


def test_change_password_rate_limit(db_client: TestClient):
    """Password change requests are rate-limited per user account."""
    limiter.reset()

    # Register and login user
    reg = db_client.post(
        "/api/v1/auth/register",
        json={"email": "changepwd@example.com", "username": "changepwd", "password": "Password123!"},
    ).json()
    token = reg["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    max_attempts = settings.RATE_LIMIT_CHANGE_PASSWORD_MAX_ATTEMPTS
    for _ in range(max_attempts):
        res = db_client.put(
            "/api/v1/settings/security/password",
            json={"current_password": "WrongPassword!", "new_password": "NewPassword123!"},
            headers=auth_headers,
        )
        assert res.status_code == 400

    # Next attempt triggers 429
    blocked = db_client.put(
        "/api/v1/settings/security/password",
        json={"current_password": "Password123!", "new_password": "NewPassword123!"},
        headers=auth_headers,
    )
    assert blocked.status_code == 429


def test_rate_limiter_reset(db_client: TestClient):
    """limiter.reset() clears all buckets and restores access."""
    limiter.reset()
    headers = {"X-Forwarded-For": "198.51.100.99"}

    for i in range(settings.RATE_LIMIT_REGISTER_MAX_ATTEMPTS):
        db_client.post(
            "/api/v1/auth/register",
            json={"email": f"reset_test_{i}@example.com", "username": f"user_{i}", "password": "Password123!"},
            headers=headers,
        )

    # Blocked with 429
    blocked = db_client.post(
        "/api/v1/auth/register",
        json={"email": "reset_test_extra@example.com", "username": "userextra", "password": "Password123!"},
        headers=headers,
    )
    assert blocked.status_code == 429

    # Reset
    limiter.reset()

    # Now permitted again
    res = db_client.post(
        "/api/v1/auth/register",
        json={"email": "fresh@example.com", "username": "freshuser", "password": "Password123!"},
        headers=headers,
    )
    assert res.status_code == 201
