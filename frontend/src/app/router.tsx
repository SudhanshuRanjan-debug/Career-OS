import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

// Layouts
import { AppShell } from "@/components/layout/AppShell";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuthStore } from "@/store/authStore";

// Auth Features
import { SignInPage } from "@/features/auth/SignInPage";
import { SignUpPage } from "@/features/auth/SignUpPage";
import { ForgotPasswordPage } from "@/features/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage";

// Dashboard
import { DashboardPage } from "@/features/dashboard/DashboardPage";

// Profile Hub
import {
  ProfileHubPage,
  PersonalInfoTab,
  ProfessionalSummaryTab,
  EducationTab,
  ExperienceTab,
  ProjectsTab,
  SkillsTab,
  CertificationsTab,
  AchievementsTab,
  LanguagesTab,
  ResumesTab,
  DocumentsTab,
  PreferencesTab,
  LinksTab,
} from "@/features/profile";

// Opportunities
import { OpportunitiesPage } from "@/features/opportunities/OpportunitiesPage";
import { SavedOpportunitiesPage } from "@/features/opportunities/SavedOpportunitiesPage";
import { OpportunityDetailsPage } from "@/features/opportunities/OpportunityDetailsPage";

// Applications
import { ApplicationsPage } from "@/features/applications/ApplicationsPage";
import { PipelineKanbanPage } from "@/features/applications/PipelineKanbanPage";
import { ApplicationFollowupsPage } from "@/features/applications/ApplicationFollowupsPage";
import { ApplicationDetailsPage } from "@/features/applications/ApplicationDetailsPage";

// Companies
import { CompaniesPage } from "@/features/companies/CompaniesPage";
import { CompanyDetailsPage } from "@/features/companies/CompanyDetailsPage";

// Interviews
import { InterviewsPage } from "@/features/interviews/InterviewsPage";
import { InterviewDetailsPage } from "@/features/interviews/InterviewDetailsPage";
import { InterviewPrepPage } from "@/features/interviews/InterviewPrepPage";

// Tasks & Calendar
import { TasksPage } from "@/features/tasks/TasksPage";
import { CalendarPage } from "@/features/calendar/CalendarPage";

// Network / Contacts
import { ContactsPage } from "@/features/contacts/ContactsPage";
import { ContactDetailsPage } from "@/features/contacts/ContactDetailsPage";

// Analytics Hub & Subpages
import { AnalyticsOverviewPage } from "@/features/analytics/AnalyticsOverviewPage";
import { AnalyticsTrendsPage } from "@/features/analytics/AnalyticsTrendsPage";
import { AnalyticsPipelinePage } from "@/features/analytics/AnalyticsPipelinePage";
import { AnalyticsCompaniesPage } from "@/features/analytics/AnalyticsCompaniesPage";
import { AnalyticsOutcomesPage } from "@/features/analytics/AnalyticsOutcomesPage";
import { AnalyticsTimePage } from "@/features/analytics/AnalyticsTimePage";

// Notifications & Settings
import { NotificationsPage } from "@/features/notifications/NotificationsPage";
import { SettingsHubPage } from "@/features/settings/SettingsHubPage";

// Shortcuts for Resumes and Documents
import { ResumesPage } from "@/features/resumes/ResumesPage";
import { DocumentsPage } from "@/features/documents/DocumentsPage";

// Two-Sided Platform: Jobs & Recruiter
import { JobDiscoveryPage } from "@/features/jobs/JobDiscoveryPage";
import { RecruiterJobsPage } from "@/features/recruiter/RecruiterJobsPage";
import { JobApplicantsPage } from "@/features/recruiter/JobApplicantsPage";
import { OrganizationProfilePage } from "@/features/recruiter/OrganizationProfilePage";

// Root Auth-Aware Redirect Component
const RootRoute: React.FC = () => {
  const { user, isAuthenticated, isInitializing, initializeAuth } = useAuthStore();

  React.useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white font-bold text-2xl shadow-md animate-pulse">
            C
          </div>
          <div className="flex items-center gap-2 text-slate-500 text-xs font-medium">
            <svg
              className="animate-spin h-4 w-4 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Verifying Career OS session...
          </div>
        </div>
      </div>
    );
  }

  if (isAuthenticated && user) {
    const dest = user.role === "HIRER" ? "/recruiter/jobs" : "/dashboard";
    return <Navigate to={dest} replace />;
  }

  return <Navigate to="/login" replace />;
};

