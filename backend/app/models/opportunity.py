"""
Opportunity and SavedOpportunity models.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)  # MANUAL, URL_IMPORT, REFERRAL, etc.
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # REMOTE, HYBRID, ON_SITE
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    compensation_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", nullable=False, index=True
    )  # ACTIVE, SAVED, CONSIDERING, APPLIED, ARCHIVED, NOT_INTERESTED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company | None"] = relationship("Company")
    job_posting: Mapped["JobPosting | None"] = relationship("JobPosting")
    saved_by_users: Mapped[list["SavedOpportunity"]] = relationship(
        "SavedOpportunity", back_populates="opportunity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Opportunity id={self.id} title={self.title} status={self.status}>"


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"
    __table_args__ = (
        UniqueConstraint("user_id", "opportunity_id", name="uq_user_opportunity_saved"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="saved_by_users")
