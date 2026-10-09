"""
Authentication endpoints: register, login, refresh, logout, me, and password resets.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limiter import (
    rate_limit_forgot_password,
    rate_limit_login,
    rate_limit_refresh,
    rate_limit_register,
    rate_limit_reset_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    AccessTokenOnlyResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SessionResponse,
)
from app.services import auth_service

router = APIRouter()


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Centralized helper for setting the secure HttpOnly refresh token cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Centralized helper for deleting the refresh token cookie."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


def _extract_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user-agent from request headers."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.headers.get("x-forwarded-for")
    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    return ip_address, user_agent


# ---------------------------------------------------------------------------
# Registration & Login
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_register(request)
    ip_address, user_agent = _extract_client_info(request)
    user, access_token, raw_refresh = await auth_service.register_user(
        db=db,
        data=data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user credentials",
)
async def login(
    data: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_login(request, data.email)
    ip_address, user_agent = _extract_client_info(request)
    user, access_token, raw_refresh = await auth_service.authenticate_user(
        db=db,
        data=data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Session & Token Management
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=AccessTokenOnlyResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue fresh access token",
)
async def refresh(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_refresh(request)
    # Read refresh token from HttpOnly cookie first, fall back to body
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token and body and body.refresh_token:
        raw_token = body.refresh_token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ip_address, user_agent = _extract_client_info(request)
    new_access_token, new_raw_refresh = await auth_service.rotate_refresh_token(
        db=db,
        raw_refresh_token=raw_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    _set_refresh_cookie(response, new_raw_refresh)
    return AccessTokenOnlyResponse(access_token=new_access_token, token_type="bearer")


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke active refresh session and clear cookie",
)
async def logout(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token and body and body.refresh_token:
        raw_token = body.refresh_token

    if raw_token:
        await auth_service.revoke_refresh_token(db=db, raw_refresh_token=raw_token)

    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate password reset flow",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_forgot_password(request, data.email)
    await auth_service.initiate_password_reset(db=db, email=data.email)
    return MessageResponse(
        message="If this email is registered, password reset instructions have been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit new password with verification token",
)
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_reset_password(request)
    await auth_service.reset_password(
        db=db,
        raw_token=data.token,
        new_password=data.new_password,
    )
    return MessageResponse(
        message="Password reset successful. You may now log in with your new password."
    )


# ---------------------------------------------------------------------------
# Active Session Inspection
# ---------------------------------------------------------------------------

@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List active authenticated sessions for current user",
)
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await auth_service.get_user_sessions(db=db, user_id=current_user.id)
    current_cookie = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    current_cookie_hash = auth_service.hash_token(current_cookie) if current_cookie else None

    responses = []
    for s in sessions:
        item = SessionResponse(
            id=s.id,
            created_at=s.created_at,
            expires_at=s.expires_at,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            is_current=(s.token_hash == current_cookie_hash),
        )
        responses.append(item)
    return responses


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke an active user session",
)
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await auth_service.revoke_user_session(
        db=db, user_id=current_user.id, session_id=session_id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return MessageResponse(message="Session revoked successfully")
