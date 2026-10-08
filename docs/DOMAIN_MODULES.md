# Domain Modules & Responsibility Matrix
## Career & Job Application Management Platform — Career Operating System

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Architectural Philosophy

Every module in the platform is a cohesive bounded domain within a **Modular Monolith**. Each domain has a well-defined purpose, explicit relational touchpoints with other domains, dedicated database entities, clear frontend page routes, and a designated backend namespace.

---

## 2. Comprehensive Domain Matrix

### 2.1 Dashboard Module
- **Purpose**: Unified career command center displaying high-level metrics, active pipelines, today's priorities, and fast action triggers.
- **Relationships**: Aggregates state across Applications, Interviews, Tasks, Opportunities, and Profile Completeness.
- **Database Entities**: Cross-table queries across `applications`, `interviews`, `tasks`, `opportunities`, and `candidate_profiles`.
- **Frontend Pages**: `/dashboard` (Executive Summary, Pipeline Funnel Widget, Upcoming Events, Quick Action Modals).
- **Backend Responsibility**: `api/v1/endpoints/dashboard.py`, `services/dashboard_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Customizable user widgets, activity heatmaps, morning briefing summary.

---

### 2.2 Candidate Profile & Career Identity Module
- **Purpose**: Comprehensive professional identity repository containing all information needed during job applications.
- **Relationships**:
  - Serves as the master profile data source.
  - Generates the Profile Completeness score.
  - Feeds candidate data into future matching engines.
- **Database Entities**:
  - `candidate_profiles` (1:1 with `users`)
  - `candidate_preferences` (1:1 with `users`)
  - `educations`, `experiences`, `projects`, `skills`, `certifications`, `achievements`, `languages`, `profile_links` (1:N with `users`)
- **Frontend Pages**:
  - `/profile` (Overview & completeness)
  - `/profile/personal`, `/profile/professional`, `/profile/education`, `/profile/experience`, `/profile/projects`
  - `/profile/skills`, `/profile/certifications`, `/profile/achievements`, `/profile/languages`, `/profile/links`, `/profile/preferences`
- **Backend Responsibility**: `api/v1/endpoints/profile.py`, `education.py`, `experience.py`, etc.; `services/profile_service.py`, `services/completeness_service.py`.
- **Navigation Placement**: Primary top-level navigation hub with internal tabbed routing.
- **Future Extensibility**: Profile export to JSON Resume standard, external profile syncing.

---

### 2.3 Resumes Module
- **Purpose**: Version-controlled resume repository allowing candidates to manage multiple tailored resumes and track which version was submitted to each application.
- **Relationships**:
  - Applications hold an immutable foreign key (`resume_id`) pointing to the specific resume row used.
  - Linked to `StorageService` for secure binary storage.
- **Database Entities**: `resumes` (with `storage_key`, `version`, `is_default`, `deleted_at`).
- **Frontend Pages**: `/profile/resumes` (Resume management hub with upload modal, preview, set-default toggle).
- **Backend Responsibility**: `api/v1/endpoints/resumes.py`, `services/resume_service.py`.
- **Navigation Placement**: Sub-hub under Profile with direct quick-action links from dashboard.
- **Future Extensibility**: Keyword highlight analysis, ATS compatibility scoring, automated PDF generation.

---

### 2.4 Document Vault Module
- **Purpose**: Secure private storage for non-resume career documents (cover letters, transcripts, diplomas, certificates, portfolios, recommendation letters).
- **Relationships**:
  - Documents can be attached to Applications via `application_documents` (N:M).
  - Uses `StorageService` for secure, non-public storage.
- **Database Entities**: `documents`, `application_documents`.
- **Frontend Pages**: `/profile/documents` (Vault grid/table, upload modal, filter by `doc_type`).
- **Backend Responsibility**: `api/v1/endpoints/documents.py`, `services/document_service.py`.
- **Navigation Placement**: Sub-hub under Profile.
- **Future Extensibility**: Document full-text indexing, cover letter template generation.

---

### 2.5 Job Preferences Module
- **Purpose**: Candidate's explicit target parameters for roles, compensation, locations, work modes, and company types.
- **Relationships**: Used by the future matching engine to evaluate Opportunity compatibility.
- **Database Entities**: `candidate_preferences`.
- **Frontend Pages**: `/profile/preferences` (Granular preference editing form).
- **Backend Responsibility**: `api/v1/endpoints/preferences.py`, `services/profile_service.py`.
- **Navigation Placement**: Sub-hub under Profile.
- **Future Extensibility**: Target employer wishlist, automated salary benchmark lookups.

---

### 2.6 Opportunity Discovery Module
- **Purpose**: Discover, capture, and curate job opportunities before formally applying; includes one-click conversion to applications.
- **Relationships**:
  - Can be associated with a `Company`.
  - Converts directly into an `Application`, freezing job data into the application record.
- **Database Entities**: `opportunities`, `saved_opportunities`.
- **Frontend Pages**:
  - `/opportunities` (Discovery grid & search)
  - `/opportunities/saved` (Bookmarked queue)
  - `/opportunities/:id` (Opportunity detail & conversion modal)
- **Backend Responsibility**: `api/v1/endpoints/opportunities.py`, `services/opportunity_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Browser extension import tool, verified employer job feeds.

