import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  List,
  Plus,
  Building2,
  MapPin,
  HeartPulse,
  ChevronRight,
  MoveRight,
  AlertCircle,
  Clock,
} from "lucide-react";
import { applicationService } from "@/services/applicationService";
import type { ApplicationStage, HealthStatus } from "@/types/application.types";

const ALL_STAGES: { stage: ApplicationStage; label: string }[] = [
  { stage: "APPLIED", label: "Applied" },
  { stage: "PHONE_SCREEN", label: "Phone Screen" },
  { stage: "ASSESSMENT", label: "Assessment" },
  { stage: "INTERVIEW", label: "Interview" },
  { stage: "OFFER", label: "Offer" },
  { stage: "ACCEPTED", label: "Accepted" },
  { stage: "REJECTED", label: "Rejected" },
  { stage: "WITHDRAWN", label: "Withdrawn" },
];

export const PipelineKanbanPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [movingAppId, setMovingAppId] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["application-pipeline"],
    queryFn: () => applicationService.getPipeline(),
  });

  const stageMutation = useMutation({
    mutationFn: ({ id, toStage }: { id: string; toStage: string }) =>
      applicationService.transitionStage(id, toStage, `Moved via Kanban to ${toStage}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      setMovingAppId(null);
    },
  });

  const getHealthBadge = (health?: { score: number; status: HealthStatus } | null) => {
    if (!health) return null;
    const { score, status } = health;
    let colorClass = "bg-slate-100 text-slate-700 border-slate-200";
    if (status === "EXCELLENT") colorClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
    else if (status === "GOOD") colorClass = "bg-blue-50 text-blue-700 border-blue-200";
    else if (status === "NEEDS_ATTENTION") colorClass = "bg-amber-50 text-amber-700 border-amber-200";
    else if (status === "POOR") colorClass = "bg-red-50 text-red-700 border-red-200";

    return (
      <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${colorClass}`}>
        <HeartPulse className="w-3 h-3" />
        {score}%
      </span>
    );
  };

  const columns = data?.columns || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Pipeline"
        subtitle="Visual pipeline tracking for all your active career opportunities."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/applications">
              <Button variant="outline">
                <List className="w-4 h-4 mr-1.5" /> List View
              </Button>
            </Link>
            <Link to="/applications/followups">
              <Button variant="outline">
                <Clock className="w-4 h-4 mr-1.5" /> Follow-ups
              </Button>
            </Link>
          </div>
        }
      />

      {/* Loading State */}
      {isLoading && (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="w-72 flex-shrink-0 bg-slate-50 border border-slate-200 rounded-xl p-3 h-96 animate-pulse"
            >
              <div className="h-5 bg-slate-200 rounded w-1/2 mb-4" />
              <div className="space-y-3">
                <div className="h-20 bg-slate-200/60 rounded" />
                <div className="h-20 bg-slate-200/60 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <Card className="p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-800">Failed to load pipeline</h3>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      )}

      {/* Kanban Board */}
      {!isLoading && !isError && (
        <div className="flex gap-4 overflow-x-auto pb-6 pt-1">
          {columns.map((column) => (
            <div
              key={column.stage}
              className="w-72 flex-shrink-0 bg-slate-50/90 border border-slate-200 rounded-xl p-3 flex flex-col max-h-[calc(100vh-210px)] shadow-sm"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-200 mb-3">
                <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-700 truncate">
                  {column.name}
                </h4>
                <Badge variant={column.count > 0 ? "info" : "neutral"}>{column.count}</Badge>
              </div>

              {/* Items Container */}
              <div className="space-y-3 overflow-y-auto flex-1 pr-1">
                {column.items.map((item) => (
                  <Card
                    key={item.id}
                    className="p-3.5 hover:shadow-md hover:border-blue-300 transition-all bg-white relative group"
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <Link
                          to={`/applications/${item.id}`}
                          className="font-semibold text-sm text-slate-900 leading-snug hover:text-blue-600 transition-colors"
                        >
                          {item.job_title}
                        </Link>
                        {getHealthBadge(item.health)}
                      </div>

                      <div className="flex items-center gap-1.5 text-xs text-slate-600">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span className="truncate">{item.company_name}</span>
                      </div>

                      {item.job_location && (
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                          <MapPin className="w-3 h-3 text-slate-400 flex-shrink-0" />
                          <span className="truncate">{item.job_location}</span>
                        </div>
                      )}

                      {/* Stage Progression Action */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400">
                          Move to:
                        </span>
                        <select
                          aria-label="Move application to stage"
                          value={item.current_stage}
                          onChange={(e) =>
                            stageMutation.mutate({ id: item.id, toStage: e.target.value })
                          }
                          disabled={stageMutation.isPending}
                          className="text-[11px] font-medium border border-slate-200 rounded px-1.5 py-0.5 bg-slate-50 text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                        >
                          {ALL_STAGES.map((st) => (
                            <option key={st.stage} value={st.stage}>
                              {st.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </Card>
                ))}

                {column.items.length === 0 && (
                  <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-lg">
                    No applications
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
