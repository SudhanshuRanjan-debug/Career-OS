"""
Interview and InterviewPreparation models.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interview_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # PHONE, VIDEO, ON_SITE, TECHNICAL, PANEL, HR, SYSTEM_DESIGN, BEHAVIORAL
    stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    duration_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="SCHEDULED", nullable=False, index=True
    )  # SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED
    result: Mapped[str | None] = mapped_column(String(30), nullable=True)  # PASSED, FAILED, PENDING, CANCELLED
    interviewer_names: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
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

    preparation: Mapped["InterviewPreparation"] = relationship(
        "InterviewPreparation", back_populates="interview", uselist=False, cascade="all, delete-orphan"
    )
    application: Mapped["Application | None"] = relationship(
        "Application", back_populates="interviews"
    )
    company: Mapped["Company | None"] = relationship(
        "Company", back_populates="interviews"
    )
    contact: Mapped["Contact | None"] = relationship(
        "Contact", back_populates="interviews"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="interview"
    )

    def __repr__(self) -> str:
        return f"<Interview id={self.id} title={self.title} status={self.status}>"


class InterviewPreparation(Base):
    __tablename__ = "interview_preparations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    company_research: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_research: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions_to_ask: Mapped[str | None] = mapped_column(Text, nullable=True)
    personal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    preparation_checklist: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    post_interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    interview: Mapped["Interview"] = relationship("Interview", back_populates="preparation")
