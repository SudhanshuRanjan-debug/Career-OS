"""002_two_sided_platform

Revision ID: 002_two_sided_platform
Revises: 001_initial_schema
Create Date: 2026-10-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_two_sided_platform"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add role column to users
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="CANDIDATE"),
    )
    op.create_index("idx_users_role", "users", ["role"])

    # 2. organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_organizations_owner_user_id", "organizations", ["owner_user_id"])
    op.create_index("idx_organizations_slug", "organizations", ["slug"])

    # 3. job_postings
    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("location_type", sa.String(20), nullable=False, server_default="ON_SITE"),
        sa.Column("employment_type", sa.String(50), nullable=False, server_default="FULL_TIME"),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("compensation_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_job_postings_org_id", "job_postings", ["organization_id"])
    op.create_index("idx_job_postings_creator_id", "job_postings", ["created_by_user_id"])
    op.create_index("idx_job_postings_status", "job_postings", ["status"])

    # 4. job_posting_skills
    op.create_table(
        "job_posting_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_posting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("job_posting_id", "name", name="uq_jps_job_skill"),
    )
    op.create_index("idx_job_posting_skills_job_id", "job_posting_skills", ["job_posting_id"])
    op.create_index("idx_job_posting_skills_name", "job_posting_skills", ["name"])

    # 5. Add job_posting_id to opportunities
    op.add_column(
        "opportunities",
        sa.Column(
            "job_posting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_opportunities_job_posting_id", "opportunities", ["job_posting_id"])

    # 6. Add job_posting_id to applications (RESTRICT delete on job postings that have applications)
    op.add_column(
        "applications",
        sa.Column(
            "job_posting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("idx_applications_job_posting_id", "applications", ["job_posting_id"])


def downgrade() -> None:
    op.drop_index("idx_applications_job_posting_id", table_name="applications")
    op.drop_column("applications", "job_posting_id")

    op.drop_index("idx_opportunities_job_posting_id", table_name="opportunities")
    op.drop_column("opportunities", "job_posting_id")

    op.drop_table("job_posting_skills")
    op.drop_table("job_postings")
    op.drop_table("organizations")

    op.drop_index("idx_users_role", table_name="users")
    op.drop_column("users", "role")
