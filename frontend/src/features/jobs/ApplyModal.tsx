import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, FileText, Send, Upload } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { jobService } from "@/services/jobService";
import { resumeService } from "@/services/resumeService";
import type { ResumeItem } from "@/types/resume.types";
import type { JobPostingDetail } from "@/types/job.types";

interface ApplyModalProps {
  job: JobPostingDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ApplyModal: React.FC<ApplyModalProps> = ({ job, isOpen, onClose, onSuccess }) => {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>("");
  const [notes, setNotes] = useState("");
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      const fetchResumes = async () => {
        setLoadingResumes(true);
        try {
          const res = await resumeService.listResumes();
          const items = res.items || [];
          setResumes(items);
          const defaultResume = items.find((r) => r.is_default) || items[0];
          if (defaultResume) {
            setSelectedResumeId(defaultResume.id);
          }
        } catch (err) {
          console.error("Failed to load resumes", err);
        } finally {
          setLoadingResumes(false);
        }
      };
      fetchResumes();
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!job || !selectedResumeId) return;

    setError(null);
    setSubmitting(true);
    try {
      await jobService.applyToJob(job.id, {
        resume_id: selectedResumeId,
        notes: notes.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to submit application. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={job ? `Apply to ${job.title}` : "Submit Application"}
      description={job?.organization_name ? `At ${job.organization_name}` : "Submit your verified application"}
      maxWidth="md"
    >
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      {loadingResumes ? (
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      ) : resumes.length === 0 ? (
        <div className="text-center py-6 space-y-3">
          <p className="text-xs text-slate-600">
            You don't have any resumes in your Career OS vault yet.
          </p>
          <Link to="/resumes">
            <Button variant="primary" size="sm" className="gap-1.5">
              <Upload className="w-3.5 h-3.5" />
              Upload Resume First
            </Button>
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-2">
              Select Resume to Submit *
            </label>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {resumes.map((r) => {
                const isSelected = selectedResumeId === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedResumeId(r.id)}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-slate-300 bg-white"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <FileText className={`w-4 h-4 ${isSelected ? "text-blue-600" : "text-slate-400"}`} />
                      <div className="truncate">
                        <div className="text-xs font-semibold text-slate-900 truncate">{r.name}</div>
                        <div className="text-[11px] text-slate-400">
                          {r.is_default ? "Default • " : ""}{r.original_filename} (v{r.version})
                        </div>
                      </div>
                    </div>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />}
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Note or Cover Message (Optional)
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Introduce yourself or highlight why you are a great match for this role..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-500">
            <strong>Data Privacy:</strong> Submitting will share only your profile contact info and this selected resume with {job?.organization_name || "the recruiter"}. Your private vault, other applications, and target companies remain strictly confidential.
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={submitting} className="gap-1.5">
              <Send className="w-3.5 h-3.5" />
              {submitting ? "Submitting..." : "Submit Application"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
};
