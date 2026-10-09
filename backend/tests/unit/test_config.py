"""
Unit tests for configuration validation, production secrets hardening, and security safeguards.
Tests verify that insecure default secrets, debug mode, and wildcards are strictly rejected in production.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_application

VALID_PROD_SECRET = "x7f9a8b1c2d3e4f5061728394a5b6c7d8e9f0123456789abcdef0123456789ab"
VALID_PROD_DB_PWD = "Pr0d_StR0ng_Db_P@ssw0rd_987654321!"
VALID_PROD_DB_URL = f"postgresql+asyncpg://postgres_admin:{VALID_PROD_DB_PWD}@db:5432/career_platform_prod"
VALID_PROD_HOSTS = ["career-platform.com", "api.career-platform.com", "testserver"]


# ---------------------------------------------------------------------------
# Development Configuration Defaults
# ---------------------------------------------------------------------------

def test_development_defaults():
    """Verify development mode retains safe developer defaults with DEBUG enabled."""
    s = Settings(APP_ENV="development")
    assert s.is_production is False
    assert s.DEBUG is True
    assert s.docs_enabled is True
    assert "*" not in s.ALLOWED_HOSTS
    assert "testserver" in s.ALLOWED_HOSTS
    assert "localhost" in s.ALLOWED_HOSTS


# ---------------------------------------------------------------------------
# Production Secret Key Validations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("insecure_secret", [
    "",
    "   ",
    "short_secret_under_32_chars",
    "CHANGE_ME_IN_PRODUCTION_USE_RANDOM_32_BYTES",
    "prod_super_secret_jwt_key_at_least_32_chars_long",
    "insecure_default_dev_secret_key_minimum_32_chars_long_12345",
    "replace_with_a_random_development_secret",
    "generate_a_strong_random_secret_key_at_least_64_characters_long",
    "secret",
    "changeme",
    "supersecret_placeholder_with_change_me_inside",
])
def test_production_fails_on_insecure_secret_key(insecure_secret):
    """Verify production startup fails immediately on missing, short, or placeholder SECRET_KEY."""
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=insecure_secret,
            POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
            DATABASE_URL=VALID_PROD_DB_URL,
            ALLOWED_HOSTS=VALID_PROD_HOSTS,
        )


# ---------------------------------------------------------------------------
# Production Database Password Validations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("insecure_pwd", [
    "postgres",
    "password",
    "admin",
    "root",
    "123456",
    "12345678",
    "replace_with_local_database_password",
    "generate_a_cryptographically_secure_password_here",
    "changeme",
])
def test_production_fails_on_insecure_postgres_password(insecure_pwd):
    """Verify production startup fails if POSTGRES_PASSWORD contains known insecure defaults."""
    with pytest.raises(ValueError, match="database password"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_PROD_SECRET,
            POSTGRES_PASSWORD=insecure_pwd,
            DATABASE_URL=f"postgresql+asyncpg://postgres_admin:{insecure_pwd}@db:5432/career_platform_prod",
            ALLOWED_HOSTS=VALID_PROD_HOSTS,
        )


def test_production_fails_on_default_db_url_password():
    """Verify production startup fails if DATABASE_URL contains default 'postgres:postgres'."""
    with pytest.raises(ValueError, match="database password"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_PROD_SECRET,
            POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/career_platform",
            ALLOWED_HOSTS=VALID_PROD_HOSTS,
        )


def test_production_fails_on_missing_db_password():
    """Verify production startup fails if PostgreSQL DATABASE_URL has no password."""
    with pytest.raises(ValueError, match="(?i)database password"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_PROD_SECRET,
            POSTGRES_PASSWORD=None,
            DATABASE_URL="postgresql+asyncpg://postgres@localhost:5432/career_platform",
            ALLOWED_HOSTS=VALID_PROD_HOSTS,
        )


# ---------------------------------------------------------------------------
# Production DEBUG and Docs Safeguards
# ---------------------------------------------------------------------------

def test_production_fails_if_debug_explicitly_true():
    """Verify production startup explicitly rejects DEBUG=True."""
    with pytest.raises(ValueError, match="DEBUG mode cannot be enabled"):
        Settings(
            APP_ENV="production",
            DEBUG=True,
            SECRET_KEY=VALID_PROD_SECRET,
            POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
            DATABASE_URL=VALID_PROD_DB_URL,
            ALLOWED_HOSTS=VALID_PROD_HOSTS,
        )


def test_production_defaults_debug_to_false_and_disables_docs():
    """Verify production defaults DEBUG to False and docs_enabled to False."""
    s = Settings(
        APP_ENV="production",
        SECRET_KEY=VALID_PROD_SECRET,
        POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
        DATABASE_URL=VALID_PROD_DB_URL,
        ALLOWED_HOSTS=VALID_PROD_HOSTS,
    )
    assert s.is_production is True
    assert s.DEBUG is False
    assert s.docs_enabled is False


def test_production_safe_docs_override():
    """Verify ENABLE_API_DOCS can safely enable API documentation in production without enabling DEBUG."""
    s = Settings(
        APP_ENV="production",
        ENABLE_API_DOCS=True,
        SECRET_KEY=VALID_PROD_SECRET,
        POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
        DATABASE_URL=VALID_PROD_DB_URL,
        ALLOWED_HOSTS=VALID_PROD_HOSTS,
    )
    assert s.is_production is True
    assert s.DEBUG is False
    assert s.docs_enabled is True


# ---------------------------------------------------------------------------
# Production Host Header and Wildcard Validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("invalid_hosts", [
    ["*"],
    ["api.example.com", "*"],
    "api.example.com, *",
    "*",
    "",
    [],
])
def test_production_rejects_wildcard_or_empty_allowed_hosts(invalid_hosts):
    """Verify production startup rejects wildcard '*' and empty host lists."""
    with pytest.raises(ValueError, match="ALLOWED_HOSTS"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_PROD_SECRET,
            POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
            DATABASE_URL=VALID_PROD_DB_URL,
            ALLOWED_HOSTS=invalid_hosts,
        )


# ---------------------------------------------------------------------------
# Full Application Integration (TrustedHost & Docs in Production)
# ---------------------------------------------------------------------------

def test_production_application_enforces_trusted_hosts_and_disables_docs():
    """
    Verify application behavior with production settings:
    - Swagger /docs and /openapi.json return 404
    - Requests with unauthorized Host headers return 400 (TrustedHostMiddleware)
    - Requests with authorized Host headers succeed
    """
    prod_settings = Settings(
        APP_ENV="production",
        SECRET_KEY=VALID_PROD_SECRET,
        POSTGRES_PASSWORD=VALID_PROD_DB_PWD,
        DATABASE_URL=VALID_PROD_DB_URL,
        ALLOWED_HOSTS=["api.career-platform.com", "testserver"],
    )

    prod_app = create_application(custom_settings=prod_settings)
    client = TestClient(prod_app)

    # 1. Docs and OpenAPI endpoints must return 404 in production
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 404

    redoc_resp = client.get("/redoc")
    assert redoc_resp.status_code == 404

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 404

    # 2. Health check with authorized host succeeds
    health_resp = client.get("/health", headers={"Host": "api.career-platform.com"})
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}

    # 3. Request with unauthorized host is blocked by TrustedHostMiddleware (HTTP 400)
    unauthorized_resp = client.get("/health", headers={"Host": "evil-attacker.com"})
    assert unauthorized_resp.status_code == 400
