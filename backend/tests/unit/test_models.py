"""
Unit tests verifying all 28+ SQLAlchemy models and schema metadata integrity.
"""

from app.db.base import Base
import app.models as models


def test_all_models_registered_in_metadata():
    """Verify that all core tables are present in SQLAlchemy metadata."""
    expected_tables = {
        "users",
        "password_reset_tokens",
        "refresh_tokens",
        "candidate_profiles",
        "candidate_preferences",
        "educations",
        "experiences",
        "projects",
        "skills",
        "certifications",
        "achievements",
        "languages",
        "profile_links",
        "resumes",
        "documents",
        "companies",
        "contacts",
        "opportunities",
        "saved_opportunities",
        "applications",
        "application_stage_history",
        "application_notes",
        "application_followups",
        "application_documents",
        "qa_vault_entries",
        "application_answers",
        "application_activity",
        "interviews",
        "interview_preparations",
        "tasks",
        "notifications",
        "organizations",
        "job_postings",
        "job_posting_skills",
    }

    registered_tables = set(Base.metadata.tables.keys())
    missing_tables = expected_tables - registered_tables

    assert not missing_tables, f"Missing tables in Base.metadata: {missing_tables}"
    assert len(registered_tables) >= len(expected_tables)


def test_application_relationships():
    """Verify Application model foreign keys exist for cross-domain links."""
    app_table = Base.metadata.tables["applications"]
    fk_targets = {fk.target_fullname for fk in app_table.foreign_keys}

    # Verify links to User, Company, Opportunity, Contact, Resume, Document, JobPosting
    assert "users.id" in fk_targets
    assert "companies.id" in fk_targets
    assert "opportunities.id" in fk_targets
    assert "contacts.id" in fk_targets
    assert "resumes.id" in fk_targets
    assert "documents.id" in fk_targets
    assert "job_postings.id" in fk_targets


def test_task_polymorphic_relationships():
    """Verify Task model supports polymorphic entity linkages."""
    task_table = Base.metadata.tables["tasks"]
    fk_targets = {fk.target_fullname for fk in task_table.foreign_keys}

    assert "users.id" in fk_targets
    assert "applications.id" in fk_targets
    assert "interviews.id" in fk_targets
    assert "companies.id" in fk_targets
    assert "contacts.id" in fk_targets


def test_orm_mapper_relationships():
    """Verify SQLAlchemy ORM relationship attributes are fully configured on models."""
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

    # Application relationships
    assert hasattr(models.Application, "company")
    assert hasattr(models.Application, "opportunity")
    assert hasattr(models.Application, "contact")
    assert hasattr(models.Application, "resume")
    assert hasattr(models.Application, "cover_letter")
    assert hasattr(models.Application, "documents")
    assert hasattr(models.Application, "answers")
    assert hasattr(models.Application, "interviews")
    assert hasattr(models.Application, "tasks")
    assert hasattr(models.Application, "job_posting")

    # Recruiter & Organization relationships
    assert hasattr(models.User, "organization")
    assert hasattr(models.Organization, "owner")
    assert hasattr(models.Organization, "job_postings")
    assert hasattr(models.JobPosting, "organization")
    assert hasattr(models.JobPosting, "creator")
    assert hasattr(models.JobPosting, "skills")
    assert hasattr(models.JobPosting, "applications")

    # Company relationships
    assert hasattr(models.Company, "contacts")
    assert hasattr(models.Company, "applications")
    assert hasattr(models.Company, "interviews")
    assert hasattr(models.Company, "tasks")

    # Contact relationships
    assert hasattr(models.Contact, "company")
    assert hasattr(models.Contact, "applications")
    assert hasattr(models.Contact, "interviews")
    assert hasattr(models.Contact, "tasks")

    # Interview relationships
    assert hasattr(models.Interview, "preparation")
    assert hasattr(models.Interview, "application")
    assert hasattr(models.Interview, "company")
    assert hasattr(models.Interview, "contact")
    assert hasattr(models.Interview, "tasks")

    # Task relationships
    assert hasattr(models.Task, "application")
    assert hasattr(models.Task, "interview")
    assert hasattr(models.Task, "company")
    assert hasattr(models.Task, "contact")


def test_tenant_user_isolation_foreign_keys():
    """Verify all candidate-owned tables carry a user_id foreign key with CASCADE."""
    candidate_tables = [
        "candidate_profiles",
        "candidate_preferences",
        "educations",
        "experiences",
        "projects",
        "skills",
        "certifications",
        "achievements",
        "languages",
        "profile_links",
        "resumes",
        "documents",
        "companies",
        "contacts",
        "opportunities",
        "saved_opportunities",
        "applications",
        "qa_vault_entries",
        "interviews",
        "tasks",
        "notifications",
    ]

    for table_name in candidate_tables:
        table = Base.metadata.tables[table_name]
        user_fk = None
        for fk in table.foreign_keys:
            if fk.target_fullname == "users.id":
                user_fk = fk
                break
        assert user_fk is not None, f"Table '{table_name}' missing user_id FK"
        assert user_fk.ondelete == "CASCADE", f"Table '{table_name}' user_id FK should be ON DELETE CASCADE"
