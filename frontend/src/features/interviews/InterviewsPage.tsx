/**
 * Interviews List & Scheduling Hub.
 * Stage 7: Interviews & Interview Preparation.
 */

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import {
  CalendarCheck,
  Plus,
  Clock,
  Video,
  Building2,
  ChevronRight,
  BookOpen,
  Search,
  Filter,
  User,
  ExternalLink,
  MapPin,
  Calendar,
  AlertCircle,
} from "lucide-react";
import { interviewService, type InterviewFilterParams } from "@/services/interviewService";
import { applicationService } from "@/services/applicationService";
import { contactService } from "@/services/contactService";
import type {
  Interview,
  InterviewCreateInput,
  InterviewStatus,
  InterviewType,
} from "@/types/interview.types";

const INTERVIEW_TYPES: { label: string; value: InterviewType }[] = [
  { label: "Technical Interview", value: "TECHNICAL" },
  { label: "Phone Screen", value: "PHONE" },
  { label: "Video Call", value: "VIDEO" },
  { label: "On-Site Round", value: "ON_SITE" },
  { label: "Panel Interview", value: "PANEL" },
  { label: "HR / Culture Screen", value: "HR" },
  { label: "System Design", value: "SYSTEM_DESIGN" },
  { label: "Behavioral Round", value: "BEHAVIORAL" },
];

