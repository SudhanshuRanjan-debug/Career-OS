/**
 * Analytics Trends Page.
 * Stage 9: Analytics & Settings.
 */

import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { TrendingUp, Calendar, Briefcase, Award } from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

const RANGES = [
  { label: "7 Days", value: "7d" },
  { label: "30 Days", value: "30d" },
  { label: "90 Days", value: "90d" },
  { label: "6 Months", value: "6m" },
  { label: "1 Year", value: "1y" },
  { label: "All Time", value: "all" },
];

export const AnalyticsTrendsPage: React.FC = () => {
  const [selectedRange, setSelectedRange] = useState("30d");

  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: trends, isLoading } = useQuery({
    queryKey: ["analytics-trends", selectedRange],
    queryFn: () => analyticsService.getTrends(selectedRange),
    staleTime: 30000,
  });

  const points = trends?.points || [];
  const maxCount = Math.max(...points.map((p) => Math.max(p.count, p.interviews_count, p.offers_count)), 1);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Trends"
        description="Deterministic time-based tracking of application submissions, interview progression, and offer velocity."
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

      {/* Date Range Selector */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setSelectedRange(r.value)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                selectedRange === r.value
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-500 font-medium">
          Total in Period:{" "}
          <span className="font-bold text-slate-900">{trends?.total_in_period ?? 0}</span> applications
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" /> Periodic Velocity & Milestones
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="p-8 text-center text-sm text-slate-500">Loading trend points...</div>
          ) : points.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No application submissions recorded in this time range.
            </div>
          ) : (
            <div className="space-y-4">
              {points.map((p) => {
                const appPct = (p.count / maxCount) * 100;
                const intPct = (p.interviews_count / maxCount) * 100;

                return (
                  <div
                    key={p.date}
                    className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        <span className="text-sm font-semibold text-slate-900">{p.label}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          {p.count} Applied
                        </span>
                        <span className="font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                          {p.interviews_count} Interviews
                        </span>
                        {p.offers_count > 0 && (
                          <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                            {p.offers_count} Offers
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Bar visualization */}
                    <div className="space-y-1 pt-1">
                      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden flex">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${Math.max(appPct, 4)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
