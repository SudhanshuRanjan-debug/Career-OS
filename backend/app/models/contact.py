"""
Contact model — recruiter, manager, interviewer, and referral network directory.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship
from app.db.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # RECRUITER, HIRING_MANAGER, INTERVIEWER, EMPLOYEE, REFERRAL, OTHER
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
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

    company: Mapped["Company | None"] = orm_relationship("Company", back_populates="contacts")
    applications: Mapped[list["Application"]] = orm_relationship("Application", back_populates="contact")
    interviews: Mapped[list["Interview"]] = orm_relationship("Interview", back_populates="contact")
    tasks: Mapped[list["Task"]] = orm_relationship("Task", back_populates="contact")

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.first_name} {self.last_name or ''}>"
