"""
Security utilities: JWT encoding/decoding, password hashing, and token hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash password using bcrypt with configured cost factor."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Token hashing (SHA-256 for opaque DB-stored tokens)
# ---------------------------------------------------------------------------

def hash_token(raw_token: str) -> str:
    """
    Produce a deterministic SHA-256 hex digest of an opaque token.
    Used for indexed storage and lookup of refresh and reset tokens.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    """Create signed access token JWT valid for ACCESS_TOKEN_EXPIRE_MINUTES."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate an access token JWT. Returns payload if valid, None otherwise."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Opaque token generation
# ---------------------------------------------------------------------------

def generate_refresh_token() -> str:
    """Generate a cryptographically secure 64-byte URL-safe refresh token."""
    return secrets.token_urlsafe(64)


def generate_reset_token() -> str:
    """Generate a cryptographically secure 32-byte URL-safe password reset token."""
    return secrets.token_urlsafe(32)
