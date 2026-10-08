# Career Platform — Personal Career Operating System

A production-ready, modular monolith web platform designed to manage the end-to-end candidate job-search lifecycle: from comprehensive profile management, resume versioning, and document vaults to opportunity discovery, application pipeline tracking, recruiter networking, interview preparation, unified calendar/tasks, and real data-driven career analytics.

---

## 🏛 Architecture Overview

```
React 18 + TypeScript + Tailwind CSS (Vite SPA)
                       ↓ (REST API / JSON / HttpOnly Cookies)
                 FastAPI Monolith
                       ↓ (SQLAlchemy 2.0 Async ORM)
             PostgreSQL 16 (31 Relational Tables)
                       +
        StorageService (Local / Azure Blob Storage)
```

- **Frontend**: React 18, TypeScript, Tailwind CSS, TanStack React Query, Zustand, Lucide Icons, Vite.
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy 2.0 (asyncio + asyncpg), Alembic, Pydantic v2.
- **Database**: PostgreSQL 16 with 31 normalized tables, foreign keys, cascade rules, composite indexes, and version locking.
- **Storage**: StorageService abstraction with LocalStorageProvider (dev) and AzureBlobStorageProvider (prod).

---

## 🧭 Navigation Hierarchy

The platform exposes 12 first-class domain hubs in the application shell:

1. **Dashboard** (`/dashboard`): Career command center (profile completeness %, active pipeline summary, upcoming interviews, today's tasks, pending follow-ups).
2. **Profile** (`/profile`): 13 dedicated career identity sections (Personal, Professional, Education, Experience, Projects, Skills, Certifications, Achievements, Languages, Resumes, Documents, Preferences, Links).
3. **Opportunities** (`/opportunities`, `/opportunities/saved`, `/opportunities/:id`): Manual entry and URL import discovery, saved opportunities, conversion to active application.
4. **Applications** (`/applications`, `/applications/pipeline`, `/applications/followups`, `/applications/:id`): Kanban pipeline board, table view, follow-ups, exact resume version locking, deterministic application health score, Q&A vault answers, notes, and chronological activity timeline.
5. **Companies** (`/companies`, `/companies/:id`): Company directory, recruitment history, linked applications, and key recruiter contacts.
6. **Interviews** (`/interviews`, `/interviews/:id`, `/interviews/:id/prep`): Multi-round interview tracking (screens, technical design, onsite), agenda, meeting links, and dedicated Interview Prep Hub (company/role research, anticipated questions, talking points, checklists).
7. **Tasks** (`/tasks`): Unified actionable task system across applications, interviews, contacts, and career milestones with priority levels and due dates.
8. **Calendar** (`/calendar`): Unified calendar view aggregating interviews, deadlines, follow-ups, and recruiter calls.
9. **Network** (`/network`, `/network/:id`): Professional contacts directory (recruiters, hiring managers, interviewers, referrals) with communication history.
10. **Analytics** (`/analytics`, `/analytics/trends`, `/analytics/pipeline`, `/analytics/companies`, `/analytics/outcomes`, `/analytics/time`): 6 sub-dashboards with real metrics (total applications, conversion funnel, response times, velocity, resume performance).
11. **Notifications** (`/notifications`): In-platform alerts, interview countdowns, and milestone updates.
12. **Settings** (`/settings`): Platform configuration (Account, Security, Notification channels, Privacy, Active Sessions, Data Export, Appearance, Account Deletion).

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- PostgreSQL 16 (or Docker)

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Backend Setup & Migrations
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at `http://localhost:5173`.

---

## 🐳 Docker Setup

### Local Development Stack
Run the development stack with live reloading (PostgreSQL 16, FastAPI backend with reload, Vite frontend on port 5173, Nginx reverse proxy):
```bash
docker compose up --build
```
- Web Application: `http://localhost`
- API Health Endpoint: `http://localhost/api/v1/health`
- API OpenAPI Docs: `http://localhost/docs`

### Production Stack (Pre-Deployment / Staging / Production VM)
The production stack uses compiled frontend static assets served through an internal Nginx container with SPA routing fallback, a hardened FastAPI backend, PostgreSQL 16 with health checks, and a perimeter Nginx gateway.

1. **Configure Production Environment**:
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with strong passwords, random 64-char SECRET_KEY, and allowed CORS origins
   ```

2. **Start Production Services**:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
   ```

3. **Apply Database Migrations**:
   ```bash
   docker exec career_platform_prod_backend alembic upgrade head
   ```

4. **Verify Production Services**:
   - Web Application & SPA Routes: `http://localhost` (or configured `$PROD_PORT`)
   - Direct API Healthcheck: `http://localhost/api/v1/health`
   - Gateway Security Headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection: 1; mode=block`
   - Client-side navigation (`/applications`, `/jobs`, `/login`) resolves to `/index.html` via Nginx SPA fallback without 404 errors.

5. **HTTPS / TLS Production Termination**:
   - For internet-facing deployment (AWS EC2 / ALB / CloudFront), terminate TLS (HTTPS on port 443) in front of the gateway.
   - When `ENVIRONMENT=production`, authentication cookies automatically enforce `Secure` and `SameSite=Strict`.

---

## 🧪 Verification & Testing

### Backend Unit Tests
```bash
cd backend
pytest -v tests/
```

### Frontend Type Check & Production Build
```bash
cd frontend
npm run build
```

---

## 🗺 Implementation Roadmap

- **Stage 0**: Architecture, Specifications, and Data Modeling *(Completed)*
- **Stage 1**: Scaffold, Database Schema (31 models), Migrations, Frontend Shell (12 Hubs), Storage Abstraction, Test Foundation *(Completed)*
- **Stage 2**: Authentication, Session Management, JWT Cookies *(Next)*
- **Stage 3**: Candidate Profile, Resume & Document Vaults, Preferences
- **Stage 4**: Opportunities & Saved Discovery
- **Stage 5**: Applications Pipeline, Version Locking, Health Rules, Q&A Vault
- **Stage 6**: Companies & Network Management
- **Stage 7**: Interviews & Interview Preparation Hub
- **Stage 8**: Tasks, Calendar & Notifications
- **Stage 9**: Dashboard & Analytics Engine
- **Stage 10**: Explainable Opportunity Matching Engine
- **Stage 11–16**: UI Polish, Security Hardening, Automated Testing, Cloud Deployment
