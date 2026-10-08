/**
 * Analytics Time & Velocity Page.
 * Stage 9: Analytics & Settings.
 */

import React from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Clock, Timer, CheckCircle, Hourglass } from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

export const AnalyticsTimePage: React.FC = () => {
  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: timeData, isLoading } = useQuery({
    queryKey: ["analytics-time"],
    queryFn: () => analyticsService.getTime(),
    staleTime: 30000,
  });

  const renderDays = (val?: number | null) => {
    if (val === null || val === undefined) {
      return <span className="text-xs text-slate-400 font-normal">No sufficient data yet</span>;
    }
    return <span>{val.toFixed(1)} days</span>;
  };

  const metrics = [
    {
      title: "Time to First Response",
      desc: "From application submission to first stage movement or interview schedule",
      value: timeData?.avg_days_to_first_response,
      icon: Clock,
    },
    {
      title: "Time to First Interview",
      desc: "From submission to scheduled first interview round",
      value: timeData?.avg_days_to_interview,
      icon: Timer,
    },
    {
      title: "Time to Offer",
      desc: "From submission to official offer extension",
      value: timeData?.avg_days_to_offer,
      icon: CheckCircle,
    },
    {
      title: "Overall Lifecycle Duration",
      desc: "Average lifespan from application creation to terminal decision",
      value: timeData?.avg_days_overall_lifecycle,
      icon: Hourglass,
    },
  ];

  const stages = timeData?.stage_durations || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Time & Velocity Analysis"
        description="Deterministic duration tracking from application submission across interview rounds, offers, and decisions."
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
        <div className="p-8 text-center text-sm text-slate-500">Loading velocity metrics...</div>
      ) : (
        <>
          {/* Velocity KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.map((m) => {
              const Icon = m.icon;
              return (
                <Card key={m.title} className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700">{m.title}</span>
                    <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="mt-2 text-xl font-bold text-slate-900">
                    {renderDays(m.value)}
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500 leading-snug">{m.desc}</p>
                </Card>
              );
            })}
          </div>

          {/* Stage Duration Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" /> Stage Duration Benchmarks
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stages.length === 0 ? (
                <div className="p-8 text-center text-sm text-slate-500">
                  No sufficient stage duration data recorded yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {stages.map((item) => (
                    <div
                      key={item.stage}
                      className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="font-semibold text-slate-900 text-sm">{item.label}</h4>
                        <span className="text-xs text-slate-500">Recruitment stage</span>
                      </div>
                      <div className="text-right font-bold text-slate-800 text-sm">
                        {item.avg_days.toFixed(1)} days avg
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
