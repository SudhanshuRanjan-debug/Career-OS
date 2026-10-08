"""
Date and time utility helpers.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_utc(dt: datetime | None) -> str | None:
    """Convert datetime to ISO 8601 UTC string."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
