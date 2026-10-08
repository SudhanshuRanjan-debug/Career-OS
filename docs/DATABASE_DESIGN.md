# Database Design & Schema Specification
## Career & Job Application Management Platform — PostgreSQL 16

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Design Principles

1. **Normalized Relational Model**: Every core entity is modeled in a dedicated table with typed columns, foreign keys, and indexes. No unstructured JSON blobs for structured domain data.
2. **User Data Isolation**: Every user-owned table carries a `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`. Every query is scoped to `user_id`.
3. **Historical Data Preservation**:
   - Resumes and documents use soft-deletes (`deleted_at`).
   - `applications.resume_id` locks the exact resume record used when applying.
   - `application_stage_history` is append-only.
   - `application_activity` is append-only.
4. **UTC Timestamps & UUID Primary Keys**: All primary keys are `UUID` (`gen_random_uuid()`). All timestamps are `TIMESTAMPTZ` in UTC.
5. **Private Storage Abstraction**: No binary file content is stored in PostgreSQL. The database stores file metadata and an immutable `storage_key`.
6. **Cross-Domain Relational Cohesion**: Clean foreign key linkages across `Company → Contact → Application → Interview → Task`.

---

## 2. Entity Relationship Overview

```
users (Authentication & Account)
  ├── refresh_tokens (1:N)
  ├── password_reset_tokens (1:N)
  ├── candidate_profiles (1:1)
  ├── candidate_preferences (1:1)
  ├── educations (1:N)
  ├── experiences (1:N)
  ├── projects (1:N)
  ├── skills (1:N)
  ├── certifications (1:N)
  ├── achievements (1:N)
  ├── languages (1:N)
  ├── profile_links (1:N)
  ├── resumes (1:N)
  ├── documents (1:N)
  ├── companies (1:N)
  │     └── contacts (1:N)
  ├── opportunities (1:N)
  │     └── saved_opportunities (N:M)
  ├── applications (1:N)
  │     ├── application_stage_history (1:N, append-only)
  │     ├── application_notes (1:N)
  │     ├── application_followups (1:N)
  │     ├── application_documents (N:M → documents)
  │     ├── application_answers (1:N → qa_vault_entries)
  │     └── application_activity (1:N, append-only)
  ├── qa_vault_entries (1:N)
  ├── interviews (1:N)
  │     └── interview_preparations (1:1)
  ├── tasks (1:N, polymorphic: application, interview, company, contact)
  └── notifications (1:N)
```

---

## 3. Schema Definitions

### 3.1 Authentication & User Management

```sql
-- 1. Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'CANDIDATE', -- 'CANDIDATE' or 'HIRER'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ
);

-- 2. Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Refresh Tokens
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_agent  TEXT,
    ip_address  VARCHAR(45)
);
```

### 3.2 Candidate Profile & Career Identity