---

### 2.7 Applications Module
- **Purpose**: The core workflow engine managing active and past job applications through standardized recruitment stages with audit history.
- **Relationships**:
  - Links to `Company`, `Opportunity`, primary `Contact` (Recruiter), `Resume` version, and `Document` (Cover letter).
  - Parent to `application_stage_history`, `application_notes`, `application_followups`, `application_answers`, and `application_activity`.
  - Has associated `Interviews` and `Tasks`.
- **Database Entities**: `applications`, `application_stage_history`, `application_notes`, `application_followups`, `application_activity`.
- **Frontend Pages**:
  - `/applications` (Filterable list table)
  - `/applications/pipeline` (Visual Kanban board)
  - `/applications/followups` (Dedicated follow-ups tracking)
  - `/applications/:id` (Application details, tabs for timeline, notes, followups, documents, Q&A, health)
- **Backend Responsibility**: `api/v1/endpoints/applications.py`, `app_notes.py`, `app_followups.py`, `app_activity.py`; `services/application_service.py`, `services/health_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Custom recruitment stage workflows, automated follow-up scheduling.

---

### 2.8 Application Q&A Vault Module
- **Purpose**: Centralized bank of reusable answers to common application and behavioral questions that can be linked to specific applications.
- **Relationships**: Application answers copy or reference entries from the master vault.
- **Database Entities**: `qa_vault_entries`, `application_answers`.
- **Frontend Pages**: Managed within `/applications` and Application Details tabs.
- **Backend Responsibility**: `api/v1/endpoints/qa_vault.py`, `app_answers.py`.
- **Navigation Placement**: Integrated inside Applications module.
- **Future Extensibility**: AI-suggested answer tailoring based on job description.

---

### 2.9 Companies Module
- **Purpose**: Central directory of employers that candidate is actively targeting, applying to, or researching.
- **Relationships**:
  - 1:N with `Contacts` (Recruiters, Hiring Managers).
  - 1:N with `Applications`.
  - 1:N with `Interviews`.
- **Database Entities**: `companies`.
- **Frontend Pages**:
  - `/companies` (Company list with search and industry filters)
  - `/companies/:id` (Company details, past applications, linked contacts, research notes)
- **Backend Responsibility**: `api/v1/endpoints/companies.py`, `services/company_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Glassdoor/levels.fyi company insights, interview trends per company.

---

### 2.10 Network & Contacts Module
- **Purpose**: Relationship management directory for recruiters, hiring managers, interviewers, and referrals.
- **Relationships**:
  - Linked to `Companies`.
  - Linked as primary recruiter on `Applications`.
  - Linked as interviewer on `Interviews`.
  - Can have associated `Tasks`.
- **Database Entities**: `contacts`.
- **Frontend Pages**:
  - `/network` (Contact directory with type filters)
  - `/network/:id` (Contact details, linked interactions)
