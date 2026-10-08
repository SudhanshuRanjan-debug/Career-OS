import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import {
  Briefcase,
  Plus,
  Search,
  Filter,
  Columns,
  Clock,
  ChevronRight,
  HeartPulse,
  Building2,
  MapPin,
  Calendar,
  AlertCircle,
  FileCheck,
  DollarSign,
  Users2,
} from "lucide-react";
import { applicationService, ApplicationFilterParams } from "@/services/applicationService";
import { contactService } from "@/services/contactService";
import type {
  Application,
  ApplicationStage,
  ApplicationStatus,
  ApplicationPriority,
  ApplicationCreateInput,
  HealthStatus,
} from "@/types/application.types";

export const ApplicationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selectedStage, setSelectedStage] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Form state for creating an application
  const [formData, setFormData] = useState<ApplicationCreateInput>({
    job_title: "",
    company_name: "",
    job_location: "",
    job_location_type: "REMOTE",
    employment_type: "FULL_TIME",
    compensation_min: null,
    compensation_max: null,
    source: "MANUAL",
    status: "ACTIVE",
    current_stage: "APPLIED",
    applied_date: new Date().toISOString().split("T")[0],
    priority: "MEDIUM",
    contact_id: null,
    initial_notes: "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  // Query contacts for linking
  const { data: contactsData } = useQuery({
    queryKey: ["contacts-selector"],
    queryFn: () => contactService.listContacts({ page_size: 100 }),
    enabled: isAddModalOpen,
  });

  // Query parameters
  const queryParams: ApplicationFilterParams = {
    page,
    page_size: 15,
    search: search.trim() || undefined,
    stage: selectedStage !== "ALL" ? selectedStage : undefined,
    status: selectedStatus !== "ALL" ? selectedStatus : undefined,
    sort_by: "created_at",
    sort_order: "desc",
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["applications", queryParams],
    queryFn: () => applicationService.listApplications(queryParams),
  });

  const createMutation = useMutation({
    mutationFn: (newApp: ApplicationCreateInput) => applicationService.createApplication(newApp),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["application-pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["contact"] });
      setIsAddModalOpen(false);
      setFormData({
        job_title: "",
        company_name: "",
        job_location: "",
        job_location_type: "REMOTE",
        employment_type: "FULL_TIME",
        compensation_min: null,
        compensation_max: null,
        source: "MANUAL",
        status: "ACTIVE",
        current_stage: "APPLIED",
        applied_date: new Date().toISOString().split("T")[0],
        priority: "MEDIUM",
        contact_id: null,
        initial_notes: "",
      });
      setFormError(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to create application";
      setFormError(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.job_title.trim()) {
      setFormError("Job title is required.");
      return;
    }
    if (!formData.company_name.trim()) {
      setFormError("Company name is required.");
      return;
    }
    setFormError(null);
    createMutation.mutate(formData);
  };

  const getStageBadgeVariant = (stage: ApplicationStage) => {
    switch (stage) {
      case "OFFER":
      case "ACCEPTED":
        return "success";
      case "INTERVIEW":
      case "ASSESSMENT":
      case "PHONE_SCREEN":
        return "info";
      case "APPLIED":
        return "neutral";
      case "REJECTED":
      case "WITHDRAWN":
        return "danger";
      default:
        return "neutral";
    }
  };

  const getHealthBadge = (health?: { score: number; status: HealthStatus } | null) => {
    if (!health) return null;
    const { score, status } = health;
    switch (status) {
      case "EXCELLENT":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <HeartPulse className="w-3.5 h-3.5 text-emerald-600" />
            Health: {score}% (Excellent)
          </span>
        );
      case "GOOD":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            <HeartPulse className="w-3.5 h-3.5 text-blue-600" />
            Health: {score}% (Good)
          </span>
        );
      case "NEEDS_ATTENTION":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            <HeartPulse className="w-3.5 h-3.5 text-amber-600" />
            Health: {score}% (Needs Attention)
          </span>
        );
      case "POOR":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200">
            <HeartPulse className="w-3.5 h-3.5 text-red-600" />
            Health: {score}% (Poor)
          </span>
        );
      default:
        return null;
    }
  };

  const applications = data?.items || [];
  const totalCount = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Applications"
        subtitle="Manage and track applications through all standardized hiring pipeline stages."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/applications/pipeline">
              <Button variant="outline">
                <Columns className="w-4 h-4 mr-1.5" /> Pipeline Board
              </Button>
            </Link>
            <Link to="/applications/followups">
              <Button variant="outline">
                <Clock className="w-4 h-4 mr-1.5" /> Follow-ups
              </Button>
            </Link>
            <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> Add Application
            </Button>
          </div>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="w-full md:w-80 relative">
          <Input
            placeholder="Search role, company, or location..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Filter className="w-4 h-4 text-slate-400" />
            <span>Stage:</span>
            <select
              aria-label="Filter by Stage"
              value={selectedStage}
              onChange={(e) => {
                setSelectedStage(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 text-xs font-medium border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Stages</option>
              <option value="APPLIED">Applied</option>
              <option value="PHONE_SCREEN">Phone Screen</option>
              <option value="ASSESSMENT">Assessment</option>
              <option value="INTERVIEW">Interview</option>
              <option value="OFFER">Offer</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected</option>
              <option value="WITHDRAWN">Withdrawn</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span>Status:</span>
            <select
              aria-label="Filter by Status"
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 text-xs font-medium border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="CLOSED">Closed</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-4 animate-pulse">
              <div className="h-5 bg-slate-200 rounded w-1/3 mb-2" />
              <div className="h-4 bg-slate-100 rounded w-1/4 mb-2" />
              <div className="h-3 bg-slate-100 rounded w-1/2" />
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <Card className="p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-800">Failed to load applications</h3>
          <p className="text-sm text-slate-500">Please check your connection and try again.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && applications.length === 0 && (
        <Card className="p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mx-auto text-blue-600">
            <Briefcase className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">No applications found</h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            {search || selectedStage !== "ALL" || selectedStatus !== "ALL"
              ? "Try adjusting your search or stage filters."
              : "Track your first job application or convert a saved opportunity into an active application."}
          </p>
          <div className="pt-2">
            <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> Add Application
            </Button>
          </div>
        </Card>
      )}

      {/* Applications List */}
      {!isLoading && !isError && applications.length > 0 && (
        <div className="space-y-3">
          {applications.map((app) => (
            <Card key={app.id} className="p-4 hover:border-blue-300 transition-colors">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/applications/${app.id}`}
                      className="font-semibold text-slate-900 text-base hover:text-blue-600 transition-colors"
                    >
                      {app.job_title}
                    </Link>
                    <Badge variant={getStageBadgeVariant(app.current_stage)}>
                      {app.current_stage.replace("_", " ")}
                    </Badge>
                    {app.status !== "ACTIVE" && (
                      <Badge variant="neutral">{app.status}</Badge>
                    )}
                    {app.priority === "URGENT" && (
                      <Badge variant="danger">Urgent</Badge>
                    )}
                  </div>

                  <p className="text-sm font-medium text-slate-600 flex items-center gap-1.5">
                    <Building2 className="w-4 h-4 text-slate-400" />
                    <span>{app.company_name}</span>
                    {app.job_location && (
                      <>
                        <span className="text-slate-300">•</span>
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-slate-500 font-normal">{app.job_location}</span>
                      </>
                    )}
                  </p>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-1">
                    {app.applied_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        Applied: {app.applied_date}
                      </span>
                    )}
                    {app.resume && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1 text-slate-600">
                          <FileCheck className="w-3.5 h-3.5 text-blue-500" />
                          Locked: {app.resume.name} (v{app.resume.version})
                        </span>
                      </>
                    )}
                    {app.notes_count ? (
                      <>
                        <span>•</span>
                        <span>{app.notes_count} notes</span>
                      </>
                    ) : null}
                    {app.followups_count ? (
                      <>
                        <span>•</span>
                        <span>{app.followups_count} follow-ups</span>
                      </>
                    ) : null}
                  </div>
                </div>

                <div className="flex items-center gap-4 flex-shrink-0">
                  <div className="text-right hidden sm:block">
                    {getHealthBadge(app.health)}
                  </div>

                  <Link to={`/applications/${app.id}`}>
                    <Button variant="outline" size="sm">
                      View Details <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200 text-sm text-slate-500">
              <div>
                Showing page {page} of {totalPages} ({totalCount} total)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add Application Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Job Application"
        description="Explicitly create an application record to track through the hiring pipeline."
        maxWidth="lg"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
              {formError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Job / Role Title *"
              placeholder="e.g. Senior Backend Engineer"
              value={formData.job_title}
              onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
              required
            />
            <Input
              label="Company Name *"
              placeholder="e.g. Stripe"
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Location"
              placeholder="e.g. San Francisco, CA"
              value={formData.job_location || ""}
              onChange={(e) => setFormData({ ...formData, job_location: e.target.value })}
            />
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Location Type</label>
              <select
                value={formData.job_location_type || "REMOTE"}
                onChange={(e) => setFormData({ ...formData, job_location_type: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
                <option value="ON_SITE">On-Site</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Employment Type</label>
              <select
                value={formData.employment_type || "FULL_TIME"}
                onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="FULL_TIME">Full Time</option>
                <option value="PART_TIME">Part Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Initial Stage</label>
              <select
                value={formData.current_stage || "APPLIED"}
                onChange={(e) => setFormData({ ...formData, current_stage: e.target.value as ApplicationStage })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="APPLIED">Applied</option>
                <option value="PHONE_SCREEN">Phone Screen</option>
                <option value="ASSESSMENT">Assessment</option>
                <option value="INTERVIEW">Interview</option>
                <option value="OFFER">Offer</option>
              </select>
            </div>
            <Input
              type="date"
              label="Application Date"
              value={formData.applied_date || ""}
              onChange={(e) => setFormData({ ...formData, applied_date: e.target.value })}
            />
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Priority</label>
              <select
                value={formData.priority || "MEDIUM"}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as ApplicationPriority })}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <Users2 className="w-3.5 h-3.5 text-slate-500" /> Primary Contact / Recruiter (Optional)
            </label>
            <select
              value={formData.contact_id || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  contact_id: e.target.value || null,
                })
              }
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- No Contact Associated --</option>
              {contactsData?.items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name || ""} ({c.role || "Role unspecified"}
                  {c.company ? ` • ${c.company.name}` : ""})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Initial Note (Optional)</label>
            <textarea
              rows={3}
              placeholder="e.g. Applied directly via hiring manager tweet or referral."
              value={formData.initial_notes || ""}
              onChange={(e) => setFormData({ ...formData, initial_notes: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Creating..." : "Create Application"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