export const router = createBrowserRouter([
  // Root Auth-Aware Route
  {
    path: "/",
    element: <RootRoute />,
  },

  // Public / Authentication Routes
  {
    element: <PublicLayout />,
    children: [
      {
        path: "/login",
        element: <SignInPage />,
      },
      {
        path: "/signin",
        element: <Navigate to="/login" replace />,
      },
      {
        path: "/signup",
        element: <SignUpPage />,
      },
      {
        path: "/forgot-password",
        element: <ForgotPasswordPage />,
      },
      {
        path: "/reset-password",
        element: <ResetPasswordPage />,
      },
    ],
  },

  // Authenticated Career Platform Shell
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
      // Shared Authenticated Routes
      {
        path: "/dashboard",
        element: <DashboardPage />,
      },
      {
        path: "/jobs",
        element: <JobDiscoveryPage />,
      },
      {
        path: "/notifications",
        element: <NotificationsPage />,
      },
      {
        path: "/settings",
        element: <SettingsHubPage />,
      },

      // Candidate-Only Route Group
      {
        element: <ProtectedRoute allowedRoles={["CANDIDATE"]} />,
        children: [
          {
            path: "/profile",
            element: <ProfileHubPage />,
            children: [
              {
                index: true,
                element: <Navigate to="/profile/personal" replace />,
              },
              {
                path: "personal",
                element: <PersonalInfoTab />,
              },
              {
                path: "professional",
                element: <ProfessionalSummaryTab />,
              },
              {
                path: "education",
                element: <EducationTab />,
              },
              {
                path: "experience",
                element: <ExperienceTab />,
              },
              {
                path: "projects",
                element: <ProjectsTab />,
              },
              {
                path: "skills",
                element: <SkillsTab />,
              },
              {
                path: "certifications",
                element: <CertificationsTab />,
              },
              {
                path: "achievements",
                element: <AchievementsTab />,
              },
              {
                path: "languages",
                element: <LanguagesTab />,
              },
              {
                path: "resumes",
                element: <ResumesTab />,
              },
              {
                path: "documents",
                element: <DocumentsTab />,
              },
              {
                path: "preferences",
                element: <PreferencesTab />,
              },
              {
                path: "links",
                element: <LinksTab />,
              },
            ],
          },
          // Opportunities
          {
            path: "/opportunities",
            element: <OpportunitiesPage />,
          },
          {
            path: "/opportunities/saved",
            element: <SavedOpportunitiesPage />,
          },
          {
            path: "/opportunities/:id",
            element: <OpportunityDetailsPage />,
          },
          // Applications
          {
            path: "/applications",
            element: <ApplicationsPage />,
          },
          {
            path: "/applications/pipeline",
            element: <PipelineKanbanPage />,
          },
          {
            path: "/applications/followups",
            element: <ApplicationFollowupsPage />,
          },
          {
            path: "/applications/:id",
            element: <ApplicationDetailsPage />,
          },
          // Companies
          {
            path: "/companies",
            element: <CompaniesPage />,
          },
          {
            path: "/companies/:id",
            element: <CompanyDetailsPage />,
          },
          // Interviews
          {
            path: "/interviews",
            element: <InterviewsPage />,
          },
          {
            path: "/interviews/:id",
            element: <InterviewDetailsPage />,
          },
          {
            path: "/interviews/:id/prep",
            element: <InterviewPrepPage />,
          },
          // Tasks & Calendar
          {
            path: "/tasks",
            element: <TasksPage />,
          },
          {
            path: "/calendar",
            element: <CalendarPage />,
          },
          // Network / Contacts
          {
            path: "/network",
            element: <ContactsPage />,
          },
          {
            path: "/network/:id",
            element: <ContactDetailsPage />,
          },
          {
            path: "/contacts",
            element: <Navigate to="/network" replace />,
          },
          {
            path: "/contacts/:id",
            element: <ContactDetailsPage />,
          },
          // Analytics Sub-routes
          {
            path: "/analytics",
            element: <AnalyticsOverviewPage />,
          },
          {
            path: "/analytics/trends",
            element: <AnalyticsTrendsPage />,
          },
          {
            path: "/analytics/pipeline",
            element: <AnalyticsPipelinePage />,
          },
          {
            path: "/analytics/companies",
            element: <AnalyticsCompaniesPage />,
          },
          {
            path: "/analytics/outcomes",
            element: <AnalyticsOutcomesPage />,
          },
          {
            path: "/analytics/time",
            element: <AnalyticsTimePage />,
          },
          // Shortcuts
          {
            path: "/resumes",
            element: <ResumesPage />,
          },
          {
            path: "/documents",
            element: <DocumentsPage />,
          },
        ],
      },

      // Recruiter-Only Route Group
      {
        element: <ProtectedRoute allowedRoles={["HIRER"]} />,
        children: [
          {
            path: "/recruiter/jobs",
            element: <RecruiterJobsPage />,
          },
          {
            path: "/recruiter/jobs/:jobId/applicants",
            element: <JobApplicantsPage />,
          },
          {
            path: "/recruiter/organization",
            element: <OrganizationProfilePage />,
          },
        ],
      },
    ],
      },
    ],
  },

  // 404 Fallback
  {
    path: "*",
    element: (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 text-center px-4">
        <h1 className="text-4xl font-extrabold text-slate-900">404</h1>
        <p className="text-slate-600 mt-2">The page you requested could not be found.</p>
        <a
          href="/dashboard"
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
        >
          Return to Dashboard
        </a>
      </div>
    ),
  },
]);
