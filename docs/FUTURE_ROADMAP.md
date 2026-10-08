# Future Roadmap & Data Engineering Architecture
## Career & Job Application Management Platform — Long-Term Evolution

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Staged Development Milestones (Stages 0–16)

```
[STAGE 0] Product & Domain Architecture (Complete Specs, DB Design, API Spec, Flows)
    ↓
[STAGE 1] Project Scaffold (Postgres 16, 28+ Models, Alembic, FastAPI, React 12-Hub Shell)
    ↓
[STAGE 2] Authentication & Session Management (JWT, Refresh Cookies, Password Reset)
    ↓
[STAGE 3] Candidate Profile, Resumes & Document Vault (Profile CRUD, Completeness Engine)
    ↓
[STAGE 4] Opportunities & Saved Queue (Discovery, Search, One-Click Convert to Application)
    ↓
[STAGE 5] Applications, Pipeline & Health Engine (Kanban, Stage History, Q&A Vault, Health Score)
    ↓
[STAGE 6] Companies & Network Directory (Recruiter/Referral Directory linked to Apps)
    ↓
[STAGE 7] Interviews & Preparation (Scheduling, Checklist, Research, Debrief Notes)
    ↓
[STAGE 8] Tasks, Calendar & In-App Notifications (Polymorphic Tasks, Schedule Aggregation)
    ↓
[STAGE 9] Career Command Dashboard & Real Analytics (Funnel Metrics, Response Rates, Trends)
    ↓
[STAGE 10] Explainable Matching Engine (Deterministic Rule-Based Profile ↔ Job Match)
    ↓
[STAGE 11] UI/UX Refinement & Accessibility (WCAG AA, Micro-interactions, Keyboard Navigation)
    ↓
[STAGE 12] Full Functional Testing (Pytest, React Component Tests, End-to-End Workflows)
    ↓
[STAGE 13] Security Hardening (Rate Limits, CORS, CSRF, CSP, Dependency Scans)
    ↓
[STAGE 14] Security Testing & Penetration Audit (OWASP Top 10, Auth Boundary Verification)
    ↓
[STAGE 15] Production Cloud Deployment (Azure Container Apps, Azure PostgreSQL, Azure Blob)
    ↓
[STAGE 16] Monitoring, Observability & Maintenance (Azure Monitor, Application Insights, Backups)
```

---

## 2. Future Data Engineering & Analytics Pipeline

As application and user volume grows, the platform is architected to transition from direct relational queries to an enterprise data lakehouse pipeline without modifying the transactional schema.

```
┌─────────────────────────┐
│     PostgreSQL 16       │
│  Transactional Database │
└───────────┬─────────────┘
            │
            ▼ CDC / Incremental Batch Ingestion (Python ETL / Airflow)
┌─────────────────────────┐
│     Parquet Storage     │
│   (Azure Data Lake Gen2)│
│  Partitioned by user/date│
└───────────┬─────────────┘
            │
            ▼ Distributed Processing & Transformation
┌─────────────────────────┐
│      Apache Spark       │
│    (PySpark on Azure)   │
│  - Cohort conversion    │
│  - Time-to-offer models │
│  - Industry benchmarks  │
└───────────┬─────────────┘
            │
            ▼ Dimensional Serving
┌─────────────────────────┐
│  Analytical Warehouse   │
│  - Fact/Dimension tables│
│  - Executive Insights   │
└─────────────────────────┘
```

### Engineering Guardrails
- **No Premature Big Data**: Do NOT introduce PySpark or Kafka in Stage 1. PostgreSQL 16 indexes easily handle hundreds of thousands of application records with sub-millisecond aggregations.
- **Parquet Analytical Export**: Clean schemas with typed fields allow direct zero-copy conversion to Apache Arrow / Parquet when bulk data export or analytics is required.

---

## 3. Future Intelligence & Matching Strategy

### 3.1 Explainable Matching (Stage 10)
- Instead of black-box AI scores, the matching engine uses transparent, deterministic scoring:
  - **Skill Alignment** (40%): Direct overlap between candidate technical skills and opportunity requirements.
  - **Role & Experience Fit** (20%): Match between candidate years of experience and role expectations.
  - **Location & Work Mode Fit** (20%): Remote/hybrid preferences vs job posting location.
  - **Compensation Alignment** (20%): Minimum salary requirements vs offered range.
- Output presents transparent breakdown: "85% Match: +Matched Python, SQL; -Missing Docker experience".

### 3.2 Machine Learning & Natural Language Processing (Post-Stage 16)
- **Resume Parsing**: Safe, local PDF extraction using standard libraries (e.g. `pdfminer.six` / `PyPDF2`) to auto-populate profile fields with human confirmation.
- **Skill Taxonomy Extraction**: Standardizing skill variations (e.g. "ReactJS", "React.js" → "React") using curated taxonomies.
- **Interview Coaching Assistant**: Context-aware interview practice questions generated from job description requirements and the candidate's actual projects.

---

## 4. External Integrations (Post-MVP)

- **Calendar Sync**: Dynamic `.ics` subscription feed allowing Google Calendar, Apple Calendar, and Outlook to display upcoming interviews and task deadlines.
- **Verified Job Feeds**: Official employer API feeds (Greenhouse, Lever, Workday) for direct application status polling without fragile web scraping.
- **Communication Log**: Email thread integration (via IMAP/OAuth) to automatically track recruiter email timestamps on application activity timelines.
