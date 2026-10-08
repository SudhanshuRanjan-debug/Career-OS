"""003_application_unique_platform_job

Revision ID: 003_app_platform_job_uq
Revises: 002_two_sided_platform
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_app_platform_job_uq"
down_revision: Union[str, None] = "002_two_sided_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_applications_user_job_posting",
        "applications",
        ["user_id", "job_posting_id"],
        unique=True,
        postgresql_where=sa.text("job_posting_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_applications_user_job_posting", table_name="applications")
