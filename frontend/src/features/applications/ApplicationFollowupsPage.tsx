import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  Clock,
  CheckCircle,
  ArrowLeft,
  Building2,
  AlertCircle,
  Trash2,
  Calendar,
} from "lucide-react";
import { applicationService } from "@/services/applicationService";
import type { ApplicationFollowupWithApp } from "@/types/application.types";

export const ApplicationFollowupsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"ALL" | "PENDING" | "COMPLETED">("ALL");

  const isCompletedParam =
    filter === "PENDING" ? false : filter === "COMPLETED" ? true : undefined;

  const { data: followups, isLoading, isError, refetch } = useQuery({
    queryKey: ["global-followups", filter],
    queryFn: () => applicationService.getGlobalFollowups(isCompletedParam),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ appId, folId, isCompleted }: { appId: string; folId: string; isCompleted: boolean }) =>
      applicationService.updateFollowup(appId, folId, { is_completed: isCompleted }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["global-followups"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ appId, folId }: { appId: string; folId: string }) =>
      applicationService.deleteFollowup(appId, folId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["global-followups"] });
    },
  });

  const items = followups || [];

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/applications" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Applications
        </Link>
      </div>

      <PageHeader
        title="Application Follow-ups"
        subtitle="Track upcoming recruiter communications, status check-ins, and deadlines across all applications."
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter("ALL")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "ALL"
              ? "bg-blue-50 text-blue-700 border border-blue-200"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          All Reminders
        </button>
        <button
          onClick={() => setFilter("PENDING")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "PENDING"
              ? "bg-blue-50 text-blue-700 border border-blue-200"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Pending
        </button>
        <button
          onClick={() => setFilter("COMPLETED")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
            filter === "COMPLETED"
              ? "bg-blue-50 text-blue-700 border border-blue-200"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Completed
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4 animate-pulse">
              <div className="h-5 bg-slate-200 rounded w-1/3 mb-2" />
              <div className="h-4 bg-slate-100 rounded w-1/2" />
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <Card className="p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-800">Failed to load follow-ups</h3>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && items.length === 0 && (
        <Card className="p-12 text-center space-y-3">
          <Clock className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-semibold text-slate-800">No follow-ups found</h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            {filter === "PENDING"
              ? "You have completed all your scheduled follow-ups!"
              : "Schedule follow-up reminders directly from any application details page."}
          </p>
        </Card>
      )}

      {/* Follow-ups List */}
      {!isLoading && !isError && items.length > 0 && (
        <div className="space-y-3">
          {items.map((fol) => (
            <Card key={fol.id} className="p-4 hover:border-slate-300 transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={fol.is_completed}
                    onChange={(e) =>
                      toggleMutation.mutate({
                        appId: fol.application_id,
                        folId: fol.id,
                        isCompleted: e.target.checked,
                      })
                    }
                    className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mt-1 cursor-pointer"
                  />
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/applications/${fol.application_id}`}
                        className="font-semibold text-sm text-slate-900 hover:text-blue-600 transition-colors"
                      >
                        {fol.company_name}
                      </Link>
                      <span className="text-xs text-slate-400">• {fol.job_title}</span>
                      {fol.current_stage && (
                        <Badge variant="neutral">{fol.current_stage.replace("_", " ")}</Badge>
                      )}
                      {fol.due_date && (
                        <Badge variant={fol.is_completed ? "success" : "warning"}>
                          Due {fol.due_date}
                        </Badge>
                      )}
                    </div>
                    <p className={`text-sm ${fol.is_completed ? "line-through text-slate-400" : "text-slate-700"}`}>
                      {fol.note || "Scheduled Follow-up"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Link to={`/applications/${fol.application_id}`}>
                    <Button variant="outline" size="sm">
                      View Application
                    </Button>
                  </Link>
                  <button
                    onClick={() =>
                      deleteMutation.mutate({
                        appId: fol.application_id,
                        folId: fol.id,
                      })
                    }
                    className="p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                    title="Delete reminder"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
