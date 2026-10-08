import React from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  MapPin,
  DollarSign,
  ArrowRight,
  BookmarkX,
  Calendar,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { opportunityService } from "@/services/opportunityService";

export const SavedOpportunitiesPage: React.FC = () => {
  const queryClient = useQueryClient();

  const {
    data: savedData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["saved-opportunities"],
    queryFn: () => opportunityService.listSavedOpportunities(),
  });

  const unsaveMutation = useMutation({
    mutationFn: (opportunityId: string) => opportunityService.unsaveOpportunity(opportunityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });

  const formatCompensation = (min: number | null | undefined, max: number | null | undefined, curr: string | null | undefined) => {
    if (!min && !max) return "Compensation Unspecified";
    const currency = curr || "USD";
    const fmt = (n: number) => `$${Number(n).toLocaleString()}`;
    if (min && max) return `${fmt(min)} - ${fmt(max)} ${currency}`;
    if (min) return `From ${fmt(min)} ${currency}`;
    if (max) return `Up to ${fmt(max)} ${currency}`;
    return "";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Saved Opportunities Queue"
        description="Review bookmarked job opportunities you are curating and considering before applying."
        actions={
          <Link to="/opportunities">
            <Button size="sm" variant="outline" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to Opportunities
            </Button>
          </Link>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-5 space-y-4 animate-pulse">
              <div className="h-5 bg-slate-200 rounded w-3/4" />
              <div className="h-4 bg-slate-100 rounded w-1/2" />
              <div className="space-y-2 pt-2">
                <div className="h-3 bg-slate-100 rounded w-2/3" />
                <div className="h-3 bg-slate-100 rounded w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : isError ? (
        <Card className="p-6 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-900">Failed to load saved opportunities</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {(error as any)?.message || "A network or server error occurred."}
          </p>
          <Button size="sm" variant="outline" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Retry
          </Button>
        </Card>
      ) : !savedData || savedData.items.length === 0 ? (
        <EmptyState
          title="No saved opportunities"
          description="You haven't bookmarked any opportunities yet. Browse discovered opportunities and save roles you want to evaluate."
          action={
            <Link to="/opportunities">
              <Button size="sm" variant="primary">
                Browse Opportunities
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {savedData.items.map((saved) => {
            const opp = saved.opportunity;
            if (!opp) return null;

            return (
              <Card
                key={saved.id}
                className="flex flex-col justify-between hover:shadow-md transition-all duration-200 border-slate-200 hover:border-blue-200"
              >
                <div className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <Link to={`/opportunities/${opp.id}`}>
                        <h3 className="text-base font-semibold text-slate-900 hover:text-blue-600 transition-colors truncate">
                          {opp.title}
                        </h3>
                      </Link>
                      <p className="text-xs font-medium text-slate-600 flex items-center gap-1.5 mt-0.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{opp.company_name || "Company Unspecified"}</span>
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Badge variant="warning">Saved</Badge>
                      {opp.location_type && (
                        <Badge variant="neutral">
                          {opp.location_type.replace("_", " ")}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-500">
                    {opp.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{opp.location}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{formatCompensation(opp.compensation_min, opp.compensation_max, opp.compensation_currency)}</span>
                    </div>
                  </div>

                  {saved.notes && (
                    <div className="p-2.5 bg-amber-50/70 border border-amber-200/60 rounded-lg text-xs text-amber-900">
                      <span className="font-semibold">Saved Note: </span>
                      {saved.notes}
                    </div>
                  )}
                </div>

                <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Saved {new Date(saved.saved_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => unsaveMutation.mutate(opp.id)}
                      disabled={unsaveMutation.isPending}
                      className="text-slate-500 hover:text-red-600 hover:border-red-200"
                      leftIcon={<BookmarkX className="w-3.5 h-3.5" />}
                    >
                      Unsave
                    </Button>
                    <Link to={`/opportunities/${opp.id}`}>
                      <Button size="sm" variant="primary" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                        Details
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
