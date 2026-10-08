"""001_initial_schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_username", "users", ["username"])

    # 2. password_reset_tokens
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_password_reset_user", "password_reset_tokens", ["user_id"])

    # 3. refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    op.create_index("idx_refresh_tokens_user", "refresh_tokens", ["user_id"])

    # 4. candidate_profiles
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("preferred_name", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("location_city", sa.String(100), nullable=True),
        sa.Column("location_state", sa.String(100), nullable=True),
        sa.Column("location_country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(60), nullable=True),
        sa.Column("headline", sa.String(255), nullable=True),
        sa.Column("professional_summary", sa.Text(), nullable=True),
        sa.Column("career_objective", sa.Text(), nullable=True),
        sa.Column("current_role", sa.String(150), nullable=True),
        sa.Column("total_experience_yrs", sa.Numeric(4, 1), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("open_to_work", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("profile_photo_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_candidate_profiles_user", "candidate_profiles", ["user_id"])

    # 5. candidate_preferences
    op.create_table(
        "candidate_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("desired_job_titles", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_industries", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_locations", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("work_arrangement", sa.String(30), nullable=True),
        sa.Column("employment_type", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("min_compensation", sa.Numeric(12, 2), nullable=True),
        sa.Column("target_compensation", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("compensation_period", sa.String(20), server_default="ANNUAL", nullable=False),
        sa.Column("availability", sa.String(50), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("work_authorization", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("relocation_preference", sa.String(30), nullable=True),
        sa.Column("preferred_company_sizes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_candidate_preferences_user", "candidate_preferences", ["user_id"])

    # 6. educations
    op.create_table(
        "educations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(100), nullable=True),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("grade", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_educations_user", "educations", ["user_id"])

    # 7. experiences
    op.create_table(
        "experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("location_type", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_experiences_user", "experiences", ["user_id"])

    # 8. projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role", sa.String(150), nullable=True),
        sa.Column("tech_stack", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("repo_url", sa.String(500), nullable=True),
        sa.Column("project_type", sa.String(50), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_ongoing", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_projects_user", "projects", ["user_id"])

    # 9. skills
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("proficiency", sa.String(30), nullable=True),
        sa.Column("years_of_exp", sa.Numeric(4, 1), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_skills_user", "skills", ["user_id"])

    # 10. certifications
    op.create_table(
        "certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuing_org", sa.String(255), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("credential_id", sa.String(255), nullable=True),
        sa.Column("credential_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_certifications_user", "certifications", ["user_id"])

    # 11. achievements
    op.create_table(
        "achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("issuer", sa.String(255), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_achievements_user", "achievements", ["user_id"])

    # 12. languages
    op.create_table(
        "languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("proficiency", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_languages_user", "languages", ["user_id"])

    # 13. profile_links
    op.create_table(
        "profile_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_profile_links_user", "profile_links", ["user_id"])

    # 14. resumes
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(500), unique=True, nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_resumes_user", "resumes", ["user_id"])

    # 15. documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("doc_type", sa.String(30), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(500), unique=True, nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_documents_user", "documents", ["user_id"])

    # 16. companies
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_companies_user", "companies", ["user_id"])

    # 17. contacts
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("contact_type", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("relationship", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_contacts_user", "contacts", ["user_id"])
    op.create_index("idx_contacts_company", "contacts", ["company_id"])

    # 18. opportunities
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("location_type", sa.String(20), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("compensation_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_currency", sa.String(10), nullable=True),
        sa.Column("posted_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_opportunities_user", "opportunities", ["user_id"])
    op.create_index("idx_opportunities_status", "opportunities", ["status"])

    # 19. saved_opportunities
    op.create_table(
        "saved_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "opportunity_id", name="uq_user_opportunity_saved"),
    )
    op.create_index("idx_saved_opportunities_user", "saved_opportunities", ["user_id"])

    # 20. applications
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("job_location", sa.String(255), nullable=True),
        sa.Column("job_location_type", sa.String(20), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("job_url", sa.String(1000), nullable=True),
        sa.Column("compensation_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_currency", sa.String(10), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("current_stage", sa.String(50), server_default="APPLIED", nullable=False),
        sa.Column("applied_date", sa.Date(), nullable=True),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cover_letter_doc_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("priority", sa.String(20), server_default="MEDIUM", nullable=False),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_applications_user", "applications", ["user_id"])
    op.create_index("idx_applications_status", "applications", ["user_id", "status"])
    op.create_index("idx_applications_stage", "applications", ["user_id", "current_stage"])

    # 21. application_stage_history
    op.create_table(
        "application_stage_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_stage", sa.String(50), nullable=True),
        sa.Column("to_stage", sa.String(50), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("changed_by_user", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("idx_stage_history_app", "application_stage_history", ["application_id"])

    # 22. application_notes
    op.create_table(
        "application_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_app_notes_app", "application_notes", ["application_id"])

    # 23. application_followups
    op.create_table(
        "application_followups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_app_followups_app", "application_followups", ["application_id"])

    # 24. application_documents
    op.create_table(
        "application_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("application_id", "document_id", name="uq_app_document"),
    )

    # 25. qa_vault_entries
    op.create_table(
        "qa_vault_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_template", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_qa_vault_user", "qa_vault_entries", ["user_id"])

    # 26. application_answers
    op.create_table(
        "application_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qa_vault_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("qa_vault_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_app_answers_app", "application_answers", ["application_id"])

    # 27. application_activity
    op.create_table(
        "application_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_data", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_activity_app", "application_activity", ["application_id"])

    # 28. interviews
    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("interview_type", sa.String(50), nullable=True),
        sa.Column("stage", sa.String(100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_mins", sa.Integer(), nullable=True),
        sa.Column("meeting_link", sa.String(500), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="SCHEDULED", nullable=False),
        sa.Column("result", sa.String(30), nullable=True),
        sa.Column("interviewer_names", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_interviews_user", "interviews", ["user_id"])
    op.create_index("idx_interviews_scheduled", "interviews", ["user_id", "scheduled_at"])

    # 29. interview_preparations
    op.create_table(
        "interview_preparations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("company_research", sa.Text(), nullable=True),
        sa.Column("role_research", sa.Text(), nullable=True),
        sa.Column("questions_to_ask", sa.Text(), nullable=True),
        sa.Column("personal_notes", sa.Text(), nullable=True),
        sa.Column("preparation_checklist", postgresql.JSONB(), nullable=True),
        sa.Column("post_interview_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_interview_prep_interview", "interview_preparations", ["interview_id"])

    # 30. tasks
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.String(20), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_type", sa.String(30), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_tasks_user", "tasks", ["user_id"])
    op.create_index("idx_tasks_due", "tasks", ["user_id", "due_date"])

    # 31. notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_type", sa.String(30), nullable=True),
        sa.Column("related_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id", "is_read"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("tasks")
    op.drop_table("interview_preparations")
    op.drop_table("interviews")
    op.drop_table("application_activity")
    op.drop_table("application_answers")
    op.drop_table("qa_vault_entries")
    op.drop_table("application_documents")
    op.drop_table("application_followups")
    op.drop_table("application_notes")
    op.drop_table("application_stage_history")
    op.drop_table("applications")
    op.drop_table("saved_opportunities")
    op.drop_table("opportunities")
    op.drop_table("contacts")
    op.drop_table("companies")
    op.drop_table("documents")
    op.drop_table("resumes")
    op.drop_table("profile_links")
    op.drop_table("languages")
    op.drop_table("achievements")
    op.drop_table("certifications")
    op.drop_table("skills")
    op.drop_table("projects")
    op.drop_table("experiences")
    op.drop_table("educations")
    op.drop_table("candidate_preferences")
    op.drop_table("candidate_profiles")
    op.drop_table("refresh_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("users")
