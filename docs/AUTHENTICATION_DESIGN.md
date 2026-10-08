# Authentication Design
## Career & Job Application Management Platform

**Version:** 1.0.0
**Date:** 2026-09-07

---

## 1. Authentication Strategy

- **Mechanism:** JWT (JSON Web Tokens) with rotating refresh tokens
- **Access Token:** Short-lived (15 minutes), stored in JavaScript memory (not localStorage)
- **Refresh Token:** Long-lived (7 days), stored in httpOnly Secure SameSite=Strict cookie
- **Password Hashing:** bcrypt with work factor 12
- **Password Reset:** Secure random token, single-use, expires in 1 hour
- **Session Tracking:** Refresh tokens stored in DB with device/IP metadata for session management

---

## 2. Token Design

### 2.1 Access Token (JWT)

```json
Header: { "alg": "HS256", "typ": "JWT" }

Payload:
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "type": "access",
  "iat": 1693000000,
  "exp": 1693000900    // 15 minutes
}
```

Signed with `SECRET_KEY` (minimum 32 bytes, random).

### 2.2 Refresh Token

- 64-byte cryptographically random token (secrets.token_urlsafe(64))
- Stored as bcrypt hash in `refresh_tokens` table
- Sent as httpOnly cookie: `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh`
- Scoped to `/api/v1/auth/refresh` path only (not leaked on other requests)
- Expires in 7 days
- Revoked on logout, password change, and account deletion

---

## 3. Registration Flow & Role Selection

```
POST /auth/register
{
  "email": "user@example.com",
  "username": "jsmith",
  "password": "SecurePass123!",
  "role": "CANDIDATE",               // "CANDIDATE" or "HIRER" (default: "CANDIDATE")
  "organization_name": "Acme Inc"    // Required / optional for HIRER role
}

Validation:
  - email: valid format, not already registered
  - username: 3-50 chars, alphanumeric + underscore, not taken
  - password: min 8 chars, at least 1 uppercase, 1 number, 1 special char
  - role: must be "CANDIDATE" or "HIRER"

On success:
  1. Hash password with bcrypt(cost=12)
  2. Create users row with role (default: "CANDIDATE")
  3. If role == "CANDIDATE":
       Create candidate_profiles row (empty scaffold)
     If role == "HIRER":
       Create organizations row (owner_user_id = user.id, name = organization_name or f"{username}'s Organization")
  4. Issue access_token (with sub, email, and informational role) + refresh_token
  5. Set HttpOnly refresh cookie
  6. Return: { id, email, username, role, created_at, access_token }

Role Immutability Policy:
  - Account role is chosen at registration and cannot be converted post-creation.
  - Users requiring both roles must register separate accounts with distinct emails.
```

---

## 4. Login Flow

```
POST /auth/login
{ "email": "...", "password": "..." }

Steps:
  1. Look up user by email
  2. Verify user is active (is_active=true, deleted_at IS NULL)
  3. Compare password with bcrypt hash
  4. On success:
       - Update last_login_at
       - Generate new access_token
       - Generate new refresh_token (store hash in DB)
       - Set refresh cookie
       - Return access_token

Failure cases:
  - User not found: generic error (don't reveal whether email exists)
  - Wrong password: generic error
  - Account inactive: specific error
  - Account deleted: generic error (same as not found)
```

---

## 5. Token Refresh Flow

```
POST /api/v1/auth/refresh
Cookie: refresh_token=<token>

Steps:
  1. Extract refresh_token from cookie
  2. Hash it and look up in refresh_tokens table
  3. Verify: not revoked (revoked_at IS NULL), not expired (expires_at > now)
  4. Load user by user_id
  5. Verify user is active
  6. Issue new access_token
  7. Optionally: rotate refresh token (revoke old, issue new)
  8. Return new access_token

Silent refresh strategy (frontend):
  - Axios interceptor catches 401 responses
  - Automatically calls /auth/refresh
  - Retries original request with new access_token
  - If refresh fails, redirect to /signin
```

---

## 6. Logout Flow