```sql
-- 4. Candidate Profiles
CREATE TABLE candidate_profiles (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name           VARCHAR(100),
    last_name            VARCHAR(100),
    preferred_name       VARCHAR(100),
    phone                VARCHAR(30),
    location_city        VARCHAR(100),
    location_state       VARCHAR(100),
    location_country     VARCHAR(100),
    timezone             VARCHAR(60),
    headline             VARCHAR(255),
    professional_summary TEXT,
    career_objective     TEXT,
    current_role         VARCHAR(150),
    total_experience_yrs NUMERIC(4,1),
    notice_period_days   INTEGER,
    open_to_work         BOOLEAN DEFAULT TRUE,
    website              VARCHAR(500),
    profile_photo_key    VARCHAR(500),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Candidate Preferences
CREATE TABLE candidate_preferences (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    desired_job_titles      TEXT[],
    preferred_industries    TEXT[],
    preferred_locations     TEXT[],
    work_arrangement        VARCHAR(30), -- REMOTE, HYBRID, ON_SITE, ANY
    employment_type         TEXT[],      -- FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP
    min_compensation        NUMERIC(12,2),
    target_compensation     NUMERIC(12,2),
    compensation_currency   VARCHAR(10) DEFAULT 'USD',
    compensation_period     VARCHAR(20) DEFAULT 'ANNUAL',
    availability            VARCHAR(50),
    notice_period_days      INTEGER,
    work_authorization      TEXT[],
    relocation_preference   VARCHAR(30),
    preferred_company_sizes TEXT[],
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Educations
CREATE TABLE educations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution     VARCHAR(255) NOT NULL,
    degree          VARCHAR(100),
    field_of_study  VARCHAR(255),
    grade           VARCHAR(50),
    description     TEXT,
    start_date      DATE,
    end_date        DATE,
    is_current      BOOLEAN DEFAULT FALSE,
    location        VARCHAR(255),
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Experiences
CREATE TABLE experiences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name    VARCHAR(255) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    employment_type VARCHAR(50),
    location        VARCHAR(255),
    location_type   VARCHAR(20),
    description     TEXT,
    responsibilities TEXT,
    achievements    TEXT,
    start_date      DATE,
    end_date        DATE,
    is_current      BOOLEAN DEFAULT FALSE,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Projects
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    role            VARCHAR(150),
    tech_stack      TEXT[],
    url             VARCHAR(500),
    repo_url        VARCHAR(500),
    project_type    VARCHAR(50),
    achievements    TEXT,
    start_date      DATE,
    end_date        DATE,
    is_ongoing      BOOLEAN DEFAULT FALSE,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Skills
CREATE TABLE skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(100), -- TECHNICAL, SOFT, TOOL, CLOUD, DATABASE, FRAMEWORK
    proficiency     VARCHAR(30),  -- BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    years_of_exp    NUMERIC(4,1),
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. Certifications
CREATE TABLE certifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    issuing_org     VARCHAR(255),
    issue_date      DATE,
    expiry_date     DATE,
    credential_id   VARCHAR(255),
    credential_url  VARCHAR(500),
    description     TEXT,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Achievements
CREATE TABLE achievements (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    category    VARCHAR(50), -- AWARD, HACKATHON, COMPETITION, PUBLICATION, SCHOLARSHIP, LEADERSHIP
    date        DATE,
    issuer      VARCHAR(255),
    url         VARCHAR(500),
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. Languages
CREATE TABLE languages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    proficiency VARCHAR(30), -- NATIVE, FLUENT, PROFESSIONAL, INTERMEDIATE, BASIC
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. Profile Links
CREATE TABLE profile_links (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform    VARCHAR(50), -- LINKEDIN, GITHUB, PORTFOLIO, LEETCODE, KAGGLE, OTHER
    label       VARCHAR(100),
    url         VARCHAR(500) NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.3 Resumes & Private Document Vault

```sql
-- 14. Resumes
CREATE TABLE resumes (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    storage_key       VARCHAR(500) NOT NULL UNIQUE,
    file_size_bytes   BIGINT,
    mime_type         VARCHAR(100),
    version           INTEGER NOT NULL DEFAULT 1,
    is_default        BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);

-- 15. Documents
CREATE TABLE documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    doc_type          VARCHAR(30) NOT NULL, -- COVER_LETTER, CERTIFICATE, TRANSCRIPT, PORTFOLIO, RECOMMENDATION, OTHER
    original_filename VARCHAR(500) NOT NULL,
    storage_key       VARCHAR(500) NOT NULL UNIQUE,
    file_size_bytes   BIGINT,
    mime_type         VARCHAR(100),
    description       TEXT,
    version           INTEGER NOT NULL DEFAULT 1,
    uploaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
```

### 3.4 Companies, Contacts & Opportunities

```sql
-- 16. Companies
CREATE TABLE companies (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    website      VARCHAR(500),
    industry     VARCHAR(255),
    size         VARCHAR(50), -- STARTUP, SMALL, MEDIUM, LARGE, ENTERPRISE
    location     VARCHAR(255),
    description  TEXT,
    notes        TEXT,
    logo_url     VARCHAR(500),
    linkedin_url VARCHAR(500),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 17. Contacts
CREATE TABLE contacts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id   UUID REFERENCES companies(id) ON DELETE SET NULL,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100),
    role         VARCHAR(255),
    contact_type VARCHAR(30), -- RECRUITER, HIRING_MANAGER, INTERVIEWER, EMPLOYEE, REFERRAL, OTHER
    email        VARCHAR(255),
    phone        VARCHAR(30),
    linkedin_url VARCHAR(500),
    relationship VARCHAR(100),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 18. Opportunities
