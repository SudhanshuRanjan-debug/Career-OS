"""
Task model — unified polymorphic action item and follow-up tracking.
"""

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    priority: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", nullable=False
    )  # LOW, MEDIUM, HIGH, URGENT
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False, index=True
    )  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Polymorphic linkages
    related_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # APPLICATION, INTERVIEW, COMPANY, CONTACT, GENERAL
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    interview_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    application: Mapped["Application | None"] = relationship("Application", back_populates="tasks")
    interview: Mapped["Interview | None"] = relationship("Interview", back_populates="tasks")
    company: Mapped["Company | None"] = relationship("Company", back_populates="tasks")
    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="tasks")


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title} status={self.status}>"
