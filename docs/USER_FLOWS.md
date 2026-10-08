# User Flows & Lifecycle Journeys
## Career & Job Application Management Platform — Career Operating System

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. End-to-End Career Operating System Lifecycle

The platform guides a candidate through an integrated, continuous career management cycle:

```
Candidate Profile
       ↓
Career Information (Experience, Education, Projects, Skills)
       ↓
Resume / Documents Vault (Targeted Versions & Credentials)
       ↓
Job Preferences (Roles, Comp, Locations, Remote/Hybrid)
       ↓
Opportunity Discovery (Manual Entry, URL Import, Saved Queue)
       ↓
Opportunity → Application Conversion (Snapshotting Job Data)
       ↓
Application Pipeline (List & Kanban, Stage History, Health Engine)
       ↓
Recruiter / Company / Network Directory (Contact Touchpoints)
       ↓
Interview & Preparation (Checklists, Role Research, Debrief Notes)
       ↓
Tasks / Follow-ups / Calendar (Unified Schedule & Action Items)
       ↓
Offer / Outcome (Negotiation, Decision Logging)
       ↓
Career Analytics & Future Intelligence (Funnel Metrics & Trends)
```

---

## 2. Onboarding & Account Creation Flow

```
New Visitor
    │
    ▼
/signup
    ├── Enter Email, Username, Password
    ├── Password strength validation
    ▼
POST /auth/register
    ├── Creates User record
    ├── Auto-provisions empty CandidateProfile and CandidatePreferences
    ├── Issues Access Token + sets HttpOnly Refresh Token cookie
    ▼
/dashboard (First-Time User View)
    ├── Welcoming state: "Welcome to your Career Operating System"
    ├── Profile Completeness banner at 0%
    ├── Primary CTA: "Complete Your Candidate Profile"
    ├── Secondary Quick Actions: Upload Resume, Set Job Preferences
```

---

## 3. Profile & Career Identity Flow

```
/profile (Comprehensive Tabbed Hub)
    │
    ├── Overview Tab (`/profile`)
    │       View aggregate profile summary and completeness breakdown
    │
    ├── Personal Tab (`/profile/personal`)
    │       Name, preferred name, phone, city, state, country, timezone, headline
    │
    ├── Professional Tab (`/profile/professional`)
    │       Professional summary, current role, years of exp, notice period
    │
    ├── Education Tab (`/profile/education`)
    │       Add/Edit/Reorder institution, degree, field of study, GPA, dates
    │
    ├── Experience Tab (`/profile/experience`)
    │       Add/Edit/Reorder company, job title, employment type, location, responsibilities
    │
    ├── Projects Tab (`/profile/projects`)
    │       Add/Edit projects, tech stack badges, GitHub repo URL, live URL
    │
    ├── Skills Tab (`/profile/skills`)
    │       Add technical, soft, tool, cloud, framework skills with proficiency
    │
    ├── Certifications Tab (`/profile/certifications`)
    │       Add certifications with issuing org, credential ID, URL, expiry
    │
    ├── Achievements Tab (`/profile/achievements`)
    │       Awards, hackathons, publications, scholarships, leadership
    │
    ├── Languages Tab (`/profile/languages`)
    │       Languages and proficiency levels (Native, Fluent, Professional, etc.)
    │
    ├── Resumes Tab (`/profile/resumes`)
    │       Upload multiple versioned resumes, set default, download, rename
    │
    ├── Documents Tab (`/profile/documents`)
    │       Private vault for cover letters, transcripts, certificates, portfolios
    │
    ├── Preferences Tab (`/profile/preferences`)
    │       Job titles, industries, locations, work arrangement, target compensation
    │
    └── Links Tab (`/profile/links`)
            LinkedIn, GitHub, Portfolio, LeetCode, Kaggle, personal website
```

---

## 4. Resume & Document Management Flow

```
Resume Upload:
    User clicks "Upload Resume"
    ├── Select PDF or DOCX file (max 10MB)
    ├── Input descriptive name (e.g. "Cloud & DevOps Resume v2")
    ├── File streamed to StorageService (LocalStorage in dev, Azure Blob in prod)
    ├── Generates unique storage_key
    └── Inserts record into `resumes` table with version number

Resume Version Pinning:
    User creates Application
    ├── System auto-selects default resume or user selects specific version
    ├── Application stores foreign key `resume_id` referencing that exact resume row
    └── When a candidate later uploads "Cloud & DevOps Resume v3", the historical
        application continues pointing to v2. Storage keys are never mutated in place.

Document Vault:
    User uploads supporting documents (Cover letters, transcripts, references)
    ├── Tagged with `doc_type`
    ├── Stored privately via StorageService
    └── Can be attached to specific applications via `application_documents`
```

---

## 5. Opportunity Discovery & Conversion Flow