```
POST /auth/logout
Authorization: Bearer <access_token>

Steps:
  1. Identify refresh_token from cookie (if present)
  2. Revoke the refresh_token record (set revoked_at = now())
  3. Clear the cookie: Set-Cookie: refresh_token=; Max-Age=0
  4. Return { "message": "Logged out" }

Note: Access tokens are short-lived and cannot be actively revoked.
      They expire within 15 minutes of logout automatically.
      For sensitive actions requiring immediate revocation, use refresh token rotation.
```

---

## 7. Password Reset Flow

```
Step 1: Request reset
  POST /auth/forgot-password
  { "email": "..." }

  - Always return same response regardless of whether email exists
    (prevents email enumeration)
  - If email found:
      1. Generate 32-byte random token: secrets.token_urlsafe(32)
      2. Hash it: sha256(token)
      3. Store hash in password_reset_tokens: { user_id, token_hash, expires_at: now+1h }
      4. Send email with: https://app.domain.com/reset-password?token=<raw_token>

Step 2: Reset password
  POST /auth/reset-password
  { "token": "...", "new_password": "..." }

  1. Hash incoming token: sha256(token)
  2. Look up password_reset_tokens by hash
  3. Verify: not used (used_at IS NULL), not expired (expires_at > now)
  4. Load user
  5. Hash new password
  6. Update users.hashed_password
  7. Mark token as used: used_at = now()
  8. Revoke ALL refresh_tokens for this user (force re-login on all devices)
  9. Return { "message": "Password reset successful" }
```

---

## 8. Protected Route & Role Authorization Dependencies

```python
# backend/app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Authoritative user resolver.
    The database users table is the SOLE AUTHORITATIVE SOURCE for user state and role.
    The JWT role claim is for client-side routing convenience only.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    # Reload user fresh from PostgreSQL
    result = await db.execute(
        select(User).where(User.id == UUID(payload["sub"]), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user

def require_role(required_role: str):
    """Enforce server-side role authorization from authoritative database model."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: this endpoint requires {required_role} role",
            )
        return current_user
    return role_checker

require_candidate = require_role("CANDIDATE")
require_hirer = require_role("HIRER")
```

All protected endpoints declare `current_user: User = Depends(get_current_user)`.

---

## 9. Data Isolation Enforcement

Every service method that reads or writes user data includes the `user_id` filter:

```python
# Example: Get applications — ALWAYS filter by user_id
def get_applications(db, user_id: UUID, filters: ...):
    query = db.query(Application).filter(
        Application.user_id == user_id  # ← enforced at service layer
    )
    ...
```

This prevents horizontal privilege escalation even if a bug allows a user to supply another user's resource ID.

---

## 10. Security Headers

Nginx will be configured to set:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 11. Rate Limiting (Stage 13)

To be implemented in Stage 13 (Security Hardening):

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 10 req/min per IP |
| POST /auth/register | 5 req/min per IP |
| POST /auth/forgot-password | 5 req/min per IP |
| POST /auth/reset-password | 5 req/min per IP |
| All other API endpoints | 200 req/min per user |

Implementation: FastAPI middleware + Redis (or in-memory for MVP).

---

## 12. Session Management

Users can view and revoke active sessions:

```
GET /settings/sessions
→ Returns list of active refresh_tokens:
  [ { "id": "uuid", "created_at": "...", "user_agent": "Chrome/Windows", "ip": "..." } ]

DELETE /settings/sessions/:id
→ Revokes specific session

DELETE /settings/sessions
→ Revokes all sessions (logs out all devices)
```

---

## 13. Future: Email Verification

Not implemented in MVP. Design placeholders:
- `users.is_verified` column already exists
- Verification flow will use same token pattern as password reset
- Until implemented, users are auto-verified on registration

---

## 14. Future: Two-Factor Authentication

Not implemented in MVP. Extension point:
- `users` table will gain `totp_secret` column (encrypted at rest)
- Login flow will add optional TOTP step after password check
- Library: `pyotp`

---

## 15. Environment Variables

```env
# .env
SECRET_KEY=<minimum 32 random bytes, base64 encoded>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
```
