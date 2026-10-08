import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  CalendarCheck,
  CheckSquare,
  Award,
  ArrowUpRight,
  Clock,
  Plus,
  FileText,
  UserCheck,
  Bookmark,
  Activity,
  Building2,
  Users,
  UserPlus,
  Search,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { PageHeader } from "@/components/layout/PageHeader";
import { analyticsService } from "@/services/analyticsService";
import { useAuthStore } from "@/store/authStore";
import { DashboardSummaryResponse } from "@/types/analytics.types";

interface HirerDashboardProps {
  summary?: DashboardSummaryResponse;
  isLoading: boolean;
}

const HirerDashboard: React.FC<HirerDashboardProps> = ({ summary, isLoading }) => {
  const pipeline = summary?.pipeline_counts || {};

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <PageHeader
        title="Hirer Command Center"
        description="Manage your hiring pipeline, active job postings, and applicant tracking."
        actions={
          <div className="flex items-center gap-2">
            <Link to="/recruiter/jobs">
              <Button size="sm" variant="outline" leftIcon={<Briefcase className="w-4 h-4" />}>
                Manage Postings
              </Button>
            </Link>
            <Link to="/recruiter/jobs/new">
              <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
                Post a Job
              </Button>
            </Link>
          </div>
        }
      />

      {/* Recruiter High-Level KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Active Job Postings</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.active_jobs_posted ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Briefcase className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-500 font-medium">
            <span>{summary?.total_jobs_posted ?? 0} total postings created</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Total Applicants</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.total_applicants ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-500 font-medium">
            <Link to="/recruiter/jobs" className="text-purple-600 hover:underline">
              View candidates →
            </Link>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">New Applicants This Week</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.new_applicants_this_week ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600">
              <UserPlus className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-emerald-600 font-medium">
            <span>Fresh candidate inquiries in last 7 days</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">In Interview Pipeline</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.total_interviews ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-500 font-medium">
            <span>Active candidates being evaluated</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Offers Extended</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.total_offers ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-amber-600 font-medium">
            <span>Offers currently in consideration</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Hires / Accepted</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.total_hires ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-green-50 text-green-600">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-green-600 font-medium">
            <span>Successful talent placements</span>
          </div>
        </Card>
      </div>

      {/* Main Grid: Pipeline Breakdown & Quick Shortcuts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recruiter Pipeline Stage Summary (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Applicant Pipeline by Stage</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Aggregate candidate counts across all your job postings</p>
              </div>
              <Link to="/recruiter/jobs" className="text-xs text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1">
                View All Postings <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-xs text-slate-500 font-medium">Applied</span>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {isLoading ? "-" : pipeline["APPLIED"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-100">
                  <span className="text-xs text-blue-700 font-medium">Screening</span>
                  <p className="text-xl font-bold text-blue-900 mt-1">
                    {isLoading ? "-" : (pipeline["PHONE_SCREEN"] ?? 0) + (pipeline["ASSESSMENT"] ?? 0)}
                  </p>
                </div>
                <div className="p-3 bg-purple-50/50 rounded-lg border border-purple-100">
                  <span className="text-xs text-purple-700 font-medium">Interview</span>
                  <p className="text-xl font-bold text-purple-900 mt-1">
                    {isLoading ? "-" : pipeline["INTERVIEW"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-amber-50/50 rounded-lg border border-amber-100">
                  <span className="text-xs text-amber-700 font-medium">Offer</span>
                  <p className="text-xl font-bold text-amber-900 mt-1">
                    {isLoading ? "-" : pipeline["OFFER"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
                  <span className="text-xs text-emerald-700 font-medium">Hired</span>
                  <p className="text-xl font-bold text-emerald-900 mt-1">
                    {isLoading ? "-" : pipeline["ACCEPTED"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-slate-100 rounded-lg border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Archived</span>
                  <p className="text-xl font-bold text-slate-700 mt-1">
                    {isLoading ? "-" : (pipeline["REJECTED"] ?? 0) + (pipeline["WITHDRAWN"] ?? 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Navigation / Recruiter Shortcuts */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recruiter Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Link
                  to="/recruiter/jobs/new"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Plus className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-semibold text-slate-800">Create Job Posting</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </Link>
                <Link
                  to="/recruiter/jobs"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-purple-600" />
                    <span className="text-xs font-semibold text-slate-800">Manage Job Postings</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </Link>
                <Link
                  to="/recruiter/organization"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-semibold text-slate-800">Company Profile</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </Link>
                <Link
                  to="/jobs"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Search className="w-4 h-4 text-slate-600" />
                    <span className="text-xs font-semibold text-slate-800">Public Job Board</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { data: summary, isLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => analyticsService.getDashboardSummary(),
    staleTime: 30000,
  });

  if (user?.role === "HIRER") {
    return <HirerDashboard summary={summary} isLoading={isLoading} />;
  }

  const pipeline = summary?.pipeline_counts || {};
  const completeness = summary?.profile_completeness ?? 0;

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <PageHeader
        title="Career Command Center"
        description="Your unified personal operating system for opportunities, applications, and interviews."
        actions={
          <div className="flex items-center gap-2">
            <Link to="/opportunities">
              <Button size="sm" variant="outline" leftIcon={<Plus className="w-4 h-4" />}>
                Add Opportunity
              </Button>
            </Link>
            <Link to="/applications">
              <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
                New Application
              </Button>
            </Link>
          </div>
        }
      />

      {/* Profile Completeness Alert & Progress */}
      <Card className="bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-white border-blue-100">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-blue-900">Profile Completeness</span>
              <Badge variant={completeness >= 80 ? "success" : "info"}>
                {completeness}% Complete
              </Badge>
            </div>
            <p className="text-xs text-slate-600">
              {completeness >= 80
                ? "Your career profile and candidate preferences are well established."
                : "Complete your Job Preferences, Skills, and Resumes to unlock targeted opportunity discovery."}
            </p>
            <div className="pt-2 w-full max-w-md">
              <ProgressBar value={completeness} size="md" color="blue" showPercent={false} />
            </div>
          </div>
          <Link to="/profile/preferences">
            <Button size="sm" variant="outline" className="bg-white">
              {completeness >= 80 ? "Edit Preferences" : "Complete Preferences"}
            </Button>
          </Link>
        </div>
      </Card>

      {/* High-Level KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Active Applications</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.active_applications ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Briefcase className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-500 font-medium">
            <Link to="/applications" className="text-blue-600 hover:underline">
              View pipeline →
            </Link>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Upcoming Interviews</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.upcoming_interviews ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-500">
            <Link to="/interviews" className="text-purple-600 hover:underline">
              Manage schedule →
            </Link>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Tasks Due Today</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.tasks_due_today ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600">
              <CheckSquare className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-amber-600 font-medium">
            <span>{summary?.pending_followups ?? 0} follow-ups pending</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Offers in Review</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? "..." : summary?.offers_in_review ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-emerald-600 font-medium">
            <span>{summary?.saved_opportunities_count ?? 0} saved leads</span>
          </div>
        </Card>
      </div>

      {/* Main Grid: Application Pipeline & Upcoming Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Stage Summary (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recruitment Pipeline</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Current distribution of applications by stage</p>
              </div>
              <Link to="/applications/pipeline" className="text-xs text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1">
                View Kanban <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-xs text-slate-500 font-medium">Applied</span>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {isLoading ? "-" : pipeline["APPLIED"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-100">
                  <span className="text-xs text-blue-700 font-medium">Screening</span>
                  <p className="text-xl font-bold text-blue-900 mt-1">
                    {isLoading ? "-" : (pipeline["PHONE_SCREEN"] ?? 0) + (pipeline["ASSESSMENT"] ?? 0)}
                  </p>
                </div>
                <div className="p-3 bg-purple-50/50 rounded-lg border border-purple-100">
                  <span className="text-xs text-purple-700 font-medium">Interview</span>
                  <p className="text-xl font-bold text-purple-900 mt-1">
                    {isLoading ? "-" : pipeline["INTERVIEW"] ?? 0}
                  </p>
                </div>
                <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
                  <span className="text-xs text-emerald-700 font-medium">Offer</span>
                  <p className="text-xl font-bold text-emerald-900 mt-1">
                    {isLoading ? "-" : (pipeline["OFFER"] ?? 0) + (pipeline["ACCEPTED"] ?? 0)}
                  </p>
                </div>
                <div className="p-3 bg-slate-100 rounded-lg border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Archived</span>
                  <p className="text-xl font-bold text-slate-700 mt-1">
                    {isLoading ? "-" : (pipeline["REJECTED"] ?? 0) + (pipeline["WITHDRAWN"] ?? 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity Timeline Preview */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Audit log of your job search touchpoints</p>
              </div>
              <span className="text-xs text-slate-400">Live Timeline</span>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="py-4 text-center text-xs text-slate-400">Loading activity...</div>
              ) : summary?.recent_activity && summary.recent_activity.length > 0 ? (
                <div className="space-y-4">
                  {summary.recent_activity.map((item, idx) => (
                    <div key={item.id || idx} className="flex items-start gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-slate-900">
                          {item.title}:{" "}
                          <span className="font-normal text-slate-600">{item.description}</span>
                        </p>
                        <span className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {new Date(item.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-slate-500">
                  No activity recorded yet. Start by tracking an opportunity or submitting an application!
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Widgets (1 col): Upcoming & Shortcuts */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Quick Navigation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Link
                  to="/analytics"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-semibold text-slate-800">Career Analytics</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </Link>
                <Link
                  to="/opportunities"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Bookmark className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-semibold text-slate-800">Saved Opportunities</span>
                  </div>
                  <span className="text-xs font-bold text-slate-600">
                    {summary?.saved_opportunities_count ?? 0}
                  </span>
                </Link>
                <Link
                  to="/interviews"
                  className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <CalendarCheck className="w-4 h-4 text-purple-600" />
                    <span className="text-xs font-semibold text-slate-800">Interview Sessions</span>
                  </div>
                  <span className="text-xs font-bold text-slate-600">
                    {summary?.upcoming_interviews ?? 0}
                  </span>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions Shortcuts */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                <Link
                  to="/applications"
                  className="p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-center transition-colors"
                >
                  <Briefcase className="w-4 h-4 mx-auto text-blue-600 mb-1" />
                  <span className="text-xs font-medium text-slate-700 block">Add App</span>
                </Link>
                <Link
                  to="/profile/resumes"
                  className="p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-center transition-colors"
                >
                  <FileText className="w-4 h-4 mx-auto text-blue-600 mb-1" />
                  <span className="text-xs font-medium text-slate-700 block">Upload CV</span>
                </Link>
                <Link
                  to="/interviews"
                  className="p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-center transition-colors"
                >
                  <CalendarCheck className="w-4 h-4 mx-auto text-blue-600 mb-1" />
                  <span className="text-xs font-medium text-slate-700 block">Schedule</span>
                </Link>
                <Link
                  to="/network"
                  className="p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-center transition-colors"
                >
                  <UserCheck className="w-4 h-4 mx-auto text-blue-600 mb-1" />
                  <span className="text-xs font-medium text-slate-700 block">Add Contact</span>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
