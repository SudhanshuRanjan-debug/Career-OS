# Frontend Architecture & Design System Specification
## Career & Job Application Management Platform — React + TypeScript Client

**Version:** 2.0.0
**Date:** 2026-09-07
**Status:** Stage 0 — Rectified Master Architecture

---

## 1. Technology Foundation

- **Core Library**: React 18 with TypeScript 5
- **Build Tool**: Vite (fast HMR, optimized ESM bundling)
- **Styling**: Tailwind CSS (utility-first with customized theme tokens)
- **Routing**: React Router v6 (declarative, nested route hierarchies)
- **Server State & Caching**: TanStack React Query v5
- **Client State**: Zustand (lightweight stores for auth session and UI state)
- **HTTP Client**: Axios (configured with request/response interceptors)
- **Icons**: Lucide React (clean, consistent SVG iconography)

---

## 2. Directory & Feature-Folder Structure

```
frontend/src/
├── app/
│   ├── router.tsx              # Central route definitions
│   └── providers.tsx           # Global providers (QueryClient, Auth, Theme)
│
├── components/
│   ├── ui/                     # Design System primitives
│   │   ├── Button.tsx          # Variants: primary, secondary, outline, danger, ghost
│   │   ├── Input.tsx           # Text input with labels, errors, and prefix/suffix icons
│   │   ├── Card.tsx            # Surface cards with header, body, footer
│   │   ├── Badge.tsx           # Status indicators with semantic color variants
│   │   ├── Modal.tsx           # Accessible dialogs with backdrop & focus management
│   │   ├── EmptyState.tsx      # Consistent zero-data illustrations & CTA buttons
│   │   ├── ProgressBar.tsx     # Percentage completion bars (completeness, health)
│   │   └── Dropdown.tsx        # Action dropdown menus
│   │
│   └── layout/
│       ├── AppShell.tsx        # Main authenticated shell (Sidebar + TopBar + Outlet)
│       ├── Sidebar.tsx         # 12-domain hierarchical navigation menu
│       ├── TopBar.tsx          # Universal search, notification badge, profile dropdown
│       ├── PageHeader.tsx      # Standardized title, breadcrumbs, action buttons
│       └── PublicLayout.tsx    # Clean centering layout for login, signup, reset
│
├── features/                   # 12 Major Domain Feature Modules
│   ├── auth/                   # SignInPage, SignUpPage, ForgotPasswordPage, ResetPasswordPage
│   ├── dashboard/              # DashboardPage, KPIs, PipelineWidget, UpcomingEvents
│   ├── profile/                # ProfileHubPage, Personal, Education, Experience, Resumes, etc.
│   ├── opportunities/          # OpportunitiesPage, SavedOpportunitiesPage, OpportunityDetailsPage
│   ├── applications/           # ApplicationsPage, PipelineKanbanPage, ApplicationDetailsPage
│   ├── companies/              # CompaniesPage, CompanyDetailsPage
│   ├── interviews/             # InterviewsPage, InterviewDetailsPage, InterviewPrepPage
│   ├── tasks/                  # TasksPage (Today, Upcoming, Completed tabs)
│   ├── calendar/               # CalendarPage (Unified schedule view)
│   ├── network/                # ContactsPage, ContactDetailsPage
│   ├── analytics/              # AnalyticsOverviewPage, TrendsPage, FunnelPage, TimeMetricsPage
│   ├── notifications/          # NotificationsPage
│   └── settings/               # SettingsHubPage, Account, Security, Sessions, Privacy, Data
│
├── lib/
│   ├── axios.ts                # Axios instance with auth bearer & refresh interceptor
│   └── queryClient.ts          # TanStack QueryClient setup with default stale times
│
├── store/
│   ├── authStore.ts            # Zustand store: user, isAuthenticated, token setter
│   └── uiStore.ts              # Zustand store: sidebarCollapsed, activeTheme, modalState
│
├── types/                      # Domain-specific TypeScript models & API DTOs
│   ├── auth.types.ts
│   ├── profile.types.ts
│   ├── application.types.ts
│   ├── opportunity.types.ts
│   ├── company.types.ts
│   ├── contact.types.ts
│   ├── interview.types.ts
│   ├── task.types.ts
│   ├── notification.types.ts
│   └── analytics.types.ts
│
├── utils/                      # Formatting helpers (dates, currency, stage labels)
│   ├── formatters.ts
│   └── constants.ts
│
├── index.css                   # Tailwind imports and design tokens
└── main.tsx                    # React DOM root mounting
```

---

## 3. Complete Route Hierarchy

