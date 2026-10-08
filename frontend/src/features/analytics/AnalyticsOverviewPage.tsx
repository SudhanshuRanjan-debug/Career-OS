/**
 * Analytics Overview Page.
 * Stage 9: Analytics & Settings.
 */

import React from "react";
import { Link, NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Button } from "@/components/ui/Button";
import {
  BarChart3,
  TrendingUp,
  PieChart,
  Building2,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Briefcase,
  Award,
  XCircle,
  HelpCircle,
  Plus,
} from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

export const AnalyticsOverviewPage: React.FC = () => {
  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: overview, isLoading } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsService.getOverview(),
    staleTime: 30000,
  });

  const hasData = (overview?.total_applications ?? 0) > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Career Analytics"
        description="Deterministic, read-only insights into your application conversion rates, pipeline velocity, and outcomes."
      />

      {/* Analytics Sub-nav */}
      <div className="flex items-center gap-6 border-b border-slate-200 overflow-x-auto pb-1">
        {tabs.map((tab) => (
          <NavLink
            key={tab.name}
            to={tab.path}
            end={tab.path === "/analytics"}
            className={({ isActive }) =>
              `pb-3 text-sm font-semibold whitespace-nowrap transition-colors border-b-2 ${
                isActive
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`
            }
          >
            {tab.name}
          </NavLink>
        ))}
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-sm text-slate-500">
          Loading analytics metrics...
        </div>
      ) : !hasData ? (
        <Card className="p-8 text-center bg-slate-50 border-dashed border-slate-300">
          <Briefcase className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No application data yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
            Deterministic career metrics are calculated directly from your real application submissions, stage progression, and interview logs.
          </p>
          <Link to="/applications">
            <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
              Create First Application
            </Button>
          </Link>
        </Card>
      ) : (
        <>
          {/* KPI High-Level Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Total Applications</span>
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <Briefcase className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900">
                  {overview?.total_applications ?? 0}
                </span>
                <span className="text-xs text-slate-500 ml-2">
                  ({overview?.active_applications ?? 0} active)
                </span>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Response Rate</span>
                <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900">
                  {(overview?.response_rate ?? 0).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-400 ml-2">Progressed past applied</span>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Interview Rate</span>
                <div className="p-2 rounded-lg bg-purple-50 text-purple-600">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900">
                  {(overview?.interview_rate ?? 0).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-400 ml-2">
                  {overview?.interviews_scheduled ?? 0} sessions
                </span>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Offer Rate</span>
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                  <Award className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900">
                  {(overview?.offer_rate ?? 0).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-400 ml-2">
                  {overview?.offers_received ?? 0} offers received
                </span>
              </div>
            </Card>
          </div>

          {/* Breakdown Grids */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Conversion Funnel Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Key Conversion Milestones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>Application to Response</span>
                    <span>{(overview?.response_rate ?? 0).toFixed(1)}%</span>
                  </div>
                  <ProgressBar value={overview?.response_rate ?? 0} color="primary" size="sm" />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>Application to Interview</span>
                    <span>{(overview?.interview_rate ?? 0).toFixed(1)}%</span>
                  </div>
                  <ProgressBar value={overview?.interview_rate ?? 0} color="blue" size="sm" />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>Application to Offer</span>
                    <span>{(overview?.offer_rate ?? 0).toFixed(1)}%</span>
                  </div>
                  <ProgressBar value={overview?.offer_rate ?? 0} color="emerald" size="sm" />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>Offer Acceptance Rate</span>
                    <span>{(overview?.acceptance_rate ?? 0).toFixed(1)}%</span>
                  </div>
                  <ProgressBar value={overview?.acceptance_rate ?? 0} color="success" size="sm" />
                </div>
              </CardContent>
            </Card>

            {/* Application Pipeline Status Snapshot */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Application Lifecycle Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                    <span className="text-sm font-medium text-slate-800">Active In Consideration</span>
                  </div>
                  <Badge variant="info">{overview?.active_applications ?? 0}</Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    <span className="text-sm font-medium text-slate-800">Accepted Offers</span>
                  </div>
                  <Badge variant="success">{overview?.accepted_offers ?? 0}</Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                    <span className="text-sm font-medium text-slate-800">Rejected Applications</span>
                  </div>
                  <Badge variant="danger">{overview?.rejected_applications ?? 0}</Badge>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                    <span className="text-sm font-medium text-slate-800">Withdrawn Applications</span>
                  </div>
                  <Badge variant="neutral">{overview?.withdrawn_applications ?? 0}</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};
