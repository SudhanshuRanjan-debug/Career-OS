/**
 * Analytics Outcomes Page.
 * Stage 9: Analytics & Settings.
 */

import React from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Award, CheckCircle, XCircle, Ban, PieChart } from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

export const AnalyticsOutcomesPage: React.FC = () => {
  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: outcomeData, isLoading } = useQuery({
    queryKey: ["analytics-outcomes"],
    queryFn: () => analyticsService.getOutcomes(),
    staleTime: 30000,
  });

  const breakdown = outcomeData?.breakdown || [];
  const total = breakdown.reduce((acc, curr) => acc + curr.count, 0);

  const getBadgeVariant = (outcome: string): "default" | "success" | "warning" | "danger" | "info" | "neutral" => {
    switch (outcome) {
      case "ACCEPTED":
        return "success";
      case "OFFER":
        return "info";
      case "REJECTED":
        return "danger";
      case "WITHDRAWN":
        return "neutral";
      default:
        return "default";
    }
  };

  const getProgressColor = (outcome: string): "blue" | "emerald" | "amber" | "rose" | "primary" | "success" | "warning" | "danger" => {
    switch (outcome) {
      case "ACCEPTED":
        return "success";
      case "OFFER":
        return "emerald";
      case "REJECTED":
        return "danger";
      case "WITHDRAWN":
        return "warning";
      default:
        return "blue";
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Outcomes"
        description="Deterministic historical outcome distribution across active pipelines, offers, rejections, and candidate withdrawals."
      />

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
        <div className="p-8 text-center text-sm text-slate-500">Loading outcome statistics...</div>
      ) : total === 0 ? (
        <Card className="p-8 text-center bg-slate-50 border-dashed border-slate-300">
          <PieChart className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No application outcomes yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            Track applications to view outcome percentages and terminal distribution.
          </p>
        </Card>
      ) : (
        <>
          {/* Outcome Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {breakdown.map((o) => (
              <Card key={o.outcome} className="p-4">
                <span className="text-xs font-medium text-slate-500">{o.label}</span>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-2xl font-bold text-slate-900">{o.count}</span>
                  <Badge variant={getBadgeVariant(o.outcome)}>{o.percentage.toFixed(1)}%</Badge>
                </div>
              </Card>
            ))}
          </div>

          {/* Outcome Distribution Bars */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <PieChart className="w-5 h-5 text-blue-600" /> Relative Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {breakdown.map((o) => (
                <div key={o.outcome} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>{o.label}</span>
                    <span>
                      {o.count} applications ({o.percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <ProgressBar
                    value={o.percentage}
                    color={getProgressColor(o.outcome)}
                    size="sm"
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
