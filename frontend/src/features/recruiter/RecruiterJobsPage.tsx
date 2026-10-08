import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Briefcase,
  Building,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  MapPin,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { CreateJobModal } from "./CreateJobModal";
import { jobService } from "@/services/jobService";
import type { JobPosting, JobStatus } from "@/types/job.types";

export const RecruiterJobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobService.listRecruiterJobs({
        status: selectedStatus === "ALL" ? undefined : selectedStatus,
        search: search.trim() || undefined,
      });
      setJobs(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to load recruiter jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [selectedStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs();
  };

  const handlePublish = async (jobId: string) => {
    setActionLoadingId(jobId);
    try {
      await jobService.publishJob(jobId);
      await fetchJobs();
    } catch (err) {
      console.error("Failed to publish job", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleClose = async (jobId: string) => {
    setActionLoadingId(jobId);
    try {
      await jobService.closeJob(jobId);
      await fetchJobs();
    } catch (err) {
      console.error("Failed to close job", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleArchive = async (jobId: string) => {
    setActionLoadingId(jobId);
    try {
      await jobService.archiveJob(jobId);
      await fetchJobs();
    } catch (err) {
      console.error("Failed to archive job", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const getStatusBadge = (status: JobStatus) => {
    switch (status) {
      case "PUBLISHED":
        return <Badge variant="success">Published</Badge>;
      case "DRAFT":
        return <Badge variant="info">Draft</Badge>;
      case "CLOSED":
        return <Badge variant="warning">Closed</Badge>;
      case "ARCHIVED":
        return <Badge variant="neutral">Archived</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Job Postings Management</h1>
          <p className="text-xs text-slate-500 mt-1">
            Publish openings, review applicant pipelines, and advance recruitment stages.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/recruiter/organization">
            <Button variant="outline" size="sm" className="gap-1.5">
              <Building className="w-3.5 h-3.5 text-slate-500" />
              Company Profile
            </Button>
          </Link>
          <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)} className="gap-1.5">
            <Plus className="w-4 h-4" />
            Post New Job
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200">
        <div className="flex flex-wrap items-center gap-1.5">
          {["ALL", "PUBLISHED", "DRAFT", "CLOSED", "ARCHIVED"].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                selectedStatus === st
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              {st === "ALL" ? "All Jobs" : st.charAt(0) + st.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by title, location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="text-xs rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 w-60 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button type="submit" variant="outline" size="sm">
            Search
          </Button>
        </form>
      </div>

      {/* Postings List */}
      {loading ? (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="w-8 h-8 text-slate-400" />}
          title="No job postings found"
          description={
            selectedStatus !== "ALL"
              ? `No job postings matching status '${selectedStatus}'.`
              : "You haven't created any job postings yet. Create your first opening to attract talent."
          }
          action={
            <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" />
              Post Your First Job
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {jobs.map((job) => (
            <Card key={job.id} className="p-5 hover:shadow-md transition-shadow">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">{job.title}</h3>
                    {getStatusBadge(job.status)}
                    <Badge variant="neutral">{job.employment_type.replace("_", " ")}</Badge>
                    <Badge variant="neutral">{job.location_type.replace("_", " ")}</Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {job.location}
                      </span>
                    )}
                    {(job.compensation_min || job.compensation_max) && (
                      <span className="font-medium text-slate-700">
                        {job.compensation_currency}{" "}
                        {job.compensation_min?.toLocaleString()}
                        {job.compensation_max ? ` - ${job.compensation_max.toLocaleString()}` : "+"}
                      </span>
                    )}
                    {job.deadline_date && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        Closes: {new Date(job.deadline_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  {job.skills && job.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {job.skills.map((s) => (
                        <span
                          key={s.id}
                          className="px-2 py-0.5 text-[11px] bg-slate-100 text-slate-600 rounded-md font-medium"
                        >
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Action / Applicant Counter Area */}
                <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end justify-between gap-3 border-t md:border-t-0 pt-3 md:pt-0">
                  <Link
                    to={`/recruiter/jobs/${job.id}/applicants`}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold transition-colors"
                  >
                    <Users className="w-4 h-4 text-blue-600" />
                    <span>{job.applicant_count} Applicant{job.applicant_count === 1 ? "" : "s"}</span>
                    <ExternalLink className="w-3.5 h-3.5 ml-0.5 text-blue-400" />
                  </Link>

                  <div className="flex items-center gap-2">
                    {job.status === "DRAFT" && (
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={actionLoadingId === job.id}
                        onClick={() => handlePublish(job.id)}
                      >
                        Publish Now
                      </Button>
                    )}
                    {job.status === "PUBLISHED" && (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={actionLoadingId === job.id}
                        onClick={() => handleClose(job.id)}
                      >
                        Close Applications
                      </Button>
                    )}
                    {job.status === "CLOSED" && (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={actionLoadingId === job.id}
                        onClick={() => handleArchive(job.id)}
                      >
                        Archive
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Modal for Creating Job */}
      <CreateJobModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={fetchJobs}
      />
    </div>
  );
};