- **Backend Responsibility**: `api/v1/endpoints/contacts.py`, `services/contact_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Interaction reminders, email communication log.

---

### 2.11 Interviews & Preparation Module
- **Purpose**: Multi-stage interview scheduling, outcome tracking, and structured preparation workspace.
- **Relationships**:
  - Child of `Application`.
  - Associated with `Company` and primary `Contact`.
  - 1:1 with `interview_preparations`.
  - Events sync with `Calendar` and `Notifications`.
- **Database Entities**: `interviews`, `interview_preparations`.
- **Frontend Pages**:
  - `/interviews` (Tabs: Upcoming, Completed, Cancelled)
  - `/interviews/:id` (Interview details, meeting links, debrief)
  - `/interviews/:id/prep` (Preparation checklist, research, question prep)
- **Backend Responsibility**: `api/v1/endpoints/interviews.py`, `interview_prep.py`; `services/interview_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Audio/transcription notes, question rehearsal timer.

---

### 2.12 Tasks & Calendar Module
- **Purpose**: Unified task management and comprehensive cross-domain schedule for all career events.
- **Relationships**:
  - Polymorphic foreign keys linking tasks to Application, Interview, Company, or Contact.
  - Calendar aggregates interviews, tasks, application deadlines, and follow-up reminders.
- **Database Entities**: `tasks`.
- **Frontend Pages**:
  - `/tasks` (Filter: Today, Upcoming, Completed)
  - `/calendar` (Monthly and Weekly schedule view)
- **Backend Responsibility**: `api/v1/endpoints/tasks.py`, `calendar.py`; `services/task_service.py`, `calendar_service.py`.
- **Navigation Placement**: Primary top-level navigation items (`Tasks`, `Calendar`).
- **Future Extensibility**: iCal / Google Calendar export (.ics feed).

---

### 2.13 Notifications Module
- **Purpose**: In-app alert system reminding users of approaching interviews, pending follow-ups, and stale applications.
- **Relationships**: Generated by system events or time triggers across Interviews, Tasks, and Applications.
- **Database Entities**: `notifications`.
- **Frontend Pages**: `/notifications` (Notification list, mark read controls) + TopBar bell dropdown.
- **Backend Responsibility**: `api/v1/endpoints/notifications.py`, `services/notification_service.py`.
- **Navigation Placement**: Primary top-level navigation item + TopBar badge.
- **Future Extensibility**: Web push notifications, email digest.

---

### 2.14 Career Analytics Module
- **Purpose**: Comprehensive, real-time analytics driven exclusively by actual database records (no mock or random metrics).
- **Relationships**: Queries aggregations across `applications`, `application_stage_history`, `interviews`, `resumes`, and `companies`.
- **Database Entities**: Relational queries on all core transactional tables.
- **Frontend Pages**:
  - `/analytics` (Overview dashboard)
  - `/analytics/trends` (Application submission velocity)
  - `/analytics/pipeline` (Funnel stage conversion rates)
  - `/analytics/companies` (Response rates by employer)
  - `/analytics/outcomes` (Offer vs rejection distribution)
  - `/analytics/time` (Velocity metrics: time-to-first-response, time-to-offer)
- **Backend Responsibility**: `api/v1/endpoints/analytics.py`, `services/analytics_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: PySpark analytical export, compensation negotiation benchmarks.

---

### 2.15 Settings Module
- **Purpose**: Strict platform/account configuration (completely separate from Candidate Profile).
- **Relationships**: Governs `users` security, active `refresh_tokens`, notification rules, and GDPR compliance.
- **Database Entities**: `users`, `refresh_tokens`.
- **Frontend Pages**:
  - `/settings` (Settings hub)
  - `/settings/account`, `/settings/security`, `/settings/notifications`
  - `/settings/privacy`, `/settings/sessions`, `/settings/data`, `/settings/appearance`, `/settings/danger`
- **Backend Responsibility**: `api/v1/endpoints/settings.py`, `services/auth_service.py`.
- **Navigation Placement**: Primary top-level navigation item.
- **Future Extensibility**: Two-Factor Authentication (TOTP), passkey support.
