import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Briefcase,
  Calendar,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Mail,
  MapPin,
  Phone,
  User,
  Users,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { jobService } from "@/services/jobService";
import type { JobPosting, RecruiterApplicant, RecruiterApplicantDetail } from "@/types/job.types";

const STAGES = [
  "APPLIED",
  "PHONE_SCREEN",
  "ASSESSMENT",
  "INTERVIEW",
  "OFFER",
  "ACCEPTED",
  "REJECTED",
];

export const JobApplicantsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobPosting | null>(null);
  const [applicants, setApplicants] = useState<RecruiterApplicant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stageFilter, setStageFilter] = useState<string>("ALL");

  // Detail Modal state
  const [selectedApplicantDetail, setSelectedApplicantDetail] = useState<RecruiterApplicantDetail | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // Transition Stage state
  const [transitioningAppId, setTransitioningAppId] = useState<string | null>(null);
  const [stageNotes, setStageNotes] = useState("");
  const [targetStage, setTargetStage] = useState<string>("");
  const [stageModalOpen, setStageModalOpen] = useState(false);
  const [stageSubmitting, setStageSubmitting] = useState(false);

  const fetchJobAndApplicants = async () => {
    if (!jobId) return;
    setLoading(true);
    try {
      const [jobData, appRes] = await Promise.all([
        jobService.getRecruiterJob(jobId),
        jobService.listApplicants(jobId, {
          stage: stageFilter === "ALL" ? undefined : stageFilter,
        }),
      ]);
      setJob(jobData);
      setApplicants(appRes.items);
      setTotal(appRes.total);
    } catch (err) {
      console.error("Failed to load applicants", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobAndApplicants();
  }, [jobId, stageFilter]);

  const handleOpenDetail = async (appId: string) => {
    setDetailLoading(true);
    setDetailModalOpen(true);
    try {
      const detail = await jobService.getApplicantDetail(appId);
      setSelectedApplicantDetail(detail);
    } catch (err) {
      console.error("Failed to load applicant detail", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleOpenStageChange = (appId: string, currentStage: string) => {
    setTransitioningAppId(appId);
    setTargetStage(currentStage);
    setStageNotes("");
    setStageModalOpen(true);
  };

  const handleStageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transitioningAppId || !targetStage) return;

    setStageSubmitting(true);
    try {
      await jobService.updateApplicantStage(transitioningAppId, targetStage, stageNotes.trim() || undefined);
      setStageModalOpen(false);
      await fetchJobAndApplicants();
      if (selectedApplicantDetail && selectedApplicantDetail.application_id === transitioningAppId) {
        const updated = await jobService.getApplicantDetail(transitioningAppId);
        setSelectedApplicantDetail(updated);
      }
    } catch (err) {
      console.error("Failed to update applicant stage", err);
    } finally {
      setStageSubmitting(false);
    }
  };

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case "APPLIED":
        return <Badge variant="info">Applied</Badge>;
      case "PHONE_SCREEN":
        return <Badge variant="default">Phone Screen</Badge>;
      case "ASSESSMENT":
        return <Badge variant="default">Assessment</Badge>;
      case "INTERVIEW":
        return <Badge variant="warning">Interview</Badge>;
      case "OFFER":
        return <Badge variant="success">Offer Extended</Badge>;
      case "ACCEPTED":
        return <Badge variant="success">Hired / Accepted</Badge>;
      case "REJECTED":
        return <Badge variant="danger">Rejected</Badge>;
      default:
        return <Badge variant="neutral">{stage}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with back navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/recruiter/jobs"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Job Postings
          </Link>
          <h1 className="text-xl font-bold text-slate-900">
            {job ? `Applicants for: ${job.title}` : "Applicants Review"}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Review candidate summaries, access submitted resumes, and advance candidates through recruitment stages.
          </p>
        </div>

        {job && (
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold text-slate-700 bg-slate-100 px-3 py-1.5 rounded-lg">
              {total} Total Applicant{total === 1 ? "" : "s"}
            </span>
          </div>
        )}
      </div>

      {/* Stage Filter Buttons */}
      <div className="flex flex-wrap items-center gap-1.5 bg-white p-3 rounded-xl border border-slate-200">
        <button
          onClick={() => setStageFilter("ALL")}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
            stageFilter === "ALL"
              ? "bg-blue-600 text-white shadow-sm"
              : "bg-slate-50 text-slate-600 hover:bg-slate-100"
          }`}
        >
          All Stages ({total})
        </button>
        {STAGES.map((st) => (
          <button
            key={st}
            onClick={() => setStageFilter(st)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              stageFilter === st
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            {st.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Applicants List */}
      {loading ? (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : applicants.length === 0 ? (
        <EmptyState
          icon={<Users className="w-8 h-8 text-slate-400" />}
          title="No applicants found"
          description={
            stageFilter !== "ALL"
              ? `No applicants currently in '${stageFilter.replace("_", " ")}' stage.`
              : "No candidates have applied to this job posting yet. Ensure the opening is published."
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {applicants.map((app) => (
            <Card key={app.application_id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                      {app.candidate.full_name?.charAt(0) || "C"}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900">
                          {app.candidate.full_name || "Applicant"}
                        </h3>
                        {getStageBadge(app.current_stage)}
                      </div>
                      {app.candidate.headline && (
                        <p className="text-xs text-slate-600 mt-0.5">{app.candidate.headline}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
                    <span className="flex items-center gap-1">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      {app.candidate.email}
                    </span>
                    {app.candidate.phone && (
                      <span className="flex items-center gap-1">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        {app.candidate.phone}
                      </span>
                    )}
                    {app.candidate.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {app.candidate.location}
                      </span>
                    )}
                    {app.applied_date && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        Applied: {new Date(app.applied_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-2 md:pt-0 border-t md:border-t-0">
                  {app.resume_id && (
                    <a
                      href={jobService.getApplicantResumeDownloadUrl(app.application_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5 text-slate-500" />
                      Resume
                    </a>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenStageChange(app.application_id, app.current_stage)}
                  >
                    Change Stage
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleOpenDetail(app.application_id)}
                  >
                    Review Profile
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detail Review Modal */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        title="Candidate Application Review"
        description="Application-scoped candidate details and recruitment stage timeline."
        maxWidth="lg"
      >
        {detailLoading || !selectedApplicantDetail ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Candidate Summary Box */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-base font-bold text-slate-900">
                    {selectedApplicantDetail.candidate.full_name || "Applicant"}
                  </h4>
                  {selectedApplicantDetail.candidate.headline && (
                    <p className="text-xs text-slate-600 mt-0.5">{selectedApplicantDetail.candidate.headline}</p>
                  )}
                </div>
                {getStageBadge(selectedApplicantDetail.current_stage)}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-200 text-xs text-slate-600">
                <div className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span>{selectedApplicantDetail.candidate.email}</span>
                </div>
                {selectedApplicantDetail.candidate.phone && (
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{selectedApplicantDetail.candidate.phone}</span>
                  </div>
                )}
                {selectedApplicantDetail.candidate.location && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{selectedApplicantDetail.candidate.location}</span>
                  </div>
                )}
                {selectedApplicantDetail.applied_date && (
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Applied: {new Date(selectedApplicantDetail.applied_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Submitted Resume & Documents */}
            {selectedApplicantDetail.resume && (
              <div className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <div>
                    <div className="text-xs font-semibold text-slate-800">
                      {selectedApplicantDetail.resume.name}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {selectedApplicantDetail.resume.file_name}
                    </div>
                  </div>
                </div>

                <a
                  href={jobService.getApplicantResumeDownloadUrl(selectedApplicantDetail.application_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-lg hover:bg-blue-100"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Resume
                </a>
              </div>
            )}

            {/* Stage History Timeline */}
            <div>
              <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Recruitment Stage Progression
              </h5>
              <div className="space-y-2 border-l-2 border-blue-500 pl-3">
                {selectedApplicantDetail.stage_history.map((sh) => (
                  <div key={sh.id} className="text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800">{sh.to_stage.replace("_", " ")}</span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(sh.changed_at).toLocaleString()}
                      </span>
                    </div>
                    {sh.notes && <p className="text-slate-500 text-[11px] mt-0.5">{sh.notes}</p>}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <Button
                variant="primary"
                onClick={() => {
                  setDetailModalOpen(false);
                  handleOpenStageChange(
                    selectedApplicantDetail.application_id,
                    selectedApplicantDetail.current_stage
                  );
                }}
              >
                Advance Candidate Stage
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Stage Change Modal */}
      <Modal
        isOpen={stageModalOpen}
        onClose={() => setStageModalOpen(false)}
        title="Advance Candidate Stage"
        description="Update the recruitment milestone and optionally log internal notes."
        maxWidth="md"
      >
        <form onSubmit={handleStageSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Target Stage *</label>
            <select
              value={targetStage}
              onChange={(e) => setTargetStage(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {STAGES.map((st) => (
                <option key={st} value={st}>
                  {st.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Recruiter Notes (Optional)</label>
            <textarea
              rows={3}
              value={stageNotes}
              onChange={(e) => setStageNotes(e.target.value)}
              placeholder="e.g. Completed technical round; moving to hiring manager interview..."
              className="w-full text-xs rounded-lg border border-slate-300 p-3 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setStageModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={stageSubmitting}>
              {stageSubmitting ? "Updating..." : "Update Stage"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
