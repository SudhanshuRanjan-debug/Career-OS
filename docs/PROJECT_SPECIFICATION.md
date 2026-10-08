# Career & Job Application Management Platform
## Project Specification — Career Operating System

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Product Vision

A comprehensive, privacy-first **Two-Sided Career & Recruiting Platform** that empowers candidates to manage their entire career lifecycle while providing employers and recruiters a unified hub to publish jobs, review applications, and coordinate hiring pipelines.

The product connects two primary user roles:
1. **Candidate / Job Seeker (`CANDIDATE`)**: Profile management, resume vault, opportunity discovery, application tracking, interview prep, and career analytics.
2. **Hirer / Recruiter (`HIRER`)**: Organization profile, job posting management, application review with submitted documents, pipeline stage progression, and hiring analytics.

```
       CANDIDATE                                     HIRER
   Candidate Profile                             Organization
          ↓                                           ↓
  Resumes / Documents                            Job Postings
          ↓                                           ↓
Opportunity Discovery ─────────► Published Jobs ◄─────┘
          ↓                           │
     Application ◄────────────────────┘
  (Dual Access: Candidate Owner + Recruiter Reviewer)
          ↓
  Stage Pipeline & History
          ↓
  Interviews & Scheduling
          ↓
    Offer & Outcome
```

---

## 2. Product Goals & Core Principles

1. **Unified Two-Sided Platform**: Empower candidates to track career progression and enable recruiters to manage hiring pipelines without fragmenting the system.
2. **Modular Monolith Architecture**: React + TypeScript frontend communicating strictly via a REST API with a FastAPI backend, SQLAlchemy 2 (async), and PostgreSQL 16. No direct database access from frontend; no premature microservices.
3. **Database-Backed Authoritative Role Authorization**: User roles (`CANDIDATE` and `HIRER`) are enforced from the database on every authenticated request.
4. **Historical Data Integrity**: Strict version pinning for resumes and documents. Job postings cannot be deleted if linked to submitted applications (`ON DELETE RESTRICT`).
5. **Candidate Privacy Boundary**: Recruiters only access data explicitly submitted with an application; candidates' private vaults, unattached documents, and preferences remain confidential.
6. **Zero External Paid Dependencies**: $0 development cost, purely open-source dependencies.

---

## 3. Target Users

- **Candidates / Job Seekers**:
  - Active & passive job seekers managing applications, resumes, interviews, and follow-ups.
- **Hirers / Recruiters / Employers**:
  - Talent acquisition teams, hiring managers, and founders posting openings, evaluating candidates, advancing pipeline stages, and scheduling interviews.

---

## 4. Product Scope (Master Domain Matrix)

| Domain | Description | Primary Entities | Navigation Placement |
|--------|-------------|------------------|----------------------|
| **Dashboard** | Career Command Center with KPIs, pipeline funnel, upcoming tasks, interview alerts, quick actions | Aggregations across all domains | `/dashboard` |
| **Candidate Profile** | Comprehensive candidate identity (personal, summary, education, experience, projects, skills, certifications, achievements, languages, links) | `candidate_profiles`, `educations`, `experiences`, `projects`, `skills`, `certifications`, `achievements`, `languages`, `profile_links` | `/profile/*` (Hub & Tabs) |
| **Resume Management** | Multi-version resume vault, label tagging, default selection, version preservation | `resumes` | `/profile/resumes` |
| **Document Vault** | Private storage for cover letters, transcripts, certificates, portfolios with secure storage abstraction | `documents` | `/profile/documents` |
| **Job Preferences** | Detailed career preferences (roles, industries, locations, remote/hybrid, compensation targets, notice period) | `candidate_preferences` | `/profile/preferences` |
| **Opportunity Discovery** | Discover, curate, filter, and save job opportunities. One-click conversion to Application | `opportunities`, `saved_opportunities` | `/opportunities/*` |
| **Applications** | Multi-stage pipeline tracking, activity timeline, Q&A vault integration, deterministic health check | `applications`, `application_stage_history`, `application_documents`, `application_notes`, `application_followups`, `application_activity` | `/applications/*` |
| **Application Q&A Vault** | Reusable bank of answers to behavioral and common application questions | `qa_vault_entries`, `application_answers` | `/applications` (Vault / Sub-tab) |
| **Companies** | Company directory with recruitment history, linked applications, contacts, and notes | `companies` | `/companies/*` |
| **Network & Contacts** | Recruiter, hiring manager, interviewer, and referral relationship directory | `contacts` | `/network/*` |
| **Interviews** | Multi-round interview tracking (phone, technical, panel, onsite, HR) | `interviews` | `/interviews/*` |
| **Interview Preparation** | Company research, role research, questions to ask, checklists, and post-interview debrief | `interview_preparations` | `/interviews/:id/prep` |
| **Tasks & Follow-ups** | Unified task management linked polymorphically to applications, interviews, companies, or contacts | `tasks` | `/tasks/*` |
| **Calendar** | Unified schedule aggregating interviews, task deadlines, follow-up dates, and application cutoffs | Cross-entity aggregation | `/calendar` |
| **Notifications** | In-app alert system for upcoming interviews, pending follow-ups, and stale applications | `notifications` | `/notifications` |
| **Analytics** | Real database-driven metrics on conversion funnels, response times, sources, and trends | Aggregated relational queries | `/analytics/*` |
| **Settings** | Account credentials, active sessions, notification preferences, privacy, data export, account deletion | `users`, `refresh_tokens` | `/settings/*` |
| **Organization (Hirer)** | Employer/company profile with branding, industry, and contact details | `organizations` | `/recruiter/organization` |
| **Job Postings (Hirer)** | Lifecycle management for job listings (draft, publish, close, archive) | `job_postings`, `job_posting_skills` | `/recruiter/jobs/*` |
| **Applicant Pipeline (Hirer)** | Applicant review, submitted resume downloads, and stage transitions | `applications`, `application_stage_history` | `/recruiter/jobs/:id/applicants`, `/recruiter/applications/:id` |
| **Hiring Analytics (Hirer)** | Metrics on active jobs, applicant conversion, time-to-hire, and offers | Aggregated relational queries | `/recruiter/analytics/*` |

