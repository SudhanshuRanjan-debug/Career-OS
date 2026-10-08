"""
JobPosting and JobPostingSkill models — recruiter-published job listings.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_type: Mapped[str] = mapped_column(
        String(20), default="ON_SITE", nullable=False
    )  # REMOTE, HYBRID, ON_SITE
    employment_type: Mapped[str] = mapped_column(
        String(50), default="FULL_TIME", nullable=False
    )  # FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP
    experience_level: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # ENTRY, MID, SENIOR, LEAD, EXECUTIVE
    compensation_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )  # Default INR, extensible to other ISO currencies
    status: Mapped[str] = mapped_column(
        String(20), default="DRAFT", nullable=False, index=True
    )  # DRAFT, PUBLISHED, CLOSED, ARCHIVED
    deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="job_postings")
    creator: Mapped["User"] = relationship("User")
    skills: Mapped[list["JobPostingSkill"]] = relationship(
        "JobPostingSkill", back_populates="job_posting", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="job_posting"
    )

    def __repr__(self) -> str:
        return f"<JobPosting id={self.id} title={self.title} status={self.status}>"


class JobPostingSkill(Base):
    __tablename__ = "job_posting_skills"
    __table_args__ = (
        UniqueConstraint("job_posting_id", "name", name="uq_jps_job_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    job_posting: Mapped["JobPosting"] = relationship("JobPosting", back_populates="skills")

    def __repr__(self) -> str:
        return f"<JobPostingSkill job_id={self.job_posting_id} name={self.name}>"
