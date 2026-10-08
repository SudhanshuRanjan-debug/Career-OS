# REST API Specification
## Career & Job Application Management Platform — v1 API

**Version:** 2.0.0
**Date:** 2026-09-07
**Base URL:** `/api/v1`
**Format:** JSON (UTF-8)
**Security:** Bearer JWT in `Authorization: Bearer <access_token>` header + HttpOnly Cookie for refresh

---

## 1. Global Conventions

- **Timestamps**: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SS.mmmmmmZ`).
- **Identifiers**: Standard UUIDv4 lowercase strings (`123e4567-e89b-12d3-a456-426614174000`).
- **Pagination**: Paginated endpoints accept `?page=1&page_size=20&sort_by=created_at&sort_order=desc` and return:
  ```json
  {
    "items": [...],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
  ```
- **Error Response Structure**:
  ```json
  {
    "error_code": "RESOURCE_NOT_FOUND",
    "message": "The requested application does not exist",
    "details": null
  }
  ```

---

## 2. Authentication Domain (`/auth`)

| Method | Endpoint | Description | Auth Required |
|:-------|:---------|:------------|:-------------:|
| `POST` | `/auth/register` | Create account & candidate profile scaffold | No |
| `POST` | `/auth/login` | Authenticate with email/password; returns JWT + sets HttpOnly cookie | No |
| `POST` | `/auth/refresh` | Exchange HttpOnly refresh cookie for fresh access token | No (Cookie) |
| `POST` | `/auth/logout` | Revoke active refresh token and clear cookie | Yes |
| `POST` | `/auth/forgot-password` | Initiate password reset email | No |
| `POST` | `/auth/reset-password` | Submit new password with verification token | No |
| `GET`  | `/auth/me` | Return current authenticated user info | Yes |

---

## 3. Candidate Profile Domain (`/profile`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/profile/overview` | Aggregated candidate profile overview & completeness score |
| `GET`  | `/profile/personal` | Get personal information (name, contact, location) |
| `PUT`  | `/profile/personal` | Update personal information |
| `GET`  | `/profile/professional` | Get professional headline, summary, current role |
| `PUT`  | `/profile/professional` | Update professional headline & summary |
| `GET`  | `/profile/preferences` | Get job search preferences |
| `PUT`  | `/profile/preferences` | Update job search preferences |
| `GET`  | `/profile/completeness` | Get explainable profile completeness breakdown |

### Profile Subsections (CRUD)
- **Education**: `GET/POST /profile/education`, `PUT/DELETE /profile/education/:id`
- **Experience**: `GET/POST /profile/experience`, `PUT/DELETE /profile/experience/:id`
- **Projects**: `GET/POST /profile/projects`, `PUT/DELETE /profile/projects/:id`
- **Skills**: `GET/POST /profile/skills`, `PUT/DELETE /profile/skills/:id`
- **Certifications**: `GET/POST /profile/certifications`, `PUT/DELETE /profile/certifications/:id`
- **Achievements**: `GET/POST /profile/achievements`, `PUT/DELETE /profile/achievements/:id`
- **Languages**: `GET/POST /profile/languages`, `PUT/DELETE /profile/languages/:id`
- **Links**: `GET/POST /profile/links`, `PUT/DELETE /profile/links/:id`

---

## 4. Resumes & Document Vault (`/resumes`, `/documents`)

### Resumes
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/resumes` | List candidate resumes with version numbers |
| `POST` | `/resumes/upload` | Upload new resume PDF/DOCX (creates version record) |
| `PUT`  | `/resumes/:id` | Update resume label/name |
| `POST` | `/resumes/:id/set-default` | Designate resume as default for new applications |
| `GET`  | `/resumes/:id/download` | Stream authorized resume file |
| `DELETE` | `/resumes/:id` | Soft-delete resume (preserves historical applications) |

### Document Vault
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/documents` | List private documents (filtered by `doc_type`) |
| `POST` | `/documents/upload` | Upload private document (cover letter, transcript, etc.) |
| `GET`  | `/documents/:id/download` | Stream authorized private document |
| `DELETE` | `/documents/:id` | Soft-delete private document |

---

## 5. Opportunities Domain (`/opportunities`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/opportunities` | List & search opportunities with status/location filters |
| `POST` | `/opportunities` | Create opportunity manually or via clean URL import |
| `GET`  | `/opportunities/:id` | Get opportunity details |
| `PUT`  | `/opportunities/:id` | Update opportunity fields |
| `DELETE`| `/opportunities/:id` | Delete opportunity |
| `POST` | `/opportunities/:id/save` | Bookmark opportunity to saved list |
| `DELETE`| `/opportunities/:id/save` | Remove opportunity from saved list |
| `GET`  | `/opportunities/saved` | List saved opportunities |
| `POST` | `/opportunities/:id/convert` | Convert opportunity into application (creates snapshot) |

---

## 6. Applications Domain (`/applications`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/applications` | List applications with filters (status, stage, company) |
| `POST` | `/applications` | Create application with company, stage, and resume version |
| `GET`  | `/applications/pipeline` | Group applications by recruitment stage for Kanban board |
| `GET`  | `/applications/:id` | Get application details, linked resume, recruiter, documents |
| `PUT`  | `/applications/:id` | Update application details |
| `DELETE`| `/applications/:id` | Delete application |
| `POST` | `/applications/:id/stage` | Transition stage (records stage history & activity) |
| `GET`  | `/applications/:id/stage-history` | View immutable stage transition history |
| `GET`  | `/applications/:id/activity` | View immutable application activity timeline |
| `GET`  | `/applications/:id/health` | Calculate deterministic application health score |

### Application Sub-Resources
- **Notes**: `GET/POST /applications/:id/notes`, `PUT/DELETE /applications/:id/notes/:note_id`
- **Follow-ups**: `GET/POST /applications/:id/followups`, `PUT/DELETE /applications/:id/followups/:followup_id`
- **Documents**: `GET/POST /applications/:id/documents`, `DELETE /applications/:id/documents/:doc_id`
- **Q&A Answers**: `GET/POST /applications/:id/answers`, `PUT/DELETE /applications/:id/answers/:ans_id`

---

## 7. Q&A Vault Domain (`/qa-vault`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/qa-vault` | List reusable Q&A answers (filter by category) |
| `POST` | `/qa-vault` | Create reusable Q&A answer template |
| `PUT`  | `/qa-vault/:id` | Update Q&A answer template |
| `DELETE`| `/qa-vault/:id` | Delete Q&A template |

---

## 8. Companies Domain (`/companies`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/companies` | List companies with search and industry filters |
| `POST` | `/companies` | Add new target company |
| `GET`  | `/companies/:id` | Get company details with linked applications & contacts |
| `PUT`  | `/companies/:id` | Update company information |
| `DELETE`| `/companies/:id` | Delete company |

---

## 9. Network & Contacts Domain (`/network/contacts`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/network/contacts` | List contacts with search and type filters (Recruiter, etc.) |
| `POST` | `/network/contacts` | Add new professional contact (link to company optional) |
| `GET`  | `/network/contacts/:id` | Get contact details with linked company & interactions |
| `PUT`  | `/network/contacts/:id` | Update contact information |
| `DELETE`| `/network/contacts/:id` | Delete contact |

---

## 10. Interviews Domain (`/interviews`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/interviews` | List interviews (filter: upcoming, completed, cancelled) |
| `POST` | `/interviews` | Schedule new interview (link to application, company, contact) |
| `GET`  | `/interviews/:id` | Get interview details |
| `PUT`  | `/interviews/:id` | Update interview details |
| `DELETE`| `/interviews/:id` | Delete interview |
| `GET`  | `/interviews/:id/preparation` | Get interview research notes & checklist |
| `PUT`  | `/interviews/:id/preparation` | Save interview prep checklist, questions, and notes |

---

## 11. Tasks & Calendar Domain (`/tasks`, `/calendar`)

### Tasks
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/tasks` | List tasks (filters: today, upcoming, completed, related_type) |
| `POST` | `/tasks` | Create task linked to Application, Interview, Company, Contact |
| `PUT`  | `/tasks/:id` | Update task fields |
| `POST` | `/tasks/:id/complete` | Mark task as completed |
| `DELETE`| `/tasks/:id` | Delete task |

### Calendar
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/calendar` | Get aggregated schedule events for date range (`start`, `end`) |

---

## 12. In-App Notifications Domain (`/notifications`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/notifications` | List user notifications (filter by unread) |
| `POST` | `/notifications/:id/read` | Mark specific notification as read |
| `POST` | `/notifications/read-all` | Mark all unread notifications as read |

---

## 13. Career Analytics Domain (`/analytics`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/analytics/overview` | High-level KPIs (total apps, active, response rate, offers) |
| `GET`  | `/analytics/trends` | Application submission volume grouped by month/week |
| `GET`  | `/analytics/pipeline` | Funnel stage conversion rates |
| `GET`  | `/analytics/companies` | Breakdown of applications and response rates by company |
| `GET`  | `/analytics/outcomes` | Offer vs. rejection vs. withdrawal distribution |
| `GET`  | `/analytics/time` | Time-to-interview, time-to-offer, average stage duration |

---

## 14. Dashboard Domain (`/dashboard`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/dashboard/summary` | Unified command center aggregation (profile completeness, pipeline counts, upcoming interviews, today's tasks, pending follow-ups, saved opportunities, quick stats) |

---

## 15. Settings Domain (`/settings`)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET`  | `/settings/account` | Get account details (email, username) |
| `PUT`  | `/settings/account` | Update account email/username |
| `PUT`  | `/settings/security/password` | Change user password (verifies current password) |
| `GET`  | `/settings/sessions` | List active sessions (user-agent, IP, issued date) |
| `DELETE`| `/settings/sessions/:id` | Revoke specific session |
| `DELETE`| `/settings/sessions` | Revoke all other active sessions |
| `GET`  | `/settings/notifications` | Get notification preference switches |
| `PUT`  | `/settings/notifications` | Update notification preferences |
| `POST` | `/settings/data-export` | Request GDPR-compliant full data export |
| `DELETE`| `/settings/account` | Permanently delete account and all data (requires password) |

---

## 16. Published Job Discovery Domain (`/jobs`)

Accessible to authenticated Candidates (and public/authenticated users for reading).

| Method | Endpoint | Description | Role Required |
|:-------|:---------|:------------|:-------------:|
| `GET`  | `/jobs` | List published job postings with query, location, type, and skill filters | Any |
| `GET`  | `/jobs/:id` | View published job posting details and company information | Any |
| `POST` | `/jobs/:id/save` | Bookmark published job to candidate's saved opportunities | CANDIDATE |
| `POST` | `/jobs/:id/apply` | Apply to published job posting (attaches `resume_id` and cover letter) | CANDIDATE |

---

## 17. Recruiter Organization & Job Management (`/recruiter`)

Requires authenticated user with `role == 'HIRER'`.

### Organization Management
| Method | Endpoint | Description | Role Required |
|:-------|:---------|:------------|:-------------:|
| `GET`  | `/recruiter/organization` | Get current hirer's organization profile | HIRER |
| `PUT`  | `/recruiter/organization` | Update organization name, website, industry, description | HIRER |

### Job Postings Management
| Method | Endpoint | Description | Role Required |
|:-------|:---------|:------------|:-------------:|
| `GET`  | `/recruiter/jobs` | List job postings owned by current hirer's organization | HIRER |
| `POST` | `/recruiter/jobs` | Create new job posting in `DRAFT` status | HIRER |
| `GET`  | `/recruiter/jobs/:id` | Get full job posting details (including draft/closed/archived) | HIRER |
| `PUT`  | `/recruiter/jobs/:id` | Update job posting fields | HIRER |
| `DELETE`| `/recruiter/jobs/:id` | Delete job posting (permitted ONLY if 0 applications exist) | HIRER |
| `POST` | `/recruiter/jobs/:id/publish` | Transition status from `DRAFT` to `PUBLISHED` | HIRER |
| `POST` | `/recruiter/jobs/:id/close` | Transition status to `CLOSED` (stops new applications) | HIRER |
| `POST` | `/recruiter/jobs/:id/archive` | Transition status to `ARCHIVED` (historical read-only) | HIRER |

---

## 18. Recruiter Applicant Management & Hiring Analytics

Requires authenticated user with `role == 'HIRER'`.

### Applicant Pipeline & Review
| Method | Endpoint | Description | Role Required |
|:-------|:---------|:------------|:-------------:|
| `GET`  | `/recruiter/jobs/:id/applicants` | List applications submitted to a specific job posting | HIRER |
| `GET`  | `/recruiter/applications` | List all applicants across all organization jobs | HIRER |
| `GET`  | `/recruiter/applications/:id` | Get application-specific candidate summary, answers, and timeline | HIRER |
| `GET`  | `/recruiter/applications/:id/resume` | Stream candidate's submitted application resume | HIRER |
| `POST` | `/recruiter/applications/:id/stage` | Transition applicant stage (`PHONE_SCREEN`, `INTERVIEW`, `OFFER`, `REJECTED`) | HIRER |

### Hiring Analytics
| Method | Endpoint | Description | Role Required |
|:-------|:---------|:------------|:-------------:|
| `GET`  | `/recruiter/analytics/overview` | Active jobs, total applicants, scheduled interviews, offers | HIRER |
| `GET`  | `/recruiter/analytics/pipeline` | Funnel conversion across recruitment stages | HIRER |
