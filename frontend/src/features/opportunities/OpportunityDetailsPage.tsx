import React, { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  MapPin,
  DollarSign,
  Briefcase,
  Calendar,
  ExternalLink,
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Edit3,
  AlertCircle,
  Clock,
  Sparkles,
  Info,
  CheckCircle2,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { opportunityService } from "@/services/opportunityService";
import { applicationService } from "@/services/applicationService";
import { resumeService } from "@/services/resumeService";
import type {
  Opportunity,
  OpportunityStatus,
  LocationType,
  EmploymentType,
  OpportunityUpdateInput,
} from "@/types/opportunity.types";
import type {
  ApplicationConvertInput,
  ApplicationPriority,
  ApplicationStage,
} from "@/types/application.types";

export const OpportunityDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isConvertModalOpen, setIsConvertModalOpen] = useState(false);
  const [editFormError, setEditFormError] = useState<string | null>(null);

  // Convert to Application state
  const [convertResumeId, setConvertResumeId] = useState<string>("");
  const [convertStage, setConvertStage] = useState<ApplicationStage>("APPLIED");
  const [convertAppliedDate, setConvertAppliedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [convertPriority, setConvertPriority] = useState<ApplicationPriority>("MEDIUM");
  const [convertNotes, setConvertNotes] = useState<string>("");
  const [convertError, setConvertError] = useState<string | null>(null);

  // Editable notes state
  const [personalNotes, setPersonalNotes] = useState<string>("");
  const [isNotesModified, setIsNotesModified] = useState(false);

  // Edit form state
  const [editFormData, setEditFormData] = useState<OpportunityUpdateInput>({});

  // Query: Get Opportunity by ID
  const {
    data: opportunity,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => opportunityService.getOpportunity(id!),
    enabled: Boolean(id),
  });

  // Sync initial personal notes and edit form data when opportunity loads
  React.useEffect(() => {
    if (opportunity) {
      setPersonalNotes(opportunity.notes || "");
      setIsNotesModified(false);
      setEditFormData({
        title: opportunity.title,
        company_name: opportunity.company_name,
        source: opportunity.source,
        source_url: opportunity.source_url,
        location: opportunity.location,
        location_type: opportunity.location_type,
        employment_type: opportunity.employment_type,
        compensation_min: opportunity.compensation_min,
        compensation_max: opportunity.compensation_max,
        compensation_currency: opportunity.compensation_currency || "USD",
        posted_date: opportunity.posted_date,
        expiry_date: opportunity.expiry_date,
        status: opportunity.status,
        description: opportunity.description,
        requirements: opportunity.requirements,
        notes: opportunity.notes,
      });
    }
  }, [opportunity]);

  // Mutation: Save / Unsave
  const toggleSaveMutation = useMutation({
    mutationFn: async () => {
      if (!opportunity) throw new Error("No opportunity");
      if (opportunity.is_saved) {
        await opportunityService.unsaveOpportunity(opportunity.id);
      } else {
        await opportunityService.saveOpportunity(opportunity.id);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
    },
  });

  // Mutation: Quick Status / Notes Update
  const updateMutation = useMutation({
    mutationFn: (data: OpportunityUpdateInput) => opportunityService.updateOpportunity(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
      setIsNotesModified(false);
      setIsEditModalOpen(false);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail;
      setEditFormError(typeof msg === "string" ? msg : "Failed to update opportunity.");
    },
  });

  // Mutation: Delete Opportunity
  const deleteMutation = useMutation({
    mutationFn: () => opportunityService.deleteOpportunity(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["saved-opportunities"] });
      navigate("/opportunities");
    },
  });

  // Query: User Resumes for Convert Modal
  const { data: resumesData, isLoading: isLoadingResumes } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumeService.listResumes(),
    enabled: isConvertModalOpen,
  });

  // Mutation: Convert Opportunity to Application
  const convertMutation = useMutation({
    mutationFn: (data: ApplicationConvertInput) =>
      applicationService.convertOpportunity(id!, data),
    onSuccess: (newApp) => {
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["pipeline"] });
      setIsConvertModalOpen(false);
      navigate(`/applications/${newApp.id}`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail;
      setConvertError(typeof msg === "string" ? msg : "Failed to convert opportunity to application.");
    },
  });

  const handleConvertSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setConvertError(null);
    convertMutation.mutate({
      resume_id: convertResumeId || null,
      current_stage: convertStage,
      applied_date: convertAppliedDate || null,
      priority: convertPriority,
      initial_notes: convertNotes.trim() || null,
    });
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setEditFormError(null);

    if (editFormData.title && !editFormData.title.trim()) {
      setEditFormError("Job title cannot be empty.");
      return;
    }

    if (editFormData.source_url && editFormData.source_url.trim()) {
      const urlLower = editFormData.source_url.trim().toLowerCase();
      if (!urlLower.startsWith("http://") && !urlLower.startsWith("https://")) {
        setEditFormError("External URL must start with http:// or https://");
        return;
      }
    }

    if (
      editFormData.compensation_min !== null &&
      editFormData.compensation_min !== undefined &&
      editFormData.compensation_max !== null &&
      editFormData.compensation_max !== undefined &&
      Number(editFormData.compensation_min) > Number(editFormData.compensation_max)
    ) {
      setEditFormError("Minimum compensation cannot exceed maximum compensation.");
      return;
    }

    if (editFormData.posted_date && editFormData.expiry_date && editFormData.posted_date > editFormData.expiry_date) {
      setEditFormError("Posted date cannot be after deadline/expiration date.");
      return;
    }

    updateMutation.mutate({
      ...editFormData,
      compensation_min: editFormData.compensation_min ? Number(editFormData.compensation_min) : null,
      compensation_max: editFormData.compensation_max ? Number(editFormData.compensation_max) : null,
    });
  };

  const handleSaveNotes = () => {
    updateMutation.mutate({ notes: personalNotes.trim() || null });
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-slate-200 rounded w-48 animate-pulse" />
        <Card className="p-8 space-y-4 animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-100 rounded w-1/4" />
          <div className="space-y-2 pt-6">
            <div className="h-4 bg-slate-100 rounded w-full" />
            <div className="h-4 bg-slate-100 rounded w-5/6" />
            <div className="h-4 bg-slate-100 rounded w-3/4" />
          </div>
        </Card>
      </div>
    );
  }

  if (isError || !opportunity) {
    return (
      <div className="space-y-6">
        <Link to="/opportunities" className="inline-flex items-center text-sm text-slate-500 hover:text-blue-600">
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Opportunities
        </Link>
        <Card className="p-8 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900">Opportunity Not Found</h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            The requested opportunity does not exist or you do not have permission to view it.
          </p>
          <Link to="/opportunities">
            <Button variant="primary" size="sm">
              Return to Opportunities
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/opportunities"
          className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Opportunities
        </Link>
        <span className="text-xs text-slate-400 flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" /> Added {new Date(opportunity.created_at).toLocaleDateString()}
        </span>
      </div>

      {/* Header with Title & Action Controls */}
      <PageHeader
        title={opportunity.title}
        description={`${opportunity.company_name || "Company Unspecified"} • ${opportunity.location || "Location Unspecified"}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant={opportunity.is_saved ? "secondary" : "outline"}
              size="sm"
              onClick={() => toggleSaveMutation.mutate()}
              disabled={toggleSaveMutation.isPending}
              leftIcon={
                opportunity.is_saved ? (
                  <BookmarkCheck className="w-4 h-4 text-amber-600" />
                ) : (
                  <Bookmark className="w-4 h-4" />
                )
              }
            >
              {opportunity.is_saved ? "Saved" : "Save"}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setEditFormError(null);
                setIsEditModalOpen(true);
              }}
              leftIcon={<Edit3 className="w-4 h-4" />}
            >
              Edit
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDeleteModalOpen(true)}
              className="text-red-600 hover:bg-red-50 hover:border-red-200"
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              Delete
            </Button>

            {opportunity.job_posting_id && (
              <Link to="/jobs">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-blue-600 hover:bg-blue-50 hover:border-blue-200"
                  leftIcon={<ExternalLink className="w-4 h-4" />}
                >
                  View Job on Board
                </Button>
              </Link>
            )}

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsConvertModalOpen(true)}
              leftIcon={<Sparkles className="w-4 h-4 text-blue-200" />}
            >
              Convert to Application
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Role Details, Requirements, Tracking Notes */}
        <div className="lg:col-span-2 space-y-6">
          {/* Role Overview */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>Role Description</CardTitle>
              <div className="flex items-center gap-2">
                {getStatusBadge(opportunity.status)}
                {opportunity.location_type && (
                  <Badge variant="neutral">
                    {opportunity.location_type.replace("_", " ")}
                  </Badge>
                )}
                {opportunity.employment_type && (
                  <Badge variant="neutral">
                    {opportunity.employment_type.replace("_", " ")}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {opportunity.description ? (
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {opportunity.description}
                </p>
              ) : (
                <p className="text-sm text-slate-400 italic">No description provided for this opportunity.</p>
              )}

              {opportunity.requirements && (
                <div className="pt-4 border-t border-slate-100">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                    Key Requirements & Qualifications
                  </h4>
                  <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {opportunity.requirements}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tracking & Personal Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Tracking & Organization</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                  Update Tracking Status
                </label>
                <div className="flex flex-wrap gap-2">
                  {(["ACTIVE", "CONSIDERING", "SAVED", "ARCHIVED", "NOT_INTERESTED"] as OpportunityStatus[]).map(
                    (st) => (
                      <button
                        key={st}
                        onClick={() => updateMutation.mutate({ status: st })}
                        disabled={updateMutation.isPending}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          opportunity.status === st
                            ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        {st.replace("_", " ")}
                      </button>
                    )
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                  Personal Tracking Notes
                </label>
                <textarea
                  rows={4}
                  placeholder="Record discussions, referral contacts, compensation notes, or follow-up goals..."
                  value={personalNotes}
                  onChange={(e) => {
                    setPersonalNotes(e.target.value);
                    setIsNotesModified(true);
                  }}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
                />
                {isNotesModified && (
                  <div className="mt-2 flex justify-end">
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={handleSaveNotes}
                      disabled={updateMutation.isPending}
                    >
                      {updateMutation.isPending ? "Saving..." : "Save Notes"}
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Opportunity Metadata Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Opportunity Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3.5 text-sm">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-slate-400 shrink-0" /> Company
                </span>
                <span className="font-semibold text-slate-900 text-right truncate max-w-[160px]">
                  {opportunity.company_name || "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-slate-400 shrink-0" /> Location
                </span>
                <span className="font-medium text-slate-800 text-right truncate max-w-[160px]">
                  {opportunity.location || "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-slate-400 shrink-0" /> Work Arrangement
                </span>
                <span className="font-medium text-slate-800">
                  {opportunity.location_type ? opportunity.location_type.replace("_", " ") : "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-400 shrink-0" /> Employment Type
                </span>
                <span className="font-medium text-slate-800">
                  {opportunity.employment_type ? opportunity.employment_type.replace("_", " ") : "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-slate-400 shrink-0" /> Compensation
                </span>
                <span className="font-medium text-slate-800 text-right text-xs">
                  {formatCompensation(opportunity.compensation_min, opportunity.compensation_max, opportunity.compensation_currency)}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-400 shrink-0" /> Posted Date
                </span>
                <span className="font-medium text-slate-800">
                  {opportunity.posted_date || "Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-400 shrink-0" /> Deadline
                </span>
                <span className="font-medium text-slate-800">
                  {opportunity.expiry_date || "Open / Unspecified"}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 flex items-center gap-2">
                  <Info className="w-4 h-4 text-slate-400 shrink-0" /> Discovery Source
                </span>
                <span className="font-medium text-slate-800">
                  {opportunity.source || "MANUAL"}
                </span>
              </div>

              {opportunity.source_url && (
                <div className="pt-2">
                  <a
                    href={opportunity.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    View Original Job Posting <ExternalLink className="w-3.5 h-3.5 ml-1" />
                  </a>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Opportunity Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Opportunity"
        description="Update opportunity details, compensation, and requirements."
        maxWidth="lg"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          {editFormError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{editFormError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Input
                label="Job Title *"
                value={editFormData.title || ""}
                onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                required
              />
            </div>

            <div>
              <Input
                label="Company Name"
                value={editFormData.company_name || ""}
                onChange={(e) => setEditFormData({ ...editFormData, company_name: e.target.value })}
              />
            </div>

            <div>
              <Input
                label="Location"
                value={editFormData.location || ""}
                onChange={(e) => setEditFormData({ ...editFormData, location: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Work Arrangement</label>
              <select
                value={editFormData.location_type || ""}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
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
                value={editFormData.employment_type || ""}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
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
                value={editFormData.compensation_min ?? ""}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    compensation_min: e.target.value ? Number(e.target.value) : null,
                  })
                }
              />
            </div>

            <div>
              <Input
                label="Max Compensation"
                type="number"
                value={editFormData.compensation_max ?? ""}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    compensation_max: e.target.value ? Number(e.target.value) : null,
                  })
                }
              />
            </div>

            <div className="md:col-span-2">
              <Input
                label="Job Posting URL"
                value={editFormData.source_url || ""}
                onChange={(e) => setEditFormData({ ...editFormData, source_url: e.target.value })}
              />
            </div>

            <div>
              <Input
                label="Posted Date"
                type="date"
                value={editFormData.posted_date || ""}
                onChange={(e) => setEditFormData({ ...editFormData, posted_date: e.target.value || null })}
              />
            </div>

            <div>
              <Input
                label="Deadline Date"
                type="date"
                value={editFormData.expiry_date || ""}
                onChange={(e) => setEditFormData({ ...editFormData, expiry_date: e.target.value || null })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <textarea
                rows={3}
                value={editFormData.description || ""}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Requirements</label>
              <textarea
                rows={3}
                value={editFormData.requirements || ""}
                onChange={(e) => setEditFormData({ ...editFormData, requirements: e.target.value })}
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsEditModalOpen(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Opportunity"
        description="Are you sure you want to delete this opportunity? This action cannot be undone."
        maxWidth="sm"
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDeleteModalOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete Opportunity"}
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          This will permanently remove <strong>{opportunity.title}</strong> at{" "}
          <strong>{opportunity.company_name || "Company"}</strong> and any bookmarks from your queue.
        </p>
      </Modal>

      {/* Convert to Application (Stage 5 Active Modal) */}
      <Modal
        isOpen={isConvertModalOpen}
        onClose={() => {
          setIsConvertModalOpen(false);
          setConvertError(null);
        }}
        title="Convert to Application"
        description="Snapshot this job opportunity into your active applications pipeline."
        maxWidth="md"
      >
        <form onSubmit={handleConvertSubmit} className="space-y-4">
          {convertError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{convertError}</span>
            </div>
          )}

          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2.5">
            <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div className="text-xs text-blue-900 leading-relaxed">
              Converting creates an immutable application snapshot for <strong>{opportunity?.title}</strong> at{" "}
              <strong>{opportunity?.company_name || "Company"}</strong>. The original Stage 4 opportunity status remains unchanged.
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Attach Versioned Resume</label>
            <select
              value={convertResumeId}
              onChange={(e) => setConvertResumeId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoadingResumes}
            >
              <option value="">-- No resume attached (or attach later) --</option>
              {resumesData?.items.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} (v{r.version}){r.is_default ? " — [Default]" : ""}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500">
              Select the resume version you submitted with this application.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Initial Stage</label>
              <select
                value={convertStage}
                onChange={(e) => setConvertStage(e.target.value as ApplicationStage)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="APPLIED">Applied</option>
                <option value="PHONE_SCREEN">Phone Screen</option>
                <option value="ASSESSMENT">Assessment</option>
                <option value="INTERVIEW">Interview</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Priority</label>
              <select
                value={convertPriority}
                onChange={(e) => setConvertPriority(e.target.value as ApplicationPriority)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          <Input
            type="date"
            label="Applied Date"
            value={convertAppliedDate}
            onChange={(e) => setConvertAppliedDate(e.target.value)}
            helperText="Date application was submitted."
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Initial Tracking Notes (Optional)</label>
            <textarea
              rows={3}
              placeholder="e.g. Applied directly via careers portal; referral from Jane."
              value={convertNotes}
              onChange={(e) => setConvertNotes(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setIsConvertModalOpen(false);
                setConvertError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={convertMutation.isPending}
              leftIcon={<Sparkles className="w-4 h-4 text-blue-200" />}
            >
              Convert to Application
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
