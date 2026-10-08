/**
 * Interview Details Page.
 * Stage 7: Interviews & Interview Preparation.
 */

import React, { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import {
  ArrowLeft,
  Calendar,
  Clock,
  Video,
  Building2,
  User,
  BookOpen,
  Edit2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  MapPin,
  HelpCircle,
  Briefcase,
  Mail,
  Phone,
} from "lucide-react";
import { interviewService } from "@/services/interviewService";
import { contactService } from "@/services/contactService";
import type {
  InterviewResult,
  InterviewStatus,
  InterviewType,
  InterviewUpdateInput,
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

export const InterviewDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Edit form state
  const [editData, setEditData] = useState<InterviewUpdateInput>({
    round_name: "",
    round_number: 1,
    interview_type: "TECHNICAL",
    status: "SCHEDULED",
    result: null,
    scheduled_at: "",
    duration_minutes: 60,
    location: "",
    meeting_url: "",
    contact_id: null,
    interviewer_names: "",
    notes: "",
    feedback: "",
  });

  // Query: Candidate contacts for editing interviewer
  const { data: contactsData } = useQuery({
    queryKey: ["candidate-contacts-dropdown"],
    queryFn: () => contactService.listContacts({ page_size: 100 }),
  });

  // Query: Interview details
  const { data: interview, isLoading, isError, refetch } = useQuery({
    queryKey: ["interview", id],
    queryFn: () => interviewService.getInterview(id!),
    enabled: !!id,
  });

  // Mutation: Update interview
  const updateMutation = useMutation({
    mutationFn: (payload: InterviewUpdateInput) =>
      interviewService.updateInterview(id!, payload),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["interview", id] });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      queryClient.invalidateQueries({ queryKey: ["application", updated.application_id] });
      setIsEditModalOpen(false);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to update interview details.";
      setFormError(msg);
    },
  });

  // Mutation: Delete interview
  const deleteMutation = useMutation({
    mutationFn: () => interviewService.deleteInterview(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      if (interview?.application_id) {
        queryClient.invalidateQueries({ queryKey: ["application", interview.application_id] });
      }
      navigate("/interviews");
    },
  });

  const openEditModal = () => {
    if (!interview) return;
    setFormError(null);

    // Format ISO string to datetime-local friendly string (YYYY-MM-DDTHH:mm)
    let localScheduled = "";
    try {
      const d = new Date(interview.scheduled_at);
      const pad = (n: number) => String(n).padStart(2, "0");
      localScheduled = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
        d.getHours()
      )}:${pad(d.getMinutes())}`;
    } catch {
      localScheduled = interview.scheduled_at;
    }

    setEditData({
      round_name: interview.round_name || "",
      round_number: interview.round_number || 1,
      interview_type: interview.interview_type,
      status: interview.status,
      result: interview.result || null,
      scheduled_at: localScheduled,
      duration_minutes: interview.duration_minutes || 60,
      location: interview.location || "",
      meeting_url: interview.meeting_url || "",
      contact_id: interview.contact_id || null,
      interviewer_names: interview.interviewer_names || "",
      notes: interview.notes || "",
      feedback: interview.feedback || "",
    });
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    let isoDate = editData.scheduled_at;
    if (editData.scheduled_at) {
      try {
        isoDate = new Date(editData.scheduled_at).toISOString();
      } catch {
        // keep as is
      }
    }

    updateMutation.mutate({
      ...editData,
      scheduled_at: isoDate,
      round_name: editData.round_name?.trim() || null,
      meeting_url: editData.meeting_url?.trim() || null,
      location: editData.location?.trim() || null,
      interviewer_names: editData.interviewer_names?.trim() || null,
      notes: editData.notes?.trim() || null,
      feedback: editData.feedback?.trim() || null,
      contact_id: editData.contact_id || null,
    });
  };

  const handleQuickOutcome = (newResult: InterviewResult, newStatus?: InterviewStatus) => {
    updateMutation.mutate({
      result: newResult,
      status: newStatus || "COMPLETED",
    });
  };

  const formatScheduledDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return {
        date: d.toLocaleDateString("en-US", {
          weekday: "long",
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-slate-200 rounded w-1/4 animate-pulse" />
        <Card className="p-8 space-y-4 animate-pulse bg-slate-50">
          <div className="h-8 bg-slate-200 rounded w-1/2" />
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-32 bg-slate-200 rounded" />
        </Card>
      </div>
    );
  }

  if (isError || !interview) {
    return (
      <Card className="p-12 text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="text-base font-semibold text-slate-900">Interview Not Found</h3>
        <p className="text-sm text-slate-500">
          This interview does not exist or you do not have permission to view it.
        </p>
        <Link to="/interviews">
          <Button variant="primary">Return to Interviews</Button>
        </Link>
      </Card>
    );
  }

  const { date, time } = formatScheduledDate(interview.scheduled_at);
  const app = interview.application;
  const contact = interview.contact;
  const prep = interview.preparation;

  const totalChecklist = prep?.preparation_checklist?.length || 0;
  const completedChecklist =
    prep?.preparation_checklist?.filter((item) => item.done)?.length || 0;

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <Link to="/interviews" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Interviews
        </Link>
        {app && (
          <>
            <span>/</span>
            <Link
              to={`/applications/${app.id}`}
              className="hover:text-blue-600 truncate max-w-xs"
            >
              {app.company_name} — {app.job_title}
            </Link>
          </>
        )}
      </div>

      {/* Page Header */}
      <PageHeader
        title={interview.round_name || `${interview.interview_type.replace(/_/g, " ")} Round`}
        subtitle={`${app?.company_name || interview.company?.name || "Company"} • ${
          app?.job_title || "Candidate Application"
        }`}
        actions={
          <div className="flex items-center gap-2.5">
            <Link to={`/interviews/${interview.id}/prep`}>
              <Button variant="outline">
                <BookOpen className="w-4 h-4 mr-1.5 text-blue-600" /> Prep Hub
              </Button>
            </Link>

            {interview.meeting_url && (
              <a href={interview.meeting_url} target="_blank" rel="noreferrer">
                <Button variant="primary">
                  <Video className="w-4 h-4 mr-1.5" /> Join Meeting
                </Button>
              </a>
            )}

            <Button variant="outline" onClick={openEditModal}>
              <Edit2 className="w-4 h-4 mr-1.5" /> Edit
            </Button>

            <Button
              variant="outline"
              className="text-red-600 hover:bg-red-50 hover:border-red-200"
              onClick={() => setIsDeleteModalOpen(true)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        }
      />

      {/* Badges bar */}
      <div className="flex items-center gap-2">
        <Badge variant="default">{interview.interview_type.replace(/_/g, " ")}</Badge>
        {getStatusBadge(interview.status)}
        {getResultBadge(interview.result)}
        {interview.round_number && (
          <Badge variant="neutral">Round #{interview.round_number}</Badge>
        )}
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Notes, Agenda, Debrief */}
        <div className="lg:col-span-2 space-y-6">
          {/* Session Agenda & Notes */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
              <CardTitle className="text-base">Session Agenda & Topics</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {interview.notes ? (
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {interview.notes}
                </p>
              ) : (
                <div className="text-sm text-slate-400 italic">
                  No session agenda or notes recorded yet. Click &quot;Edit&quot; to outline topics.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Outcome & Post-Interview Feedback */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
              <CardTitle className="text-base">Interview Outcome & Debrief</CardTitle>
              {/* Quick outcome recorder buttons */}
              {interview.status !== "COMPLETED" && (
                <div className="flex items-center gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs text-green-700 hover:bg-green-50"
                    onClick={() => handleQuickOutcome("PASSED")}
                  >
                    Mark Passed
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs text-red-700 hover:bg-red-50"
                    onClick={() => handleQuickOutcome("FAILED")}
                  >
                    Mark Failed
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div className="flex items-center gap-4 text-sm">
                <span className="text-slate-500 font-medium">Result:</span>
                <div>{getResultBadge(interview.result) || <span className="text-slate-400 italic">Pending debrief</span>}</div>
              </div>

              <div>
                <span className="text-slate-500 text-sm font-medium block mb-1">
                  Interviewer Feedback / Debrief Notes:
                </span>
                {interview.feedback ? (
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-200">
                    {interview.feedback}
                  </p>
                ) : (
                  <p className="text-sm text-slate-400 italic">
                    No interviewer feedback recorded yet.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 col): Meta details, Application, Contact, Prep */}
        <div className="space-y-6">
          {/* Meeting Details Card */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" /> Meeting Details
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3 text-sm space-y-3">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Date</span>
                <span className="font-semibold text-slate-900">{date}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Time</span>
                <span className="font-semibold text-slate-900">{time || "TBD"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Duration</span>
                <span className="font-semibold text-slate-900">
                  {interview.duration_minutes || 60} mins
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Format</span>
                <span className="font-semibold text-slate-900">
                  {interview.interview_type.replace(/_/g, " ")}
                </span>
              </div>

              {interview.meeting_url && (
                <div className="pt-1">
                  <span className="text-slate-500 text-xs block mb-1">Virtual Meeting Link:</span>
                  <a
                    href={interview.meeting_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline break-all text-xs flex items-center gap-1 font-medium"
                  >
                    {interview.meeting_url}
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                </div>
              )}

              {interview.location && (
                <div className="pt-1">
                  <span className="text-slate-500 text-xs block mb-1">Office Location:</span>
                  <span className="text-slate-800 text-xs flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    {interview.location}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Associated Application Card */}
          {app && (
            <Card>
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-indigo-600" /> Linked Application
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-3 text-sm space-y-3">
                <div>
                  <h4 className="font-bold text-slate-900">{app.company_name}</h4>
                  <p className="text-slate-600 text-xs mt-0.5">{app.job_title}</p>
                </div>
                <div className="flex items-center justify-between text-xs py-1 border-t border-slate-100">
                  <span className="text-slate-500">Stage:</span>
                  <Badge variant="default">{app.current_stage}</Badge>
                </div>
                <Link to={`/applications/${app.id}`} className="block pt-1">
                  <Button variant="outline" size="sm" className="w-full text-xs">
                    View Full Application <ArrowLeft className="w-3.5 h-3.5 ml-1 rotate-180" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}

          {/* Interviewer / Contact Card */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="w-4 h-4 text-emerald-600" /> Interviewer / Contact
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3 text-sm space-y-3">
              {contact ? (
                <>
                  <div>
                    <h4 className="font-bold text-slate-900">
                      {contact.first_name} {contact.last_name || ""}
                    </h4>
                    {contact.role && (
                      <p className="text-xs text-slate-600 mt-0.5">{contact.role}</p>
                    )}
                    {contact.company_name && (
                      <p className="text-xs text-slate-500">{contact.company_name}</p>
                    )}
                  </div>

                  <div className="space-y-1 text-xs text-slate-600 pt-1 border-t border-slate-100">
                    {contact.email && (
                      <div className="flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5 text-slate-400" />
                        <a
                          href={`mailto:${contact.email}`}
                          className="text-blue-600 hover:underline truncate"
                        >
                          {contact.email}
                        </a>
                      </div>
                    )}
                    {contact.phone && (
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        <span>{contact.phone}</span>
                      </div>
                    )}
                  </div>

                  <Link to={`/network/${contact.id}`} className="block pt-1">
                    <Button variant="outline" size="sm" className="w-full text-xs">
                      View Contact Profile <ArrowLeft className="w-3.5 h-3.5 ml-1 rotate-180" />
                    </Button>
                  </Link>
                </>
              ) : interview.interviewer_names ? (
                <div className="text-sm">
                  <span className="text-slate-500 text-xs block mb-1">Interviewer Name(s):</span>
                  <span className="font-semibold text-slate-800">
                    {interview.interviewer_names}
                  </span>
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic">
                  No specific interviewer assigned. You can link a contact or specify interviewer names via Edit.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Preparation Snapshot Card */}
          <Card className="border-blue-100 bg-blue-50/40">
            <CardHeader className="pb-3 border-b border-blue-100">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2 text-blue-900">
                  <BookOpen className="w-4 h-4 text-blue-600" /> Prep Hub
                </span>
                <span className="text-xs font-semibold text-blue-700">
                  {completedChecklist}/{totalChecklist} done
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3 text-sm space-y-3">
              <p className="text-xs text-slate-600">
                Maintain company research, anticipated questions, talking points, and pre-interview checklists.
              </p>
              <Link to={`/interviews/${interview.id}/prep`} className="block">
                <Button variant="primary" size="sm" className="w-full text-xs">
                  Open Preparation Hub
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Interview Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setFormError(null);
        }}
        title="Edit Interview Session"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          {/* Round Name & Number */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Round Name
              </label>
              <Input
                type="text"
                placeholder="e.g. System Design Screen"
                value={editData.round_name || ""}
                onChange={(e) => setEditData({ ...editData, round_name: e.target.value })}
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
                value={editData.round_number || 1}
                onChange={(e) =>
                  setEditData({ ...editData, round_number: parseInt(e.target.value, 10) || 1 })
                }
              />
            </div>
          </div>

          {/* Type & Status */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Interview Type
              </label>
              <select
                value={editData.interview_type}
                onChange={(e) =>
                  setEditData({ ...editData, interview_type: e.target.value as InterviewType })
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
                Status
              </label>
              <select
                value={editData.status}
                onChange={(e) =>
                  setEditData({ ...editData, status: e.target.value as InterviewStatus })
                }
                className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="SCHEDULED">Scheduled</option>
                <option value="COMPLETED">Completed</option>
                <option value="RESCHEDULED">Rescheduled</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          {/* Scheduled Date/Time & Duration */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Date & Time
              </label>
              <Input
                type="datetime-local"
                value={editData.scheduled_at || ""}
                onChange={(e) => setEditData({ ...editData, scheduled_at: e.target.value })}
              />
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
                value={editData.duration_minutes || 60}
                onChange={(e) =>
                  setEditData({
                    ...editData,
                    duration_minutes: parseInt(e.target.value, 10) || 60,
                  })
                }
              />
            </div>
          </div>

          {/* Result / Outcome */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Interview Result
            </label>
            <select
              value={editData.result || ""}
              onChange={(e) =>
                setEditData({
                  ...editData,
                  result: (e.target.value as InterviewResult) || null,
                })
              }
              className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Pending / Not Decided --</option>
              <option value="PASSED">Passed</option>
              <option value="FAILED">Failed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {/* Virtual URL & Location */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Virtual Meeting URL
              </label>
              <Input
                type="url"
                placeholder="https://zoom.us/..."
                value={editData.meeting_url || ""}
                onChange={(e) => setEditData({ ...editData, meeting_url: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Office / Location
              </label>
              <Input
                type="text"
                placeholder="Office address or room"
                value={editData.location || ""}
                onChange={(e) => setEditData({ ...editData, location: e.target.value })}
              />
            </div>
          </div>

          {/* Contact / Interviewer Link */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Link Contact / Interviewer
            </label>
            <select
              value={editData.contact_id || ""}
              onChange={(e) =>
                setEditData({ ...editData, contact_id: e.target.value || null })
              }
              className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- None --</option>
              {contactsData?.items?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name || ""} {c.role ? `— ${c.role}` : ""}{" "}
                  {c.company?.name ? `(${c.company.name})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Interviewer Name(s) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Interviewer Name(s)
            </label>
            <Input
              type="text"
              placeholder="e.g. Elena Rostova"
              value={editData.interviewer_names || ""}
              onChange={(e) => setEditData({ ...editData, interviewer_names: e.target.value })}
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Session Agenda & Notes
            </label>
            <textarea
              rows={3}
              value={editData.notes || ""}
              onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
              className="w-full text-sm border border-slate-300 rounded-md p-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Debrief & Feedback */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Post-Interview Debrief / Feedback
            </label>
            <textarea
              rows={3}
              placeholder="Questions asked, areas that went well, followup items..."
              value={editData.feedback || ""}
              onChange={(e) => setEditData({ ...editData, feedback: e.target.value })}
              className="w-full text-sm border border-slate-300 rounded-md p-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
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
        title="Delete Interview"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Are you sure you want to delete this interview round? All associated preparation
            notes and checklists will also be permanently removed.
          </p>
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
            <Button
              variant="outline"
              onClick={() => setIsDeleteModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Confirm Delete"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
