import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Bookmark,
  Building2,
  MapPin,
  DollarSign,
  ArrowRight,
  Search,
  Filter,
  X,
  Calendar,
  Briefcase,
  AlertCircle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { EmptyState } from "@/components/ui/EmptyState";
import { opportunityService } from "@/services/opportunityService";
import type {
  Opportunity,
  OpportunityCreateInput,
  OpportunityStatus,
  LocationType,
  EmploymentType,
} from "@/types/opportunity.types";

export const OpportunitiesPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [locationTypeFilter, setLocationTypeFilter] = useState<string>("");
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const pageSize = 9;

  // Add Opportunity Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState<OpportunityCreateInput>({
    title: "",
    company_name: "",
    source: "MANUAL",
    source_url: "",
    location: "",
    location_type: null,
    employment_type: null,
    compensation_min: null,
    compensation_max: null,
    compensation_currency: "USD",
    posted_date: null,
    expiry_date: null,
    status: "ACTIVE",
    description: "",
    requirements: "",
    notes: "",
  });

  // Query: Opportunities
  const {
    data: opportunitiesData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: [
      "opportunities",
      { search: searchTerm, status: statusFilter, location_type: locationTypeFilter, employment_type: employmentTypeFilter, page, pageSize },
    ],
    queryFn: () =>
      opportunityService.listOpportunities({
        search: searchTerm || undefined,
        status: statusFilter || undefined,
        location_type: locationTypeFilter || undefined,
        employment_type: employmentTypeFilter || undefined,
        page,
        page_size: pageSize,
      }),
  });

  // Query: Saved Opportunities count
  const { data: savedData } = useQuery({
    queryKey: ["saved-opportunities"],
    queryFn: () => opportunityService.listSavedOpportunities(),
  });

  // Mutation: Create Opportunity
  const createMutation = useMutation({
    mutationFn: (newOpp: OpportunityCreateInput) => opportunityService.createOpportunity(newOpp),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      setIsAddModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail;
      if (typeof msg === "string") {
        setFormError(msg);
      } else if (Array.isArray(msg)) {
        setFormError(msg.map((m: any) => m.msg || "Invalid input").join(", "));
      } else {
        setFormError("Failed to create opportunity. Please check all fields.");
      }
    },
  });

  // Mutation: Save / Bookmark Opportunity
  const saveMutation = useMutation({
    mutationFn: (id: string) => opportunityService.saveOpportunity(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
    },
  });

  // Mutation: Unsave Opportunity
  const unsaveMutation = useMutation({
    mutationFn: (id: string) => opportunityService.unsaveOpportunity(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
    },
  });

  const resetForm = () => {
    setFormData({
      title: "",
      company_name: "",
      source: "MANUAL",
      source_url: "",
      location: "",
      location_type: null,
      employment_type: null,
      compensation_min: null,
      compensation_max: null,
      compensation_currency: "USD",
      posted_date: null,
      expiry_date: null,
      status: "ACTIVE",
      description: "",
      requirements: "",
      notes: "",
    });
    setFormError(null);
  };

  const handleToggleSave = (opp: Opportunity, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (opp.is_saved) {
      unsaveMutation.mutate(opp.id);
    } else {
      saveMutation.mutate(opp.id);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.title.trim()) {
      setFormError("Job title is required.");
      return;
    }

    if (formData.source_url && formData.source_url.trim()) {
      const urlLower = formData.source_url.trim().toLowerCase();
      if (!urlLower.startsWith("http://") && !urlLower.startsWith("https://")) {
        setFormError("External URL must start with http:// or https://");
        return;
      }
    }

    if (
      formData.compensation_min !== null &&
      formData.compensation_max !== null &&
      Number(formData.compensation_min) > Number(formData.compensation_max)
    ) {
      setFormError("Minimum compensation cannot exceed maximum compensation.");
      return;
    }

    if (formData.posted_date && formData.expiry_date && formData.posted_date > formData.expiry_date) {
      setFormError("Posted date cannot be after deadline/expiration date.");
      return;
    }

    createMutation.mutate({
      ...formData,
      title: formData.title.trim(),
      company_name: formData.company_name?.trim() || null,
      source_url: formData.source_url?.trim() || null,
      location: formData.location?.trim() || null,
      description: formData.description?.trim() || null,
      requirements: formData.requirements?.trim() || null,
      notes: formData.notes?.trim() || null,
      compensation_min: formData.compensation_min ? Number(formData.compensation_min) : null,
      compensation_max: formData.compensation_max ? Number(formData.compensation_max) : null,
    });
  };

  const formatCompensation = (min: number | null, max: number | null, curr: string | null) => {
    if (!min && !max) return "Compensation Unspecified";
    const currency = curr || "USD";
    const fmt = (n: number) => `$${Number(n).toLocaleString()}`;
    if (min && max) return `${fmt(min)} - ${fmt(max)} ${currency}`;
    if (min) return `From ${fmt(min)} ${currency}`;
    if (max) return `Up to ${fmt(max)} ${currency}`;
    return "";
  };

  const getStatusBadge = (status: OpportunityStatus) => {
    switch (status) {
      case "ACTIVE":
        return <Badge variant="success">Active</Badge>;
      case "CONSIDERING":
        return <Badge variant="info">Considering</Badge>;
      case "SAVED":
        return <Badge variant="warning">Saved</Badge>;
      case "ARCHIVED":
        return <Badge variant="neutral">Archived</Badge>;
      case "NOT_INTERESTED":
        return <Badge variant="danger">Not Interested</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const clearFilters = () => {
    setSearchTerm("");
    setStatusFilter("");
    setLocationTypeFilter("");
    setEmploymentTypeFilter("");
    setPage(1);
  };

  const hasActiveFilters = Boolean(searchTerm || statusFilter || locationTypeFilter || employmentTypeFilter);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Opportunity Discovery"
        description="Discover, curate, and track career opportunities. Record jobs manually or via clean URLs, organize them in your queue, and prepare for applications."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/opportunities/saved">
              <Button size="sm" variant="outline" leftIcon={<Bookmark className="w-4 h-4" />}>
                Saved Queue {savedData?.total !== undefined && `(${savedData.total})`}
              </Button>
            </Link>
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => {
                resetForm();
                setIsAddModalOpen(true);
              }}
            >
              Add Opportunity
            </Button>
          </div>
        }
      />

      {/* Search and Filters Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Keyword Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by role, company, location, or keywords..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-8 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {searchTerm && (
              <button
                onClick={() => {
                  setSearchTerm("");
                  setPage(1);
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Status Filter */}
          <div className="w-full md:w-44">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="CONSIDERING">Considering</option>
              <option value="SAVED">Saved</option>
              <option value="ARCHIVED">Archived</option>
              <option value="NOT_INTERESTED">Not Interested</option>
            </select>
          </div>

          {/* Location Type Filter */}
          <div className="w-full md:w-44">
            <select
              value={locationTypeFilter}
              onChange={(e) => {
                setLocationTypeFilter(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Work Modes</option>
              <option value="REMOTE">Remote</option>
              <option value="HYBRID">Hybrid</option>
              <option value="ON_SITE">On-Site</option>
            </select>
          </div>

          {/* Employment Type Filter */}
          <div className="w-full md:w-44">
            <select
              value={employmentTypeFilter}
              onChange={(e) => {
                setEmploymentTypeFilter(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="FULL_TIME">Full-Time</option>
              <option value="PART_TIME">Part-Time</option>
              <option value="CONTRACT">Contract</option>
              <option value="INTERNSHIP">Internship</option>
            </select>
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <Button size="sm" variant="ghost" onClick={clearFilters} className="text-slate-500 whitespace-nowrap">
              Clear Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="p-5 space-y-4 animate-pulse">
              <div className="h-5 bg-slate-200 rounded w-3/4" />
              <div className="h-4 bg-slate-100 rounded w-1/2" />
              <div className="space-y-2 pt-2">
                <div className="h-3 bg-slate-100 rounded w-2/3" />
                <div className="h-3 bg-slate-100 rounded w-1/2" />
              </div>
              <div className="pt-4 border-t border-slate-100 flex justify-between">
                <div className="h-4 bg-slate-100 rounded w-1/4" />
                <div className="h-8 bg-slate-200 rounded w-1/3" />
              </div>
            </Card>
          ))}
        </div>
      ) : isError ? (
        <Card className="p-6 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-900">Failed to load opportunities</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {(error as any)?.message || "A network or server error occurred while retrieving opportunities."}
          </p>
          <Button size="sm" variant="outline" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Retry
          </Button>
        </Card>
      ) : opportunitiesData?.items.length === 0 ? (
        <EmptyState
          title={hasActiveFilters ? "No matching opportunities" : "No opportunities yet"}
          description={
            hasActiveFilters
              ? "Try broadening your search query or clearing filter criteria to discover more jobs."
              : "Track your career discovery by adding your first job opportunity manually or via clean URL import."
          }
          action={
            <Button
              size="sm"
              variant="primary"
              onClick={hasActiveFilters ? clearFilters : () => setIsAddModalOpen(true)}
            >
              {hasActiveFilters ? "Clear All Filters" : "Add Opportunity"}
            </Button>
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Opportunities Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {opportunitiesData?.items.map((opp) => (
              <Card
                key={opp.id}
                className="flex flex-col justify-between hover:shadow-md transition-all duration-200 border-slate-200 hover:border-blue-200 group"
              >
                <div className="p-5 space-y-3">
                  {/* Top Row: Title, Company, Status, and Bookmark Toggle */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <Link to={`/opportunities/${opp.id}`}>
                        <h3 className="text-base font-semibold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                          {opp.title}
                        </h3>
                      </Link>
                      <p className="text-xs font-medium text-slate-600 flex items-center gap-1.5 mt-0.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{opp.company_name || "Company Unspecified"}</span>
                      </p>
                    </div>

                    <button
                      onClick={(e) => handleToggleSave(opp, e)}
                      title={opp.is_saved ? "Remove from Saved Queue" : "Save Opportunity"}
                      className={`p-1.5 rounded-lg border transition-colors ${
                        opp.is_saved
                          ? "bg-amber-50 text-amber-600 border-amber-200 hover:bg-amber-100"
                          : "bg-white text-slate-400 border-slate-200 hover:text-amber-500 hover:border-amber-300"
                      }`}
                    >
                      <Bookmark className={`w-4 h-4 ${opp.is_saved ? "fill-current" : ""}`} />
                    </button>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {getStatusBadge(opp.status)}
                    {opp.location_type && (
                      <Badge variant="neutral">
                        {opp.location_type.replace("_", " ")}
                      </Badge>
                    )}
                    {opp.employment_type && (
                      <Badge variant="neutral">
                        {opp.employment_type.replace("_", " ")}
                      </Badge>
                    )}
                  </div>

                  {/* Metadata: Location, Compensation, Source */}
                  <div className="space-y-1.5 text-xs text-slate-500 pt-1">
                    {opp.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{opp.location}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{formatCompensation(opp.compensation_min, opp.compensation_max, opp.compensation_currency)}</span>
                    </div>
                  </div>

                  {/* Description Preview */}
                  {opp.description && (
                    <p className="text-xs text-slate-600 line-clamp-2 pt-1 border-t border-slate-50">
                      {opp.description}
                    </p>
                  )}
                </div>

                {/* Card Footer */}
                <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {opp.posted_date || new Date(opp.created_at).toLocaleDateString()}
                  </span>
                  <Link to={`/opportunities/${opp.id}`}>
                    <Button size="sm" variant="outline" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                      Details
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {opportunitiesData && opportunitiesData.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200">
              <p className="text-xs text-slate-500">
                Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, opportunitiesData.total)} of{" "}
                {opportunitiesData.total} opportunities
              </p>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                >
                  Previous
                </Button>
                <span className="text-xs font-medium text-slate-700 px-2">
                  Page {page} of {opportunitiesData.total_pages}
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= opportunitiesData.total_pages}
                  onClick={() => setPage((p) => Math.min(p + 1, opportunitiesData.total_pages))}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual / Clean URL Opportunity Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Job Opportunity"
        description="Record a job opportunity manually or paste a clean job posting URL."
        maxWidth="lg"
      >
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Input
                label="Job Title *"
                placeholder="e.g. Senior Backend Engineer"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div>
              <Input
                label="Company Name"
                placeholder="e.g. Stripe"
                value={formData.company_name || ""}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              />
            </div>

            <div>
              <Input
                label="Location (City, State / Region)"
                placeholder="e.g. San Francisco, CA"
                value={formData.location || ""}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Work Arrangement</label>
              <select
                value={formData.location_type || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location_type: (e.target.value as LocationType) || null,
                  })
                }
                className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Unspecified</option>
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
                <option value="ON_SITE">On-Site</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Employment Type</label>
              <select
                value={formData.employment_type || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    employment_type: (e.target.value as EmploymentType) || null,
                  })
                }
                className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Unspecified</option>
                <option value="FULL_TIME">Full-Time</option>
                <option value="PART_TIME">Part-Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
              </select>
            </div>

            <div>
              <Input
                label="Min Compensation"
                type="number"
                placeholder="e.g. 150000"
                value={formData.compensation_min ?? ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    compensation_min: e.target.value ? Number(e.target.value) : null,
                  })
                }
              />
            </div>

            <div>
              <Input
                label="Max Compensation"
                type="number"
                placeholder="e.g. 190000"
                value={formData.compensation_max ?? ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    compensation_max: e.target.value ? Number(e.target.value) : null,
                  })
                }
              />
            </div>

            <div className="md:col-span-2">
              <Input
                label="Job Posting URL"
                placeholder="https://careers.company.com/job/..."
                value={formData.source_url || ""}
                onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                helperText="External link to the original job posting. Must use http:// or https://"
              />
            </div>

            <div>
              <Input
                label="Posted Date"
                type="date"
                value={formData.posted_date || ""}
                onChange={(e) => setFormData({ ...formData, posted_date: e.target.value || null })}
              />
            </div>

            <div>
              <Input
                label="Deadline / Expiry Date"
                type="date"
                value={formData.expiry_date || ""}
                onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value || null })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tracking Status</label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    status: e.target.value as OpportunityStatus,
                  })
                }
                className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ACTIVE">Active</option>
                <option value="CONSIDERING">Considering</option>
                <option value="SAVED">Saved</option>
                <option value="ARCHIVED">Archived</option>
                <option value="NOT_INTERESTED">Not Interested</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <textarea
                rows={3}
                placeholder="Overview of the role, responsibilities, and team mission..."
                value={formData.description || ""}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Key Requirements</label>
              <textarea
                rows={3}
                placeholder="Technical requirements, years of experience, qualifications..."
                value={formData.requirements || ""}
                onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Personal Notes</label>
              <textarea
                rows={2}
                placeholder="Referral contacts, follow-up timeline, salary negotiation thoughts..."
                value={formData.notes || ""}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Saving..." : "Save Opportunity"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