```
/opportunities
    │
    ├── Browse & Search
    │       Filter by status (Active, Saved, Considering, Applied, Archived)
    │       Filter by location type (Remote, Hybrid, On-site)
    │
    ├── Add Opportunity
    │       Option A: Manual Form (Title, Company, URL, Comp, Description)
    │       Option B: Clean URL Import (Pastes URL, auto-populates metadata)
    │
    ├── Save / Bookmark
    │       Click bookmark → moves to Saved Queue (`/opportunities/saved`)
    │
    └── Convert to Application
            User clicks "Convert to Application"
            ├── Confirmation modal with pre-filled snapshot of job title & company
            ├── Select resume version to attach
            ├── Click "Confirm & Create Application"
            ├── Backend creates application with frozen job snapshot
            ├── Opportunity marked as status = 'CONVERTED'
            └── Redirects user to new `/applications/:id` detail page
```

---

## 6. Application Pipeline & Tracking Flow

```
/applications
    │
    ├── Toggle View: List Table or Kanban Board (`/applications/pipeline`)
    │       Columns: APPLIED → PHONE_SCREEN → ASSESSMENT → INTERVIEW → OFFER → ACCEPTED
    │
    ├── Application Details (`/applications/:id`)
    │       ├── Overview: Job title, Company, Location, Compensation, Source
    │       ├── Resume Used: Download link for exact resume version submitted
    │       ├── Recruiter / Contact: Linked primary contact from Network directory
    │       ├── Stage Progression:
    │       │     Move to next stage (e.g., "Schedule Phone Screen")
    │       │     Triggers modal for stage notes & date
    │       │     Appends record to `application_stage_history`
    │       │     Appends event to `application_activity`
    │       ├── Notes Tab: Timestamped discussion and interview feedback notes
    │       ├── Follow-ups Tab: Scheduled follow-up dates with completion checkboxes
    │       ├── Documents Tab: Linked cover letter or submission artifacts
    │       ├── Q&A Answers Tab: Custom responses pulled from or saved to Q&A Vault
    │       ├── Activity Timeline Tab: Full immutable audit trail of all actions
    │       └── Application Health Badge:
    │             Explains score (e.g., 85% Health: "Missing recruiter contact link")
```

---

## 7. Company & Network Directory Flow

```
Companies (`/companies`)
    │
    ├── Browse companies, industries, sizes, and locations
    ├── View Company Details (`/companies/:id`):
    │       ├── Associated applications (past & active)
    │       ├── Associated interviews
    │       ├── Associated contacts (recruiters, employees)
    │       └── Company research notes
    │
Network Contacts (`/network`)
    │
    ├── Directory of professional contacts
    ├── Categorized by: Recruiter, Hiring Manager, Interviewer, Referral, Employee
    ├── Link contacts to Companies and specific Applications
    └── Record notes from interactions and email touchpoints
```

---

## 8. Interview Management & Preparation Flow

```
/interviews
    │
    ├── Tabs: Upcoming | Completed | Cancelled
    │
    ├── Schedule Interview:
    │       Select Application, Company, Contact (Lead Interviewer)
    │       Set round type (Technical, HR, System Design, Behavioral, Panel)
    │       Set date, start/end time, timezone, video meeting URL
    │       Generates associated task automatically
    │
    └── Interview Preparation (`/interviews/:id/prep`):
            ├── Pre-Interview Checklist (e.g., "Test webcam", "Review portfolio")
            ├── Company Research & Products Notes
            ├── Role-Specific Talking Points
            ├── Questions to Ask the Interviewer
            └── Post-Interview Debrief Notes & Outcome Result logging
```

---

## 9. Unified Tasks, Calendar & Notifications Flow

```
Tasks (`/tasks`)
    ├── Filter: Today | Upcoming | Completed
    ├── Polymorphic linking: Link task to an Application, Interview, Company, or Contact
    └── Quick complete checkbox updates task status and records completion date

Calendar (`/calendar`)
    ├── Monthly and Weekly views
    └── Aggregates cross-domain events on a single grid:
            - Scheduled Interviews (with meeting link quick actions)
            - Task Due Dates
            - Application Deadlines
            - Application Follow-up Milestones

Notifications (`/notifications`)
    ├── In-app notification bell in TopBar
    ├── Real-time indicators for:
    │       - Upcoming interviews within 24 hours
    │       - Tasks due today or overdue
    │       - Applications with pending follow-ups
    └── Mark as read / mark all as read actions
```

---

## 10. Career Analytics Flow

```
/analytics
    │
    ├── Overview KPIs: Total Applications, Active Pipeline, Response Rate, Offer Rate
    ├── Application Trends: Submissions over time (weekly/monthly bar chart)
    ├── Pipeline Funnel: Conversion rates from Applied → Screen → Interview → Offer
    ├── Company Insights: Application volume and outcome distribution by company
    ├── Outcome Breakdown: Doughnut chart of Accepted, Rejected, and Withdrawn apps
    └── Time Metrics: Average days to first response, average days from interview to offer
```
