"""
Application, StageHistory, Note, Followup, Document link, and Activity models.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        Index(
            "uq_applications_user_job_posting",
            "user_id",
            "job_posting_id",
            unique=True,
            postgresql_where=text("job_posting_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    # Job information snapshot
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_location_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    compensation_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Application state & stage tracking
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)
    current_stage: Mapped[str] = mapped_column(String(50), default="APPLIED", nullable=False, index=True)
    applied_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Immutable historical references
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    cover_letter_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)

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
    stage_history: Mapped[list["ApplicationStageHistory"]] = relationship(
        "ApplicationStageHistory", back_populates="application", cascade="all, delete-orphan"
    )
    notes: Mapped[list["ApplicationNote"]] = relationship(
        "ApplicationNote", back_populates="application", cascade="all, delete-orphan"
    )
    followups: Mapped[list["ApplicationFollowup"]] = relationship(
        "ApplicationFollowup", back_populates="application", cascade="all, delete-orphan"
    )
    activity: Mapped[list["ApplicationActivity"]] = relationship(
        "ApplicationActivity", back_populates="application", cascade="all, delete-orphan"
    )
    company: Mapped["Company | None"] = relationship(
        "Company", back_populates="applications"
    )
    opportunity: Mapped["Opportunity | None"] = relationship(
        "Opportunity"
    )
    job_posting: Mapped["JobPosting | None"] = relationship(
        "JobPosting", back_populates="applications"
    )
    contact: Mapped["Contact | None"] = relationship(
        "Contact", back_populates="applications"
    )
    resume: Mapped["Resume | None"] = relationship(
        "Resume", foreign_keys=[resume_id]
    )
    cover_letter: Mapped["Document | None"] = relationship(
        "Document", foreign_keys=[cover_letter_doc_id]
    )
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    answers: Mapped[list["ApplicationAnswer"]] = relationship(
        "ApplicationAnswer", back_populates="application", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview", back_populates="application"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="application"
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} title={self.job_title} company={self.company_name}>"



class ApplicationStageHistory(Base):
    __tablename__ = "application_stage_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_user: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    application: Mapped["Application"] = relationship("Application", back_populates="stage_history")


class ApplicationNote(Base):
    __tablename__ = "application_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    application: Mapped["Application"] = relationship("Application", back_populates="notes")


class ApplicationFollowup(Base):
    __tablename__ = "application_followups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    application: Mapped["Application"] = relationship("Application", back_populates="followups")


class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    __table_args__ = (
        UniqueConstraint("application_id", "document_id", name="uq_app_document"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    application: Mapped["Application"] = relationship("Application", back_populates="documents")
    document: Mapped["Document"] = relationship("Document")



class ApplicationActivity(Base):
    __tablename__ = "application_activity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    application: Mapped["Application"] = relationship("Application", back_populates="activity")
