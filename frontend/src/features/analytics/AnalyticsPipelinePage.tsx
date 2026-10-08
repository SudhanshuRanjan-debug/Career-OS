/**
 * Analytics Pipeline Page.
 * Stage 9: Analytics & Settings.
 */

import React from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";
import { GitFork, ArrowDown, XCircle, Ban } from "lucide-react";
import { analyticsService } from "@/services/analyticsService";

export const AnalyticsPipelinePage: React.FC = () => {
  const tabs = [
    { name: "Overview", path: "/analytics" },
    { name: "Trends", path: "/analytics/trends" },
    { name: "Pipeline", path: "/analytics/pipeline" },
    { name: "Companies", path: "/analytics/companies" },
    { name: "Outcomes", path: "/analytics/outcomes" },
    { name: "Time Analysis", path: "/analytics/time" },
  ];

  const { data: pipeline, isLoading } = useQuery({
    queryKey: ["analytics-pipeline"],
    queryFn: () => analyticsService.getPipeline(),
    staleTime: 30000,
  });

  const stages = pipeline?.stages || [];
  const totalApps = pipeline?.total_applications ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pipeline Conversion"
        description="Deterministic funnel metrics tracking stage volume and progression through the recruitment lifecycle."
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
        <div className="p-8 text-center text-sm text-slate-500">Loading pipeline funnel...</div>
      ) : totalApps === 0 ? (
        <Card className="p-8 text-center bg-slate-50 border-dashed border-slate-300">
          <GitFork className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No applications in pipeline</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            Add applications to visualize candidate volume and conversion drop-offs.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Funnel Column (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <GitFork className="w-5 h-5 text-blue-600" /> Pipeline Stage Progression Funnel
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {stages.map((st, idx) => {
                  const shareOfTotal = totalApps > 0 ? (st.cumulative_count / totalApps) * 100 : 0;
                  return (
                    <div key={st.stage} className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-800">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px]">
                            {idx + 1}
                          </span>
                          <span>{st.label}</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-600">
                          <span className="font-bold text-slate-900">{st.count} current</span>
                          <span>•</span>
                          <span>{st.cumulative_count} reached ({st.conversion_rate.toFixed(1)}% conversion)</span>
                        </div>
                      </div>
                      <ProgressBar value={shareOfTotal} color="primary" size="md" />
                      {idx < stages.length - 1 && (
                        <div className="flex justify-center py-0.5">
                          <ArrowDown className="w-3.5 h-3.5 text-slate-300" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Terminal & Inactive Stages (1 col) */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Terminal Outcomes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-rose-50/50 rounded-lg border border-rose-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-rose-600" />
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900">Rejected</h4>
                      <span className="text-[11px] text-slate-500">Ended by employer</span>
                    </div>
                  </div>
                  <Badge variant="danger">{pipeline?.rejected_count ?? 0}</Badge>
                </div>

                <div className="p-3 bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Ban className="w-4 h-4 text-slate-500" />
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900">Withdrawn</h4>
                      <span className="text-[11px] text-slate-500">Ended by candidate</span>
                    </div>
                  </div>
                  <Badge variant="neutral">{pipeline?.withdrawn_count ?? 0}</Badge>
                </div>

                <div className="pt-2 text-xs text-slate-500">
                  Total Managed Applications: <span className="font-bold text-slate-800">{totalApps}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
