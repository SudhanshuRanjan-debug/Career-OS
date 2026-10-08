"""
Pydantic schemas for authentication, tokens, user registration, and sessions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Alphanumeric username with underscores allowed",
    )
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    role: str = Field("CANDIDATE", description="Account role: CANDIDATE or HIRER")
    organization_name: Optional[str] = Field(None, max_length=255, description="Organization name (required for HIRER)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        val = v.strip().upper()
        if val not in ("CANDIDATE", "HIRER"):
            raise ValueError("Role must be either CANDIDATE or HIRER")
        return val

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")
    password: str = Field(..., description="Password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: str = "CANDIDATE"
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AccessTokenOnlyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Optional raw refresh token if not in cookie")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, description="User email address")


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Password reset verification token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_current: bool = False

    model_config = {"from_attributes": True}
