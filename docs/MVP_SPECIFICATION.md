# MVP & Staged Rollout Specification
## Career & Job Application Management Platform

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Architecture

---

## 1. Product Vision & MVP Philosophy

The Career & Job Application Management Platform is designed as a **personal Career Operating System**. It is intentionally NOT a barebones job application tracker.

To prevent architectural debt or premature rewrites, the **scaffold (Stage 1) establishes the full structural blueprint** across all 12 platform domains (database models, routing hierarchy, UI design system, storage abstraction, and API contracts). Feature capabilities are then systematically brought online across staged milestones.

```
Candidate Profile
       ↓
Career Information
       ↓
Resume / Documents
       ↓
Job Preferences
       ↓
Opportunity Discovery
       ↓
Opportunity → Application Conversion
       ↓
Application Pipeline & Health
       ↓
Recruiter / Company / Network
       ↓
Interview & Preparation
       ↓
Tasks / Follow-ups / Calendar
       ↓
Offer / Outcome
       ↓
Career Analytics
```

---

## 2. Staged Delivery Scope

### Stage 1: Scaffold & Infrastructure Foundation (Current Stage)
- Full normalized database schema (28+ tables) in PostgreSQL 16 via async SQLAlchemy 2 & Alembic.
- Storage abstraction layer (`LocalStorageProvider` and `AzureBlobStorageProvider`).
- FastAPI modular monolith structure with API routing stubs and health checks.
- React 18 + TypeScript + Vite + Tailwind CSS shell with the complete 12-hub navigation hierarchy and route stubs.
- Base UI design system components (Button, Input, Card, Badge, Modal, EmptyState, ProgressBar).
- Containerization setup (Docker, Docker Compose, Nginx) and GitHub Actions CI baseline.

### Core Foundation Rollout (Stages 2–5)
- **Stage 2: Authentication & Sessions**: JWT access tokens + secure HttpOnly refresh cookies, user registration, login, password reset, session management.
- **Stage 3: Candidate Profile & Document Vault**: Complete profile CRUD (personal, education, experience, projects, skills, certifications, achievements, languages, links), multi-version resume management, private document vault, job preferences, and deterministic Profile Completeness engine.
- **Stage 4: Opportunity Discovery & Conversion**: Opportunity creation, search, saved opportunities, and one-click conversion of opportunities into applications.
- **Stage 5: Applications & Health Engine**: Full recruitment pipeline (List & Kanban), immutable activity timeline, note-taking, follow-up tracking, Q&A vault integration, resume version locking, and deterministic Application Health calculation.

### Ecosystem & Network Rollout (Stages 6–9)
- **Stage 6: Companies & Professional Network**: Company directory with linked applications, contact management (recruiters, hiring managers, interviewers, referrals) linked to companies and applications.
- **Stage 7: Interviews & Preparation**: Multi-round interview tracking, interview prep checklists, company research, and post-interview debriefs.
- **Stage 8: Tasks, Calendar & Notifications**: Unified polymorphic tasks, aggregated calendar view (interviews, follow-ups, deadlines), and in-app notifications.
- **Stage 9: Dashboard & Career Analytics**: Career command center dashboard and real relational aggregations (application trends, funnel conversion, response rates, time metrics).

### Stage 9+: Two-Sided Platform Evolution (Current Stage)
- **Role Architecture**: Two first-class roles: `CANDIDATE` (job seeker) and `HIRER` (recruiter/employer), verified via authoritative database check (`users.role`).
- **Employer Organization**: Hirer organization profile setup and management.
- **Job Postings Management**: Lifecycle management for employer job postings (Draft, Published, Closed, Archived), normalized skills, compensation in INR (default) / extensible currency, and application deadline tracking.
- **Candidate Job Discovery**: Published jobs discoverable and directly applicable by candidates.
- **Applicant Pipeline & Review**: Recruiter applicant review with submitted resume streaming and stage progression.
- **Dual-Sided Application Ownership**: Candidates own submitted applications; recruiters access applications submitted to their postings with strict candidate privacy protection.

### Intelligence, Hardening & Production (Stages 10–16)
- **Stage 10: Explainable Matching**: Rule-based matching engine comparing profile skills/preferences with opportunities.
- **Stage 11: UI/UX Refinement**: Accessibility, responsive polish, micro-animations, keyboard navigation.
- **Stage 12–14: Testing & Security**: Integration testing, security hardening (rate limits, CSRF, CSP), vulnerability audit.
- **Stage 15–16: Cloud Deployment & Monitoring**: Azure Container Apps, Azure PostgreSQL, Azure Blob Storage, Azure Monitor.

---

## 3. Core Functional Requirements & User Stories