export const InterviewsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Filters state
  const [statusTab, setStatusTab] = useState<"ALL" | "SCHEDULED" | "COMPLETED" | "CANCELLED">("SCHEDULED");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  // Schedule modal state
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [formData, setFormData] = useState<InterviewCreateInput>({
    application_id: "",
    interview_type: "TECHNICAL",
    round_name: "",
    round_number: 1,
    scheduled_at: "",
    duration_minutes: 60,
    location: "",
    meeting_url: "",
    contact_id: null,
    interviewer_names: "",
    notes: "",
  });

  // Query: Candidate applications for dropdown
  const { data: applicationsData } = useQuery({
    queryKey: ["active-applications-dropdown"],
    queryFn: () => applicationService.listApplications({ status: "ACTIVE", page_size: 100 }),
  });

  // Query: Candidate contacts for interviewer dropdown
  const { data: contactsData } = useQuery({
    queryKey: ["candidate-contacts-dropdown"],
    queryFn: () => contactService.listContacts({ page_size: 100 }),
  });

  // Query: Candidate interviews
  const queryParams: InterviewFilterParams = {
    page,
    page_size: 12,
    search: search.trim() || undefined,
    status: statusTab !== "ALL" ? statusTab : undefined,
    interview_type: selectedType !== "ALL" ? (selectedType as InterviewType) : undefined,
    sort_by: "scheduled_at",
    sort_order: statusTab === "COMPLETED" ? "desc" : "asc",
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["interviews", queryParams],
    queryFn: () => interviewService.listInterviews(queryParams),
  });

  // Mutation: Schedule Interview
  const createMutation = useMutation({
    mutationFn: (payload: InterviewCreateInput) => interviewService.createInterview(payload),
    onSuccess: (newInterview) => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      queryClient.invalidateQueries({ queryKey: ["application", newInterview.application_id] });
      queryClient.invalidateQueries({ queryKey: ["application-interviews", newInterview.application_id] });
      setIsScheduleModalOpen(false);
      setFormData({
        application_id: "",
        interview_type: "TECHNICAL",
        round_name: "",
        round_number: 1,
        scheduled_at: "",
        duration_minutes: 60,
        location: "",
        meeting_url: "",
        contact_id: null,
        interviewer_names: "",
        notes: "",
      });
      navigate(`/interviews/${newInterview.id}`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to schedule interview. Please check your inputs.";
      setFormError(msg);
    },
  });

  const handleScheduleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.application_id) {
      setFormError("Please select the application for this interview.");
      return;
    }
    if (!formData.scheduled_at) {
      setFormError("Please select the interview scheduled date and time.");
      return;
    }

    // Format scheduled_at to ISO string
    const isoDate = new Date(formData.scheduled_at).toISOString();

    createMutation.mutate({
      ...formData,
      scheduled_at: isoDate,
      round_name: formData.round_name?.trim() || undefined,
      interviewer_names: formData.interviewer_names?.trim() || undefined,
      meeting_url: formData.meeting_url?.trim() || undefined,
      location: formData.location?.trim() || undefined,
      notes: formData.notes?.trim() || undefined,
      contact_id: formData.contact_id || null,
    });
  };

  const formatScheduledDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return {
        date: d.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          year: "numeric",
        }),
        time: d.toLocaleTimeString("en-US", {
          hour: "numeric",
          minute: "2-digit",
        }),
      };
    } catch {
      return { date: dateStr, time: "" };
    }
  };

  const getStatusBadge = (status: InterviewStatus) => {
    switch (status) {
      case "SCHEDULED":
        return <Badge variant="default">Scheduled</Badge>;
      case "COMPLETED":
        return <Badge variant="success">Completed</Badge>;
      case "CANCELLED":
        return <Badge variant="danger">Cancelled</Badge>;
      case "RESCHEDULED":
        return <Badge variant="warning">Rescheduled</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getResultBadge = (result?: string | null) => {
    if (!result) return null;
    switch (result) {
      case "PASSED":
        return <Badge variant="success">Passed</Badge>;
      case "FAILED":
        return <Badge variant="danger">Failed</Badge>;
      case "PENDING":
        return <Badge variant="warning">Pending Result</Badge>;
      case "CANCELLED":
        return <Badge variant="neutral">Cancelled</Badge>;
      default:
        return null;
    }
  };

  const interviews = data?.items || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interviews & Preparation"
        subtitle="Manage upcoming interview rounds, track preparation checklists, and document session notes."
        actions={
          <Button variant="primary" onClick={() => setIsScheduleModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" /> Schedule Interview
          </Button>
        }
      />

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {(
            [
              { key: "SCHEDULED", label: "Scheduled / Upcoming" },
              { key: "COMPLETED", label: "Completed" },
              { key: "CANCELLED", label: "Cancelled" },
              { key: "ALL", label: "All Interviews" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setStatusTab(tab.key);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors whitespace-nowrap ${
                statusTab === tab.key
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Type Select */}
        <div className="flex items-center gap-3">
          <div className="relative min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              type="text"
              placeholder="Search role, company, interviewer..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9 text-sm"
            />
          </div>

          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setPage(1);
            }}
            aria-label="Filter by interview type"
            className="text-sm border border-slate-300 rounded-md px-2.5 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Types</option>
            {INTERVIEW_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Interview Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <Card key={n} className="p-5 animate-pulse bg-slate-50 space-y-4">
              <div className="h-4 bg-slate-200 rounded w-1/3" />
              <div className="h-6 bg-slate-200 rounded w-3/4" />
              <div className="h-4 bg-slate-200 rounded w-1/2" />
              <div className="h-10 bg-slate-200 rounded" />
            </Card>
          ))}
        </div>
      ) : isError ? (
        <Card className="p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-900">Failed to load interviews</h3>
          <p className="text-sm text-slate-500">There was an issue fetching your interviews.</p>
          <Button variant="outline" onClick={() => refetch()}>
            Try Again
          </Button>
        </Card>
      ) : interviews.length === 0 ? (
        <Card className="p-12 text-center space-y-4 border-dashed border-2 border-slate-200">
          <CalendarCheck className="w-12 h-12 text-blue-500 mx-auto opacity-80" />
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-900">No interviews found</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              {statusTab === "SCHEDULED"
                ? "You have no upcoming interviews scheduled. Schedule a new interview round linked to your active job applications."
                : "No interviews match the selected status or search filter."}
            </p>
          </div>
          <Button variant="primary" onClick={() => setIsScheduleModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" /> Schedule Interview
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {interviews.map((interview) => {
            const { date, time } = formatScheduledDate(interview.scheduled_at);
            const app = interview.application;
            const contact = interview.contact;

            return (
              <Card
                key={interview.id}
                className="hover:shadow-md transition-shadow flex flex-col justify-between border-slate-200"
              >
                <div className="p-5 space-y-4">
                  {/* Top row: Type badge, Status & Result */}
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="default">
                      {interview.interview_type.replace(/_/g, " ")}
                    </Badge>
                    <div className="flex items-center gap-1.5">
                      {getResultBadge(interview.result)}
                      {getStatusBadge(interview.status)}
                    </div>
                  </div>

                  {/* Header: Round & Company */}
                  <div>
                    <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-1">
                      {interview.round_name || `Round ${interview.round_number || 1} Interview`}
                    </h3>
                    <div className="flex items-center gap-1.5 text-sm text-slate-600 mt-1">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="font-semibold text-slate-800">
                        {app?.company_name || interview.company?.name || "Company"}
                      </span>
                      <span>•</span>
                      <span className="text-slate-600 truncate">
                        {app?.job_title || "Job Application"}
                      </span>
                    </div>
                  </div>

                  {/* Date & Time banner */}
                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 space-y-1 text-xs text-slate-700">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-medium text-slate-900">
                        <Calendar className="w-3.5 h-3.5 text-blue-600" />
                        <span>{date}</span>
                      </div>
                      <div className="flex items-center gap-1 text-slate-500">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{time || "TBD"}</span>
                      </div>
                    </div>
                    {interview.duration_minutes && (
                      <div className="text-[11px] text-slate-500 pl-5">
                        Duration: {interview.duration_minutes} minutes
                      </div>
                    )}
                  </div>

                  {/* Interviewer details */}
                  {(contact || interview.interviewer_names) && (
                    <div className="flex items-center gap-2 text-xs text-slate-600">
                      <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      {contact ? (
                        <Link
                          to={`/network/${contact.id}`}
                          className="text-blue-600 hover:underline truncate font-medium"
                        >
                          {contact.first_name} {contact.last_name || ""}
                          {contact.role ? ` (${contact.role})` : ""}
                        </Link>
                      ) : (
                        <span className="truncate">{interview.interviewer_names}</span>
                      )}
                    </div>
                  )}

                  {/* Meeting Link or Location */}
                  {interview.meeting_url && (
                    <div className="flex items-center gap-1.5 text-xs">
                      <Video className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                      <a
                        href={interview.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:underline truncate flex items-center gap-1 font-medium"
                      >
                        Join Virtual Meeting
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                  {!interview.meeting_url && interview.location && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-600">
                      <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate">{interview.location}</span>
                    </div>
                  )}
                </div>

                {/* Footer Action Buttons */}
                <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
                  <Link
                    to={`/interviews/${interview.id}/prep`}
                    className="flex-1"
                  >
                    <Button variant="outline" size="sm" className="w-full text-xs">
                      <BookOpen className="w-3.5 h-3.5 mr-1 text-blue-600" /> Prep Hub
                    </Button>
                  </Link>

                  <Link
                    to={`/interviews/${interview.id}`}
                    className="flex-1"
                  >
                    <Button variant="primary" size="sm" className="w-full text-xs">
                      Details <ChevronRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-200 pt-4 text-sm text-slate-600">
          <span>
            Showing {(page - 1) * data.page_size + 1} to{" "}
            {Math.min(page * data.page_size, data.total)} of {data.total} interviews
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <span className="px-2 font-medium text-slate-700">
              Page {page} of {data.total_pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Schedule Interview Modal */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => {
          setIsScheduleModalOpen(false);
          setFormError(null);
        }}
        title="Schedule Interview Round"
      >
        <form onSubmit={handleScheduleSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          {/* Application Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Application <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.application_id}
              onChange={(e) => setFormData({ ...formData, application_id: e.target.value })}
              required
              className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Choose active application --</option>
              {applicationsData?.items?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.company_name} — {a.job_title} ({a.current_stage})
                </option>
              ))}
            </select>
          </div>

          {/* Round Name & Number */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Round Name
              </label>
              <Input
                type="text"
                placeholder="e.g. System Design Screen"
                value={formData.round_name || ""}
                onChange={(e) => setFormData({ ...formData, round_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Round #
              </label>
              <Input
                type="number"
                min={1}
                max={20}
                value={formData.round_number || 1}
                onChange={(e) =>
                  setFormData({ ...formData, round_number: parseInt(e.target.value, 10) || 1 })
                }
              />
            </div>
          </div>

          {/* Interview Type & Duration */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Interview Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.interview_type}
                onChange={(e) =>
                  setFormData({ ...formData, interview_type: e.target.value as InterviewType })
                }
                className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {INTERVIEW_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Duration (minutes)
              </label>
              <Input
                type="number"
                min={15}
                max={480}
                step={15}
                value={formData.duration_minutes || 60}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    duration_minutes: parseInt(e.target.value, 10) || 60,
                  })
                }
              />
            </div>
          </div>

          {/* Scheduled Date & Time */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Date & Time <span className="text-red-500">*</span>
            </label>
            <Input
              type="datetime-local"
              required
              value={formData.scheduled_at}
              onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
            />
          </div>

          {/* Meeting URL or Location */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Virtual Meeting URL
              </label>
              <Input
                type="url"
                placeholder="https://meet.google.com/..."
                value={formData.meeting_url || ""}
                onChange={(e) => setFormData({ ...formData, meeting_url: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Office / Location
              </label>
              <Input
                type="text"
                placeholder="e.g. Building 4, Floor 3"
                value={formData.location || ""}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              />
            </div>
          </div>

          {/* Contact / Interviewer Link */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Link Contact / Interviewer (Optional)
            </label>
            <select
              value={formData.contact_id || ""}
              onChange={(e) =>
                setFormData({ ...formData, contact_id: e.target.value || null })
              }
              className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- None (Or enter name below) --</option>
              {contactsData?.items?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name || ""} {c.role ? `— ${c.role}` : ""}{" "}
                  {c.company?.name ? `(${c.company.name})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Fallback Interviewer names */}
          {!formData.contact_id && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Interviewer Name(s)
              </label>
              <Input
                type="text"
                placeholder="e.g. Jane Doe (Tech Lead)"
                value={formData.interviewer_names || ""}
                onChange={(e) => setFormData({ ...formData, interviewer_names: e.target.value })}
              />
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Initial Session Notes / Agenda
            </label>
            <textarea
              rows={3}
              placeholder="Key topics to discuss, expectations, interview format notes..."
              value={formData.notes || ""}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full text-sm border border-slate-300 rounded-md p-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsScheduleModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Scheduling..." : "Schedule Interview"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
