# System Architecture Design
## Career & Job Application Management Platform — Career Operating System

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. High-Level Architecture

The platform is designed as a high-cohesion, low-coupling **Modular Monolith** to deliver enterprise-grade performance and maintainability without premature microservice complexity.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                                                                         │
│   Browser (Desktop / Tablet / Mobile)                                   │
│   └── React 18 + TypeScript + Vite + Tailwind CSS                       │
│       ├── React Router v6 (12-Domain Route Tree)                        │
│       ├── TanStack Query (Server State & Caching)                       │
│       ├── Zustand (Client Auth & UI State)                              │
│       └── Axios (HTTP Interceptors, Token Refresh)                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │  HTTPS / REST JSON
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY / REVERSE PROXY                      │
│                                                                         │
│   Nginx (Reverse Proxy, TLS Termination, Security Headers, SPA fallback)│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION BACKEND LAYER                        │
│                                                                         │
│   FastAPI (Python 3.12 / 3.13)                                          │
│   ├── Security & JWT Engine (Access Token + HttpOnly Refresh Cookie)    │
│   ├── Authoritative Role Verification (users.role in PostgreSQL)       │
│   ├── Core Middleware (CORS, Request Logging, Exception Handlers)       │
│   ├── Domain Routers (/api/v1/*):                                       │
│   │   ├── auth / users        ├── applications    ├── tasks             │
│   │   ├── profile / skills    ├── companies       ├── calendar          │
│   │   ├── resumes / documents ├── contacts        ├── notifications     │
│   │   ├── opportunities       ├── interviews      ├── analytics         │
│   │   ├── jobs (published)    ├── organizations   ├── recruiter/jobs    │
│   │   └── preferences         ├── qa_vault        └── settings          │
│   ├── Business Service Layer (Rule Engines, Completeness, Health)       │
│   ├── Repository Layer (SQLAlchemy 2 Async Sessions)                    │
│   └── Storage Abstraction Layer (StorageService Interface)              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────┐
│           DATA PERSISTENCE            │ │       FILE STORAGE LAYER      │
│                                       │ │                               │
│  PostgreSQL 16                        │ │  Dev: Local Storage Provider  │
│  - 34+ Normalized Relational Tables   │ │       (/storage/private/...)  │
│  - Strict Foreign Keys & Indexes      │ │  Prod: Azure Blob Storage     │
│  - Immutable Activity & Stage Logs    │ │       (Private SAS access)    │
│  - Dual-Sided Tenant Isolation Model  │ │                               │
└───────────────────────────────────────┘ └───────────────────────────────┘
```

---

## 2. Backend Modular Monolith Structure

```
backend/app/
├── api/
│   └── v1/
│       ├── router.py                # Main API v1 router combining all domains
│       └── endpoints/
│           ├── auth.py              # Register, login, refresh, logout, password reset
│           ├── profile.py           # Profile overview, personal & professional info
│           ├── education.py         # Education records CRUD
│           ├── experience.py        # Work experience records CRUD
│           ├── projects.py          # Project portfolio records CRUD
│           ├── skills.py            # Technical & soft skills CRUD
│           ├── certifications.py    # Certification records CRUD
│           ├── achievements.py      # Awards, publications, achievements CRUD
│           ├── languages.py         # Language proficiency CRUD
│           ├── links.py             # Professional links (LinkedIn, GitHub, etc.) CRUD
│           ├── preferences.py       # Candidate job preferences CRUD
│           ├── resumes.py           # Resume management, versioning, download
│           ├── documents.py         # Document vault CRUD, upload, stream download
│           ├── opportunities.py     # Opportunity discovery, search, save, convert
│           ├── applications.py      # Application CRUD, pipeline stages, health
│           ├── app_notes.py         # Application notes CRUD
│           ├── app_followups.py     # Application follow-up reminders CRUD
│           ├── app_documents.py     # Application document associations
│           ├── app_answers.py       # Application Q&A custom answers
│           ├── app_activity.py      # Application immutable activity timeline
│           ├── qa_vault.py          # Reusable Q&A answer vault CRUD
│           ├── companies.py         # Company directory CRUD & history
│           ├── contacts.py          # Contact/network directory CRUD
│           ├── interviews.py        # Interview tracking & outcomes CRUD
│           ├── interview_prep.py    # Interview preparation checklist & research
│           ├── tasks.py             # Polymorphic tasks & follow-ups CRUD
│           ├── calendar.py          # Aggregated calendar schedule endpoint
│           ├── notifications.py     # In-app notification alerts CRUD
│           ├── analytics.py         # Database-driven analytics endpoints
│           ├── dashboard.py         # Dashboard aggregation endpoint
│           └── settings.py          # User account, session, and security settings
│
├── core/
│   ├── config.py                    # Environment settings via pydantic-settings
│   ├── security.py                  # Password hashing (bcrypt) & JWT issuance/validation
│   ├── dependencies.py              # Database session & get_current_user dependencies
│   ├── exceptions.py                # Standardized AppError exceptions and handlers
│   └── logging.py                   # Structured JSON logging configuration
│
├── db/
│   ├── base.py                      # DeclarativeBase with common timestamp mixins
│   ├── session.py                   # Async session factory using asyncpg
│   └── init_db.py                   # DB connection verification & table initialization
│
├── models/                          # 28+ Normalized SQLAlchemy 2 ORM models
│   ├── user.py                      # User, PasswordResetToken, RefreshToken
│   ├── candidate_profile.py         # CandidateProfile, CandidatePreferences
│   ├── profile_items.py             # Education, Experience, Project, Skill, etc.
│   ├── resume.py                    # Resume (with strict versioning)
│   ├── document.py                  # Document (DocumentType enum)
│   ├── company.py                   # Company
│   ├── contact.py                   # Contact (Recruiter, Interviewer, Referral, etc.)
│   ├── opportunity.py               # Opportunity, SavedOpportunity
│   ├── application.py               # Application, StageHistory, Note, Followup, etc.
│   ├── qa_vault.py                  # QAVaultEntry, ApplicationAnswer
│   ├── interview.py                 # Interview, InterviewPreparation
│   ├── task.py                      # Task (polymorphic relation)
│   └── notification.py              # Notification
│
├── schemas/                         # Pydantic v2 validation models
│   ├── common.py                    # Pagination, Sorting, Standard Responses
│   ├── auth.py                      # Auth DTOs
│   ├── profile.py                   # Profile DTOs
│   ├── resume.py                    # Resume DTOs
│   ├── document.py                  # Document DTOs
│   ├── opportunity.py               # Opportunity DTOs
│   ├── application.py               # Application DTOs
│   ├── company.py                   # Company DTOs
│   ├── contact.py                   # Contact DTOs
│   ├── interview.py                 # Interview DTOs
│   ├── task.py                      # Task DTOs
│   ├── notification.py              # Notification DTOs
│   ├── analytics.py                 # Analytics DTOs
│   └── dashboard.py                 # Dashboard DTOs
│
├── services/                        # Domain logic and rule engines
│   ├── auth_service.py              # Auth & session logic
│   ├── profile_service.py           # Profile management
│   ├── completeness_service.py      # Deterministic Profile Completeness Engine
│   ├── resume_service.py            # Resume upload & version pinning
│   ├── document_service.py          # Document vault logic
│   ├── opportunity_service.py       # Opportunity discovery & conversion
│   ├── application_service.py       # Application pipeline & stage management
│   ├── health_service.py            # Deterministic Application Health Engine
│   ├── activity_service.py          # Activity logger
│   ├── company_service.py           # Company directory
│   ├── contact_service.py           # Contact directory
│   ├── interview_service.py         # Interview scheduling & prep
│   ├── task_service.py              # Polymorphic task management
│   ├── calendar_service.py          # Schedule aggregator
│   ├── notification_service.py      # In-app notifications
│   ├── analytics_service.py         # Real relational query aggregations
│   └── dashboard_service.py         # Command center aggregator
│
├── storage/                         # Clean Storage Abstraction
│   ├── base.py                      # Abstract StorageService class
│   ├── local_storage.py             # Local filesystem provider (Development)
│   └── azure_storage.py             # Azure Blob Storage provider (Production)
│
├── utils/                           # Shared utility helpers
│   ├── pagination.py                # Page calculation
│   ├── date_utils.py                # UTC time formatters
│   └── validators.py                # File MIME / size validators
│
└── main.py                          # Application lifespan, CORS, and root health routes
```

---

## 3. Frontend Architecture (Feature-Folder Pattern)

```
frontend/src/
├── app/
│   ├── router.tsx                   # React Router v6 complete 12-domain routing
│   └── providers.tsx                # Context providers (QueryClient, Auth, Theme)
│
├── components/                      # Reusable Design System Components
│   ├── ui/
│   │   ├── Button.tsx               # Primary, Secondary, Outline, Danger variants
│   │   ├── Input.tsx                # Form inputs with validation states
│   │   ├── Card.tsx                 # Container cards with elevation
│   │   ├── Badge.tsx                # Status badges with color mappings
│   │   ├── Modal.tsx                # Accessible dialog modals
│   │   ├── EmptyState.tsx           # Rich empty states with call-to-action
│   │   ├── ProgressBar.tsx          # Deterministic completeness & health bars
│   │   └── Dropdown.tsx             # Action menus
│   └── layout/
│       ├── AppShell.tsx             # Main authenticated shell (Sidebar + TopBar + Main)
│       ├── Sidebar.tsx              # 12-hub hierarchical navigation
│       ├── TopBar.tsx               # Search, notifications bell, user profile menu
│       ├── PageHeader.tsx           # Standardized page title, breadcrumbs, actions
│       └── PublicLayout.tsx         # Layout for public auth pages
│
├── features/                        # 12 Major Domain Feature Modules
│   ├── auth/                        # SignIn, SignUp, ForgotPassword, ResetPassword
│   ├── dashboard/                   # Dashboard command center page & widgets
│   ├── profile/                     # Profile hub and all 13 sub-tab pages
│   ├── opportunities/               # Discovery, Saved, Details, Convert modal
│   ├── applications/                # List view, Kanban pipeline, Details, Health
│   ├── companies/                   # Companies list and Company detail pages
│   ├── interviews/                  # Upcoming/Past tabs, Details, Prep checklist
│   ├── tasks/                       # Tasks list, Today/Upcoming tabs, Add modal
│   ├── calendar/                    # Unified multi-event calendar page
│   ├── network/                     # Contacts list and Contact detail pages
│   ├── analytics/                   # Analytics overview, trends, funnels, time
│   ├── notifications/               # In-app notifications list and controls
│   └── settings/                    # Account, Security, Sessions, Privacy, Data
│
├── lib/
│   ├── axios.ts                     # Axios client with JWT injection & refresh flow
│   └── queryClient.ts               # React Query default configuration
│
├── store/
│   ├── authStore.ts                 # Zustand client auth state (token, user info)
│   └── uiStore.ts                   # Zustand UI state (sidebar collapse, theme)
│
├── types/                           # Shared TypeScript interfaces per domain
│   ├── auth.types.ts
│   ├── profile.types.ts
│   ├── application.types.ts
│   ├── opportunity.types.ts
│   ├── company.types.ts
│   ├── contact.types.ts
│   ├── interview.types.ts
│   ├── task.types.ts
│   └── analytics.types.ts
│
└── index.css                        # Tailwind directives and CSS variables
```

---

## 4. Key Cross-Domain Relational Decisions

### 4.1 Company → Contact → Application → Interview Chain
- A `Company` can have multiple `Contacts` (Recruiters, Hiring Managers, Interviewers).
- An `Application` links to a `Company`, an optional originating `Opportunity`, an optional primary `Contact` (Recruiter/Referral), and an immutable `Resume` version.
- An `Interview` belongs to an `Application`, links to a `Company`, and can associate with a primary `Contact` (Lead Interviewer) as well as specific interviewer names.
- All four entities can have associated polymorphic `Tasks`.

### 4.2 Immutable Resume & Document Versioning
- Applications record a foreign key to `resumes.id`.
- The `storage_key` of a `Resume` record is immutable once uploaded.
- If a candidate creates an updated resume ("Software Engineer v3"), it is stored as a new row. Existing applications remain attached to Resume v2.
- The `application_documents` table provides an N:M link between applications and supporting documents (transcripts, portfolios, cover letters) with timestamped records.

### 4.3 Opportunity to Application Conversion Snapshot
- An `Opportunity` can be saved and tracked.
- When converted to an `Application`, job data (title, company, description, salary, location) is snapshot into the `applications` record. This ensures that if the original opportunity posting expires or is deleted, the candidate's application history remains intact.
- The `Opportunity` status is automatically updated to `CONVERTED`.

### 4.4 Immutable Activity Audit Trail
- Every stage change, document attachment, note creation, and interview scheduling event generates an append-only row in `application_activity`.
- This ensures an audit trail that powers the Application Activity Timeline.

---

## 5. Security & Tenant Isolation

1. **Short-Lived Access Tokens**: Signed with HMAC-SHA256 (HS256), 15-minute expiration.
2. **Secure Refresh Cookies**: Refresh tokens are stored in `refresh_tokens` table, with the client token sent via an `HttpOnly`, `Secure`, `SameSite=Strict` cookie.
3. **Strict User Isolation**: Every database query is strictly filtered by `user_id == current_user.id`. No user can access or mutate another user's resources.
4. **Private Object Storage**: Files are stored under private storage keys. No public URLs exist. Downloads are streamed through authenticated endpoints or delivered via time-limited SAS tokens.