---

## 5. Role-Based Navigation Architecture

The application provides distinct, role-tailored navigation shells enforced by backend authorization:

### Candidate Navigation
```
Dashboard                 → /dashboard
Jobs (Discover)           → /jobs
Opportunities (Saved)     → /opportunities
Applications              → /applications
 ├── Pipeline (Kanban)    → /applications/pipeline
 └── Follow-ups           → /applications/followups
Interviews                → /interviews
Tasks                     → /tasks
Calendar                  → /calendar
Profile & Vault           → /profile/* (Personal, Experience, Skills, Resumes, Documents)
Companies                 → /companies (Personal target list)
Network                   → /network (Personal contacts)
Analytics                 → /analytics
Notifications             → /notifications
Settings                  → /settings
```

### Hirer / Recruiter Navigation
```
Dashboard                 → /recruiter/dashboard (or role-routed /dashboard)
Job Postings              → /recruiter/jobs
 ├── Active Postings      → /recruiter/jobs
 ├── Create Job           → /recruiter/jobs/new
 └── Job Details          → /recruiter/jobs/:id
Applicants                → /recruiter/applicants
Interviews                → /recruiter/interviews
Tasks                     → /tasks
Calendar                  → /calendar
Organization              → /recruiter/organization
Hiring Analytics          → /recruiter/analytics
Notifications             → /notifications
Settings                  → /settings
```

---

## 6. Profile vs. Settings Architectural Boundary

- **PROFILE (`/profile/*`)**: Defines the candidate's professional career identity. Contains personal info, work history, education, skills, resume variants, private certificates, and job search criteria.
- **SETTINGS (`/settings/*`)**: Defines application configuration, security controls, notification switches, theme preferences, session management, and GDPR-compliant data export/deletion.

---

## 7. Development Roadmap (Stages 0–16)

| Stage | Name | Key Deliverables |
|:-----:|:-----|:-----------------|
| **0** | **Product & Domain Architecture** | Complete specifications, database design, API design, user flows, navigation map |
| **1** | **Project Scaffold & Infrastructure** | Full 28+ SQLAlchemy models, Alembic async migration, FastAPI skeleton, React shell with 12-domain routing, Tailwind design system, health check, testing/CI baseline |
| **2** | **Authentication & Accounts** | JWT auth (short-lived access + secure HttpOnly refresh cookie), password hashing (bcrypt), password reset, session revocation |
| **3** | **Candidate Profile & Document Vault** | Profile subsections CRUD, multi-version resume management, storage abstraction (Local/Azure), job preferences, deterministic completeness engine |
| **4** | **Opportunity Discovery & Conversion** | Opportunity repository, filtering/search, saved opportunities, one-click conversion to application |
| **5** | **Applications & Health Engine** | Multi-stage pipeline (list + Kanban), resume version lock, notes, followups, documents, Q&A vault, immutable activity timeline, deterministic health check |
| **6** | **Companies & Network Directory** | Company CRUD with recruitment history, Contact management (recruiters/referrals) linked to companies, applications, and interviews |
| **7** | **Interviews & Preparation** | Interview scheduling, round types, outcome logging, structured prep checklists, research notes, and debrief |
| **8** | **Tasks, Calendar & Notifications** | Unified task management linked to entities, aggregated multi-event calendar, in-app notification engine |
| **9** | **Dashboard & Career Analytics** | Career command center, real relational aggregations (trends, funnel conversion, response rates, time metrics) |
| **10** | **Explainable Matching Engine** | Deterministic rule-based scoring matching candidate profile against opportunities (skills, role, location, comp) |
| **11** | **UI/UX Refinement & Polish** | Responsive design, accessibility (WCAG AA), micro-animations, loading/empty states, keyboard shortcuts |
| **12** | **Full Functional Testing** | Backend integration test suite, frontend component/integration tests, end-to-end workflow verification |
| **13** | **Security Hardening** | Rate limiting, CORS tightening, CSRF protection, input sanitization, security headers, dependency scanning |
| **14** | **Security Testing** | Vulnerability assessment, penetration testing, auth boundary verification, OWASP Top 10 validation |
| **15** | **Production Cloud Deployment** | Azure Container Apps / App Service, Azure Database for PostgreSQL, Azure Blob Storage, Azure Front Door |
| **16** | **Monitoring & Maintenance** | Azure Monitor, Application Insights, structured JSON logging, health alerts, database maintenance |

---

## 8. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, React Router v6, TanStack React Query, Zustand, Axios, Lucide Icons.
- **Backend API**: Python 3.12/3.13, FastAPI (modular monolith), Pydantic v2.
- **Database**: PostgreSQL 16, SQLAlchemy 2 (asyncpg), Alembic migrations.
- **Storage Layer**: Custom `StorageService` abstraction (`LocalStorageProvider` for dev, `AzureBlobStorageProvider` for staging/prod).
- **Containerization**: Docker, Docker Compose, Nginx reverse proxy.
- **CI/CD**: GitHub Actions.
- **Cloud Infrastructure**: Microsoft Azure (Container Apps, Flexible PostgreSQL Server, Blob Storage, Key Vault).
