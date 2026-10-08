"""
Authentication and session management service.
Handles registration, login, token rotation, logout, and password resets.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    create_access_token,
    generate_refresh_token,
    generate_reset_token,
)
from app.models.user import User, RefreshToken, PasswordResetToken
from app.models.candidate_profile import CandidateProfile
from app.models.organization import Organization
from app.schemas.auth import UserRegisterRequest, UserLoginRequest

logger = logging.getLogger("auth_service")


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware UTC for cross-database comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt



async def register_user(
    db: AsyncSession,
    data: UserRegisterRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[User, str, str]:
    """
    Register a new user account.
    Creates user, initial candidate profile scaffold, and authenticated session.
    Returns (user, access_token, raw_refresh_token).
    """
    # 1. Check duplicate email
    email_check = await db.execute(
        select(User.id).where(User.email == data.email)
    )
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # 2. Check duplicate username
    username_check = await db.execute(
        select(User.id).where(User.username == data.username)
    )
    if username_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken",
        )

    # 3. Create user
    now = datetime.now(timezone.utc)
    hashed = hash_password(data.password)
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hashed,
        role=data.role,
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    db.add(user)
    await db.flush()  # Populates user.id

    # 4. Role-based entity initialization
    base_slug = None
    if data.role == "HIRER":
        if not data.organization_name or not data.organization_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name is required for recruiter registration",
            )
        import re
        org_name = data.organization_name.strip()
        base_slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-") or "org"

        # Check existing slug to prevent collision
        existing = (await db.execute(select(Organization.id).where(Organization.slug == base_slug))).scalar_one_or_none()
        slug = f"{base_slug}-{uuid4().hex[:6]}" if existing else base_slug

        org = Organization(
            owner_user_id=user.id,
            name=org_name,
            slug=slug,
            created_at=now,
            updated_at=now,
        )
        db.add(org)
    else:
        # Default CANDIDATE profile scaffold
        profile = CandidateProfile(
            user_id=user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)

    # 5. Create initial refresh token session
    raw_refresh = generate_refresh_token()
    token_hashed = hash_token(raw_refresh)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hashed,
        expires_at=expires_at,
        created_at=now,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(refresh_record)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        if data.role == "HIRER" and base_slug:
            # Handle concurrent race condition: retry with unique random suffix
            user.id = user.id
            db.add(user)
            unique_slug = f"{base_slug}-{uuid4().hex[:8]}"
            org = Organization(
                owner_user_id=user.id,
                name=org_name,
                slug=unique_slug,
                created_at=now,
                updated_at=now,
            )
            db.add(org)
            db.add(refresh_record)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Organization with this identifier could not be registered due to a conflict",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration failed due to a unique constraint violation",
            )

    await db.refresh(user)

    # 6. Issue access token (contains role for client convenience; DB role remains authoritative)
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "username": user.username, "role": user.role},
    )

    return user, access_token, raw_refresh


async def authenticate_user(
    db: AsyncSession,
    data: UserLoginRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[User, str, str]:
    """
    Authenticate user credentials.
    Returns (user, access_token, raw_refresh_token).
    """
    result = await db.execute(
        select(User).where(
            User.email == data.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Generic credential error prevents account enumeration
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or disabled",
        )

    now = datetime.now(timezone.utc)
    user.last_login_at = now

    # Issue refresh token and session record
    raw_refresh = generate_refresh_token()
    token_hashed = hash_token(raw_refresh)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hashed,
        expires_at=expires_at,
        created_at=now,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(refresh_record)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "username": user.username, "role": user.role},
    )

    return user, access_token, raw_refresh


async def rotate_refresh_token(
    db: AsyncSession,
    raw_refresh_token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, str]:
    """
    Rotate refresh token:
    1. Validate existing token hash.
    2. Detect reuse of already-revoked tokens (triggering revocation of all user tokens).
    3. Invalidate old token.
    4. Issue new refresh token and fresh access token.
    Returns (new_access_token, new_raw_refresh_token).
    """
    now = datetime.now(timezone.utc)
    incoming_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # REUSE DETECTION: A revoked token is being presented again!
    if token_record.revoked_at is not None:
        logger.warning(
            "Security alert: Revoked refresh token reuse attempted for user %s",
            token_record.user_id,
        )
        # Invalidate all active sessions for this user as a safeguard
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == token_record.user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Expiration check
    if _ensure_utc(token_record.expires_at) <= now:
        token_record.revoked_at = now

        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user state
    user_result = await db.execute(
        select(User).where(
            User.id == token_record.user_id,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        token_record.revoked_at = now
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Revoke old token
    token_record.revoked_at = now

    # Issue new rotated refresh token
    new_raw_refresh = generate_refresh_token()
    new_token_hash = hash_token(new_raw_refresh)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=new_expires_at,
        created_at=now,
        user_agent=user_agent or token_record.user_agent,
        ip_address=ip_address or token_record.ip_address,
    )
    db.add(new_refresh_record)
    await db.commit()

    new_access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "username": user.username, "role": user.role},
    )

    return new_access_token, new_raw_refresh


async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a specific refresh token (used during logout)."""
    now = datetime.now(timezone.utc)
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token_record = result.scalar_one_or_none()
    if token_record:
        token_record.revoked_at = now
        await db.commit()


async def initiate_password_reset(db: AsyncSession, email: str) -> None:
    """
    Generate password reset token for given email.
    Always completes silently to prevent email enumeration.
    """
    result = await db.execute(
        select(User).where(
            User.email == email.strip().lower(),
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        return

    now = datetime.now(timezone.utc)
    raw_token = generate_reset_token()
    token_hash = hash_token(raw_token)
    expires_at = now + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=now,
    )
    db.add(reset_record)
    await db.commit()

    logger.info("Password reset token generated for user %s (dispatching email in Stage 9)", user.id)


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    """
    Validate reset token, update user password, and revoke all existing sessions.
    """
    now = datetime.now(timezone.utc)
    token_hash = hash_token(raw_token)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
    )
    reset_record = result.scalar_one_or_none()

    if not reset_record or _ensure_utc(reset_record.expires_at) <= now:
        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user_result = await db.execute(
        select(User).where(
            User.id == reset_record.user_id,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # 1. Update password
    user.hashed_password = hash_password(new_password)
    user.updated_at = now

    # 2. Mark reset token as used
    reset_record.used_at = now

    # 3. Revoke ALL active refresh tokens for this user across all devices
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await db.commit()


async def get_user_sessions(db: AsyncSession, user_id: UUID) -> list[RefreshToken]:
    """Retrieve active session records for a tenant user."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_user_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> bool:
    """Revoke a specific session ensuring tenant isolation."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return False
    record.revoked_at = now
    await db.commit()
    return True
