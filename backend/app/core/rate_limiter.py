"""
Authentication rate limiter: in-memory sliding window rate limiting
with composite keying for shared-network resilience and HTTP 429 enforcement.

Deployment Architecture & Limitations:
-------------------------------------
- Storage model: Process-local in-memory sliding-window counter.
- Concurrency: Thread-safe via threading.Lock().
- Limitations: In multi-worker or multi-container deployments without sticky sessions,
  limits apply per worker/process rather than globally across the cluster.
  For clustered multi-node horizontal scaling, a distributed backend (e.g. Redis)
  can be configured via a shared adapter.
- Shared network resilience: For login and password reset flows, rate limiting uses
  composite keys combining client IP and target account identifier, preventing an
  attacker from locking out other legitimate users behind a shared NAT/corporate proxy,
  paired with a broader IP-level flood threshold.
"""

import threading
import time
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter."""

    def __init__(self) -> None:
        self._entries: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        """
        Check and record a request under the sliding time window.
        Raises HTTPException(429) if limit is exceeded.
        """
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.monotonic()

        with self._lock:
            # Purge timestamps outside the sliding window
            timestamps = [
                t for t in self._entries.get(key, []) if (now - t) < window_seconds
            ]

            if len(timestamps) >= max_requests:
                oldest_timestamp = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest_timestamp)) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)
            self._entries[key] = timestamps

            # Opportunistic cleanup to prevent memory growth
            if len(self._entries) > 2000:
                self._cleanup_expired(now)

    def _cleanup_expired(self, now: float) -> None:
        """Remove keys with no active timestamps."""
        keys_to_delete = []
        for key, ts_list in self._entries.items():
            active = [t for t in ts_list if (now - t) < 3600]
            if not active:
                keys_to_delete.append(key)
            else:
                self._entries[key] = active
        for key in keys_to_delete:
            self._entries.pop(key, None)

    def reset(self) -> None:
        """Clear all rate limit buckets. Used for test isolation."""
        with self._lock:
            self._entries.clear()


# Global in-memory rate limiter instance
limiter = InMemoryRateLimiter()


def extract_client_ip(request: Request) -> str:
    """Extract client IP safely from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


# -----------------------------------------------------------------------------
# Endpoint-Specific Rate Limiters
# -----------------------------------------------------------------------------

def rate_limit_login(request: Request, identifier: str) -> None:
    """
    Rate limit login attempts.
    Dual-check strategy for shared network safety:
    1. Account + IP key: Limits attempts against a specific account from this IP.
    2. IP burst ceiling: Broader ceiling to prevent brute-force dictionary attacks.
    """
    client_ip = extract_client_ip(request)
    normalized = identifier.strip().lower()

    # Account-specific limit (protects individual accounts without locking out entire NAT)
    account_key = f"login:account_ip:{client_ip}:{normalized}"
    limiter.check(
        key=account_key,
        max_requests=settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )

    # Broad IP ceiling (prevents massive credential stuffing from a single IP)
    ip_key = f"login:ip:{client_ip}"
    limiter.check(
        key=ip_key,
        max_requests=settings.RATE_LIMIT_LOGIN_IP_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_LOGIN_IP_WINDOW_SECONDS,
    )


def rate_limit_register(request: Request) -> None:
    """Rate limit user registration attempts per IP."""
    client_ip = extract_client_ip(request)
    key = f"register:ip:{client_ip}"
    limiter.check(
        key=key,
        max_requests=settings.RATE_LIMIT_REGISTER_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
    )


def rate_limit_refresh(request: Request) -> None:
    """Rate limit token refresh calls per IP."""
    client_ip = extract_client_ip(request)
    key = f"refresh:ip:{client_ip}"
    limiter.check(
        key=key,
        max_requests=settings.RATE_LIMIT_REFRESH_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_REFRESH_WINDOW_SECONDS,
    )


def rate_limit_forgot_password(request: Request, email: str) -> None:
    """
    Rate limit password reset requests per email and per IP.
    Prevents SMTP abuse and email enumeration.
    """
    client_ip = extract_client_ip(request)
    normalized = email.strip().lower()

    # Per email+IP
    account_key = f"forgot:email_ip:{client_ip}:{normalized}"
    limiter.check(
        key=account_key,
        max_requests=settings.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS,
    )

    # Per IP broad limit
    ip_key = f"forgot:ip:{client_ip}"
    limiter.check(
        key=ip_key,
        max_requests=settings.RATE_LIMIT_FORGOT_PASSWORD_IP_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_FORGOT_PASSWORD_IP_WINDOW_SECONDS,
    )


def rate_limit_reset_password(request: Request) -> None:
    """Rate limit password reset token submissions per IP."""
    client_ip = extract_client_ip(request)
    key = f"reset_password:ip:{client_ip}"
    limiter.check(
        key=key,
        max_requests=settings.RATE_LIMIT_RESET_PASSWORD_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_RESET_PASSWORD_WINDOW_SECONDS,
    )


def rate_limit_change_password(user_id: UUID) -> None:
    """Rate limit authenticated password changes per user."""
    key = f"change_password:user:{user_id}"
    limiter.check(
        key=key,
        max_requests=settings.RATE_LIMIT_CHANGE_PASSWORD_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_CHANGE_PASSWORD_WINDOW_SECONDS,
    )