CREATE TABLE opportunities (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id            UUID REFERENCES companies(id) ON DELETE SET NULL,
    job_posting_id        UUID REFERENCES job_postings(id) ON DELETE SET NULL,
    title                 VARCHAR(255) NOT NULL,
    company_name          VARCHAR(255),
    source                VARCHAR(100), -- MANUAL, URL_IMPORT, REFERRAL, etc.
    source_url            VARCHAR(1000),
    location              VARCHAR(255),
    location_type         VARCHAR(20),  -- REMOTE, HYBRID, ON_SITE
    employment_type       VARCHAR(50),
    description           TEXT,
    requirements          TEXT,
    compensation_min      NUMERIC(12,2),
    compensation_max      NUMERIC(12,2),
    compensation_currency VARCHAR(10),
    posted_date           DATE,
    expiry_date           DATE,
    status                VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, SAVED, CONSIDERING, APPLIED, ARCHIVED, NOT_INTERESTED
    notes                 TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 19. Saved Opportunities
CREATE TABLE saved_opportunities (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    saved_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes          TEXT,
    UNIQUE(user_id, opportunity_id)
);
```

### 3.5 Applications & Activity Pipeline

```sql
-- 20. Applications
CREATE TABLE applications (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_posting_id        UUID REFERENCES job_postings(id) ON DELETE RESTRICT,
    company_id            UUID REFERENCES companies(id) ON DELETE SET NULL,
    opportunity_id        UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    contact_id            UUID REFERENCES contacts(id) ON DELETE SET NULL, -- primary recruiter/contact

    -- Snapshot of job information at application time
    job_title             VARCHAR(255) NOT NULL,
    company_name          VARCHAR(255) NOT NULL,
    job_location          VARCHAR(255),
    job_location_type     VARCHAR(20),
    employment_type       VARCHAR(50),
    job_description       TEXT,
    job_url               VARCHAR(1000),
    compensation_min      NUMERIC(12,2),
    compensation_max      NUMERIC(12,2),
    compensation_currency VARCHAR(10),

    -- Application state & stage tracking
    source                VARCHAR(100),
    status                VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, CLOSED, ARCHIVED
    current_stage         VARCHAR(50) NOT NULL DEFAULT 'APPLIED',
    applied_date          DATE,
    deadline_date         DATE,

    -- Immutable historical reference to resume and cover letter
    resume_id             UUID REFERENCES resumes(id) ON DELETE SET NULL,
    cover_letter_doc_id   UUID REFERENCES documents(id) ON DELETE SET NULL,

    priority              VARCHAR(20) DEFAULT 'MEDIUM',
    outcome               VARCHAR(50), -- ACCEPTED, REJECTED, WITHDRAWN, OFFER_DECLINED

    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 21. Application Stage History (Append-Only)
CREATE TABLE application_stage_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    from_stage      VARCHAR(50),
    to_stage        VARCHAR(50) NOT NULL,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT,
    changed_by_user UUID REFERENCES users(id) ON DELETE SET NULL
);

-- 22. Application Notes
CREATE TABLE application_notes (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content        TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 23. Application Follow-ups
CREATE TABLE application_followups (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    due_date       DATE,
    note           TEXT,
    is_completed   BOOLEAN DEFAULT FALSE,
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 24. Application Supporting Documents (N:M)
CREATE TABLE application_documents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    attached_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(application_id, document_id)
);

-- 25. Q&A Vault Entries (Reusable Answers)
CREATE TABLE qa_vault_entries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question    VARCHAR(500) NOT NULL,
    answer      TEXT NOT NULL,
    category    VARCHAR(100), -- GENERAL, BEHAVIORAL, TECHNICAL, SALARY, LOGISTICS
    is_template BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 26. Application Answers (Application-Specific Q&A)
CREATE TABLE application_answers (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id    UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    qa_vault_entry_id UUID REFERENCES qa_vault_entries(id) ON DELETE SET NULL,
    question          VARCHAR(500) NOT NULL,
    answer            TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 27. Application Activity Timeline (Append-Only)
CREATE TABLE application_activity (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type     VARCHAR(50) NOT NULL, -- APPLICATION_CREATED, STAGE_CHANGED, RESUME_ATTACHED, INTERVIEW_SCHEDULED, NOTE_ADDED, etc.
    event_data     JSONB,
    description    TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.6 Interviews & Interview Preparation

```sql
-- 28. Interviews
CREATE TABLE interviews (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application_id    UUID REFERENCES applications(id) ON DELETE SET NULL,
    company_id        UUID REFERENCES companies(id) ON DELETE SET NULL,
    contact_id        UUID REFERENCES contacts(id) ON DELETE SET NULL, -- primary interviewer contact
    title             VARCHAR(255),
    interview_type    VARCHAR(50), -- PHONE, VIDEO, ON_SITE, TECHNICAL, PANEL, HR, SYSTEM_DESIGN, BEHAVIORAL
    stage             VARCHAR(100),
    scheduled_at      TIMESTAMPTZ,
    duration_mins     INTEGER,
    meeting_link      VARCHAR(500),
    location          VARCHAR(255),
    status            VARCHAR(20) DEFAULT 'SCHEDULED', -- SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED
    result            VARCHAR(30), -- PASSED, FAILED, PENDING, CANCELLED
    interviewer_names TEXT[],
    notes             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 29. Interview Preparation
CREATE TABLE interview_preparations (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id          UUID NOT NULL UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    company_research      TEXT,
    role_research         TEXT,
    questions_to_ask      TEXT,
    personal_notes        TEXT,
    preparation_checklist JSONB, -- Array of { id: string, label: string, done: boolean }
    post_interview_notes  TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.7 Unified Tasks & In-App Notifications

```sql
-- 30. Tasks (Polymorphic Association)
CREATE TABLE tasks (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title          VARCHAR(255) NOT NULL,
    description    TEXT,
    due_date       DATE,
    priority       VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    status         VARCHAR(20) DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    is_completed   BOOLEAN DEFAULT FALSE,
    completed_at   TIMESTAMPTZ,

    -- Polymorphic entity linkages
    related_type   VARCHAR(30), -- APPLICATION, INTERVIEW, COMPANY, CONTACT, GENERAL
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    interview_id   UUID REFERENCES interviews(id) ON DELETE SET NULL,
    company_id     UUID REFERENCES companies(id) ON DELETE SET NULL,
    contact_id     UUID REFERENCES contacts(id) ON DELETE SET NULL,

    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 31. Notifications
CREATE TABLE notifications (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title             VARCHAR(255) NOT NULL,
    body              TEXT,
    notification_type VARCHAR(50), -- INTERVIEW_REMINDER, TASK_DUE, FOLLOW_UP_DUE, DEADLINE, SYSTEM
    is_read           BOOLEAN DEFAULT FALSE,
    read_at           TIMESTAMPTZ,
    related_type      VARCHAR(30),
    related_id        UUID,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.8 Employer Organizations & Job Postings

```sql
-- 32. Organizations (Employer Profiles)
CREATE TABLE organizations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    slug         VARCHAR(255) UNIQUE,
    website      VARCHAR(500),
    industry     VARCHAR(255),
    size         VARCHAR(50), -- STARTUP, SMALL, MEDIUM, LARGE, ENTERPRISE
    location     VARCHAR(255),
    description  TEXT,
    logo_url     VARCHAR(500),
    linkedin_url VARCHAR(500),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 33. Job Postings (Employer / Recruiter Job Listings)
CREATE TABLE job_postings (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by_user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title                 VARCHAR(255) NOT NULL,
    description           TEXT NOT NULL,
    requirements          TEXT,
    location              VARCHAR(255),
    location_type         VARCHAR(20) NOT NULL DEFAULT 'ON_SITE', -- REMOTE, HYBRID, ON_SITE
    employment_type       VARCHAR(50) NOT NULL DEFAULT 'FULL_TIME', -- FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP
    experience_level      VARCHAR(50), -- ENTRY, MID, SENIOR, LEAD, EXECUTIVE
    compensation_min      NUMERIC(12,2),
    compensation_max      NUMERIC(12,2),
    compensation_currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    status                VARCHAR(20) NOT NULL DEFAULT 'DRAFT', -- DRAFT, PUBLISHED, CLOSED, ARCHIVED
    deadline_date         DATE,
    published_at          TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 34. Job Posting Skills (Normalized Skills)
CREATE TABLE job_posting_skills (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    name           VARCHAR(100) NOT NULL,
    UNIQUE(job_posting_id, name)
);
```

---

## 4. Performance Indexes

```sql
-- Role and two-sided scoping indexes
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_organizations_owner ON organizations(owner_user_id);
CREATE INDEX idx_job_postings_org ON job_postings(organization_id);
CREATE INDEX idx_job_postings_creator ON job_postings(created_by_user_id);
CREATE INDEX idx_job_postings_status ON job_postings(status);
CREATE INDEX idx_jps_job ON job_posting_skills(job_posting_id);
CREATE INDEX idx_jps_name ON job_posting_skills(name);
CREATE INDEX idx_opportunities_job_posting ON opportunities(job_posting_id);
CREATE INDEX idx_applications_job_posting ON applications(job_posting_id);
-- Per-user tenant scoping indexes
CREATE INDEX idx_candidate_profiles_user ON candidate_profiles(user_id);
CREATE INDEX idx_educations_user ON educations(user_id);
CREATE INDEX idx_experiences_user ON experiences(user_id);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_skills_user ON skills(user_id);
CREATE INDEX idx_resumes_user ON resumes(user_id);
CREATE INDEX idx_resumes_default ON resumes(user_id, is_default) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_companies_user ON companies(user_id);
CREATE INDEX idx_contacts_user ON contacts(user_id);
CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_opportunities_user ON opportunities(user_id);
CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(user_id, status);
CREATE INDEX idx_applications_stage ON applications(user_id, current_stage);
CREATE INDEX idx_stage_history_app ON application_stage_history(application_id);
CREATE INDEX idx_activity_app ON application_activity(application_id);
CREATE INDEX idx_interviews_user ON interviews(user_id);
CREATE INDEX idx_interviews_scheduled ON interviews(user_id, scheduled_at);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_due ON tasks(user_id, due_date) WHERE is_completed = FALSE;
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read) WHERE is_read = FALSE;
```