```tsx
// Public Routes
/signin              → SignInPage
/signup              → SignUpPage
/forgot-password     → ForgotPasswordPage
/reset-password      → ResetPasswordPage

// Authenticated Routes (Wrapped by AppShell & ProtectedRoute)
/dashboard           → DashboardPage

/profile             → ProfileHubPage (default: Overview)
/profile/personal    → PersonalTab
/profile/professional→ ProfessionalTab
/profile/education   → EducationTab
/profile/experience  → ExperienceTab
/profile/projects    → ProjectsTab
/profile/skills      → SkillsTab
/profile/certifications → CertificationsTab
/profile/achievements→ AchievementsTab
/profile/languages   → LanguagesTab
/profile/resumes     → ResumesTab
/profile/documents   → DocumentsTab
/profile/preferences → PreferencesTab
/profile/links       → LinksTab

/opportunities       → OpportunitiesPage
/opportunities/saved → SavedOpportunitiesPage
/opportunities/:id   → OpportunityDetailsPage

/applications        → ApplicationsListPage
/applications/pipeline → ApplicationPipelineKanbanPage
/applications/followups → ApplicationFollowupsPage
/applications/:id    → ApplicationDetailsPage

/companies           → CompaniesListPage
/companies/:id       → CompanyDetailsPage

/interviews          → InterviewsPage
/interviews/:id      → InterviewDetailsPage
/interviews/:id/prep → InterviewPrepPage

/tasks               → TasksPage
/calendar            → CalendarPage

/network             → ContactsListPage
/network/:id         → ContactDetailsPage

/analytics           → AnalyticsOverviewPage
/analytics/trends    → AnalyticsTrendsPage
/analytics/pipeline  → AnalyticsPipelinePage
/analytics/companies → AnalyticsCompaniesPage
/analytics/outcomes  → AnalyticsOutcomesPage
/analytics/time      → AnalyticsTimePage

/notifications       → NotificationsPage

/settings            → SettingsHubPage (default: General/Account)
/settings/account    → AccountSettingsTab
/settings/security   → SecuritySettingsTab
/settings/notifications → NotificationSettingsTab
/settings/privacy    → PrivacySettingsTab
/settings/sessions   → ActiveSessionsTab
/settings/data       → DataExportTab
/settings/appearance → AppearanceSettingsTab
/settings/danger     → DeleteAccountTab

// Published Jobs Discovery (Candidate & Authenticated)
/jobs                → JobDiscoveryPage
/jobs/:id            → JobDetailsPage

// Recruiter Authenticated Routes (RoleRoute allowedRoles=['HIRER'])
/recruiter/jobs      → RecruiterJobsPage
/recruiter/jobs/new  → CreateJobPage
/recruiter/jobs/:id  → RecruiterJobDetailsPage
/recruiter/jobs/:id/edit → EditJobPage
/recruiter/jobs/:id/applicants → JobApplicantsPage
/recruiter/applicants → RecruiterApplicantsPage
/recruiter/applications/:id → ApplicantReviewPage
/recruiter/interviews → RecruiterInterviewsPage
/recruiter/organization → OrganizationProfilePage
/recruiter/analytics → RecruiterAnalyticsPage
```

---

## 4. State Management Philosophy

1. **Server State (TanStack React Query)**:
   - All asynchronous data (Profile, Applications, Companies, Tasks, Analytics) is managed via React Query hooks.
   - Configured with `staleTime: 60_000` (1 minute) to reduce unnecessary network requests while maintaining fresh data.
   - Automatic cache invalidation on mutations (e.g. updating an application status automatically invalidates `['applications']` and `['dashboard-summary']`).

2. **Client Transient State (Zustand)**:
   - **Auth Store**: Stores the current user object and access token in memory. Never stores sensitive refresh tokens in `localStorage`.
   - **UI Store**: Stores responsive sidebar collapsed state, active dialog modals, and theme preferences.

---

## 5. Design System Tokens & Guidelines

- **Typography**: Clean, highly readable system font stack with fallback to modern sans-serif.
- **Color Palette**:
  - **Brand Primary**: Indigo / Blue (`#3B82F6` / `#2563EB`)
  - **Success**: Emerald (`#10B981`)
  - **Warning**: Amber (`#F59E0B`)
  - **Danger**: Rose (`#EF4444`)
  - **Neutrals**: Slate (`#0F172A` to `#F8FAFC`)
- **Interactive Affordance**:
  - Consistent focus rings (`focus:ring-2 focus:ring-primary-500 focus:outline-none`).
  - Subtle hover transitions (`transition-all duration-150 ease-in-out`).
  - Clear active tab indicators and accessible ARIA attributes.
- **State Feedback**:
  - Every async view features explicit **Loading** (skeleton screens), **Error** (retry banner), and **Empty** states.
  - Destructive operations (Delete Application, Delete Account) require modal confirmation.
