"""
Candidate profile and preferences models.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    professional_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    total_experience_yrs: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_to_work: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_photo_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<CandidateProfile user_id={self.user_id}>"


class CandidatePreferences(Base):
    __tablename__ = "candidate_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    desired_job_titles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    preferred_industries: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    preferred_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    work_arrangement: Mapped[str | None] = mapped_column(String(30), nullable=True)  # REMOTE, HYBRID, ON_SITE, ANY
    employment_type: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)  # FULL_TIME, PART_TIME, etc.
    min_compensation: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_compensation: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    compensation_period: Mapped[str] = mapped_column(String(20), default="ANNUAL", nullable=False)
    availability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_authorization: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    relocation_preference: Mapped[str | None] = mapped_column(String(30), nullable=True)
    preferred_company_sizes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<CandidatePreferences user_id={self.user_id}>"