### 3.1 Candidate Profile
```
As a candidate, I can manage my personal information, contact info, and professional summary.
As a candidate, I can add, edit, reorder, and remove multiple education records.
As a candidate, I can add, edit, reorder, and remove multiple work experience records.
As a candidate, I can add, edit, and link projects with tech stacks and repository URLs.
As a candidate, I can manage technical and soft skills with proficiency levels.
As a candidate, I can record certifications with credential IDs, URLs, and optional expiry dates.
As a candidate, I can record awards, hackathons, publications, and leadership achievements.
As a candidate, I can track languages and proficiencies.
As a candidate, I can link external profiles (LinkedIn, GitHub, Portfolio, LeetCode, Kaggle).
As a candidate, I can define granular job preferences (roles, industries, locations, remote/hybrid, target compensation, notice period).
As a candidate, I can view an explainable Profile Completeness score with clear action items.
```

### 3.2 Resumes & Document Vault
```
As a candidate, I can upload multiple resume versions with custom labels (e.g., "Full Stack Resume v2").
As a candidate, I can designate a default resume for new applications.
As a candidate, I can download, preview, rename, and soft-delete resume versions.
As a candidate, when I submit an application, the exact resume version is immutably pinned.
As a candidate, I can privately store cover letters, transcripts, certificates, and portfolios.
As a candidate, my uploaded files are stored securely and never made publicly accessible.
```

### 3.3 Opportunities & Conversion
```
As a candidate, I can create opportunities manually or import clean URLs.
As a candidate, I can search, filter, and save opportunities for future consideration.
As a candidate, I can convert any opportunity into an application with a single click, snapshotting the job details.
```

### 3.4 Applications & Health
```
As a candidate, I can manage applications through standardized recruitment stages (Applied, Screen, Interview, Offer, etc.).
As a candidate, I can view applications in both a list table and a visual Kanban pipeline.
As a candidate, I can inspect an immutable activity timeline recording all major application events.
As a candidate, I can save and reuse common answers from my Q&A vault.
As a candidate, I can attach specific documents and add timestamped notes and follow-ups.
As a candidate, I can view an explainable Application Health score with actionable missing steps.
```

### 3.5 Companies, Contacts & Interviews
```
As a candidate, I can maintain a directory of target companies and view all associated applications, contacts, and interviews.
As a candidate, I can manage professional contacts (recruiters, managers, referrals) and associate them with companies and applications.
As a candidate, I can schedule interviews with meeting links, round types, and interviewers.
As a candidate, I can prepare for interviews with role research, question checklists, and post-interview debrief notes.
```

### 3.6 Tasks, Calendar, Notifications & Dashboard
```
As a candidate, I can manage tasks linked to applications, interviews, companies, or contacts.
As a candidate, I can view a unified calendar showing interviews, task due dates, and follow-up deadlines.
As a candidate, I can receive in-app alerts for pending tasks, upcoming interviews, and stale applications.
As a candidate, I can view a career command center dashboard with metrics, pipeline stats, and quick actions.
```

---

## 4. Deterministic Engines

### 4.1 Profile Completeness Engine
Calculated dynamically based on defined weights:
- Personal information (Name, Email, Location, Headline): **10%**
- Professional summary: **10%**
- At least one education record: **10%**
- At least one experience record: **15%**
- At least three skills: **10%**
- At least one resume uploaded: **15%**
- Job preferences configured: **10%**
- At least one project recorded: **10%**
- At least one social/profile link: **5%**
- At least one language recorded: **5%**
**Total: 100%**

Returns: `{ score: 85, completed: [...], missing: [...] }`

### 4.2 Application Health Engine
Deterministic audit per application:
- **Required**: Job title present, Company present, Resume attached, Current stage set, Application date set.
- **Health Penalties**: Stale application (active with no updates or follow-ups for > 14 days).
- **Suggestions (No Penalty)**: Primary recruiter/contact linked, follow-up scheduled, notes added.

Returns: `{ score: 80, status: "GOOD", checks: [...] }`

---

## 5. Success Criteria for Stage 1 Scaffold

- [x] Comprehensive architecture and specification documents fully updated and internally consistent.
- [x] Complete normalized PostgreSQL schema with all 28+ tables defined in SQLAlchemy 2 async models.
- [x] Alembic migration configuration and initial migration script generated and verifiable.
- [x] Storage service abstraction implemented with Local and Azure Blob providers.
- [x] FastAPI modular monolith skeleton with base dependencies, error handlers, config, and health checks.
- [x] Complete React 18 + Vite + TypeScript frontend with Tailwind CSS design system.
- [x] Full 12-hub navigation hierarchy and route stubs implemented.
- [x] Clean Docker Compose and CI workflows configured.
- [x] 100% verified via automated compilation, test execution, and schema inspection.
