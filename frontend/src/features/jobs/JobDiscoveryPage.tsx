import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bookmark,
  Briefcase,
  Building,
  CheckCircle,
  Clock,
  ExternalLink,
  Globe,
  MapPin,
  Search,
  Send,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ApplyModal } from "./ApplyModal";
import { jobService } from "@/services/jobService";
import { useAuthStore } from "@/store/authStore";
import type { JobPosting, JobPostingDetail } from "@/types/job.types";

export const JobDiscoveryPage: React.FC = () => {
  const { user } = useAuthStore();
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [jobDetail, setJobDetail] = useState<JobPostingDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [locationType, setLocationType] = useState<string>("");
  const [employmentType, setEmploymentType] = useState<string>("");
  const [currency, setCurrency] = useState<string>("");

  // Apply modal
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [savingOpportunity, setSavingOpportunity] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobService.listPublishedJobs({
        search: search.trim() || undefined,
        location: location.trim() || undefined,
        location_type: locationType || undefined,
        employment_type: employmentType || undefined,
        currency: currency || undefined,
      });
      setJobs(res.items);
      setTotal(res.total);
      if (res.items.length > 0 && !selectedJobId) {
        setSelectedJobId(res.items[0].id);
      }
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [locationType, employmentType, currency]);

  useEffect(() => {
    if (selectedJobId) {
      const loadDetail = async () => {
        setDetailLoading(true);
        try {
          const detail = await jobService.getPublishedJob(selectedJobId);
          setJobDetail(detail);
        } catch (err) {
          console.error("Failed to load job details", err);
        } finally {
          setDetailLoading(false);
        }
      };
      loadDetail();
    } else {
      setJobDetail(null);
    }
  }, [selectedJobId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs();
  };

  const handleSaveOpportunity = async (jobId: string) => {
    setSavingOpportunity(true);
    try {
      await jobService.saveJobToOpportunity(jobId);
      setSaveSuccessMsg("Saved to your Career OS Opportunities!");
      setTimeout(() => setSaveSuccessMsg(null), 3000);
      if (selectedJobId === jobId) {
        const updated = await jobService.getPublishedJob(jobId);
        setJobDetail(updated);
      }
    } catch (err) {
      console.error("Failed to save opportunity", err);
    } finally {
      setSavingOpportunity(false);
    }
  };

  const handleApplySuccess = async () => {
    if (selectedJobId) {
      const updated = await jobService.getPublishedJob(selectedJobId);
      setJobDetail(updated);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Explore Job Openings</h1>
        <p className="text-xs text-slate-500 mt-1">
          Discover verified roles from employers, save to your opportunities tracker, and apply with your locked Career OS resume.
        </p>
      </div>

      {saveSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          {saveSuccessMsg}
        </div>
      )}

      {/* Search & Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-3">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search title, skills, employer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="relative">
            <MapPin className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Location (e.g. Bengaluru, Remote)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Button type="submit" variant="primary" size="sm" className="w-full">
              Find Jobs
            </Button>
          </div>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
          <span className="text-slate-400 font-medium">Workplace:</span>
          {["", "REMOTE", "HYBRID", "ON_SITE"].map((type) => (
            <button
              key={type}
              onClick={() => setLocationType(type)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                locationType === type
                  ? "bg-blue-600 text-white font-medium"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {type === "" ? "All" : type.replace("_", " ")}
            </button>
          ))}

          <span className="text-slate-400 font-medium ml-2">Type:</span>
          {["", "FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP"].map((type) => (
            <button
              key={type}
              onClick={() => setEmploymentType(type)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                employmentType === type
                  ? "bg-blue-600 text-white font-medium"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {type === "" ? "All" : type.replace("_", " ")}
            </button>
          ))}

          <span className="text-slate-400 font-medium ml-2">Currency:</span>
          {["", "INR", "USD"].map((cur) => (
            <button
              key={cur}
              onClick={() => setCurrency(cur)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                currency === cur
                  ? "bg-blue-600 text-white font-medium"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {cur === "" ? "Any" : cur}
            </button>
          ))}
        </div>
      </div>

      {/* Main 2-Column Split: Job List + Job Detail */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="w-8 h-8 text-slate-400" />}
          title="No open jobs match your criteria"
          description="Try broadening your search keywords, location filters, or workplace preferences."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Job Cards */}
          <div className="lg:col-span-5 space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {jobs.map((job) => {
              const isSelected = selectedJobId === job.id;
              return (
                <div
                  key={job.id}
                  onClick={() => setSelectedJobId(job.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "border-blue-600 bg-blue-50/30 shadow-sm ring-1 ring-blue-500/20"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 leading-snug">{job.title}</h3>
                      <p className="text-xs font-medium text-slate-600 mt-0.5">
                        {job.organization_name || "Employer"}
                      </p>
                    </div>
                    <Badge variant="neutral" size="sm">
                      {job.location_type.replace("_", " ")}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 mt-2">
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        {job.location}
                      </span>
                    )}
                    {(job.compensation_min || job.compensation_max) && (
                      <span className="font-semibold text-slate-700">
                        {job.compensation_currency}{" "}
                        {job.compensation_min?.toLocaleString()}
                        {job.compensation_max ? ` - ${job.compensation_max.toLocaleString()}` : "+"}
                      </span>
                    )}
                  </div>

                  {job.skills && job.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2.5">
                      {job.skills.slice(0, 4).map((s) => (
                        <span
                          key={s.id}
                          className="px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-600 rounded font-medium"
                        >
                          {s.name}
                        </span>
                      ))}
                      {job.skills.length > 4 && (
                        <span className="text-[10px] text-slate-400 self-center">
                          +{job.skills.length - 4}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Right: Job Detail Panel */}
          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-6 sticky top-6 max-h-[calc(100vh-280px)] overflow-y-auto">
            {detailLoading || !jobDetail ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-5 border-b border-slate-100">
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold text-slate-900">{jobDetail.title}</h2>
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Building className="w-4 h-4 text-slate-400" />
                      <span className="font-semibold">{jobDetail.organization_name}</span>
                      {jobDetail.organization?.website && (
                        <a
                          href={jobDetail.organization.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-0.5 ml-1"
                        >
                          Website <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-2">
                      {jobDetail.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {jobDetail.location} ({jobDetail.location_type.replace("_", " ")})
                        </span>
                      )}
                      <Badge variant="neutral">{jobDetail.employment_type.replace("_", " ")}</Badge>
                      {jobDetail.experience_level && (
                        <Badge variant="neutral">{jobDetail.experience_level}</Badge>
                      )}
                      {(jobDetail.compensation_min || jobDetail.compensation_max) && (
                        <span className="font-bold text-slate-900">
                          {jobDetail.compensation_currency} {jobDetail.compensation_min?.toLocaleString()}
                          {jobDetail.compensation_max ? ` - ${jobDetail.compensation_max.toLocaleString()}` : "+"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Primary CTA Area */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={savingOpportunity}
                      onClick={() => handleSaveOpportunity(jobDetail.id)}
                      className="gap-1.5"
                    >
                      <Bookmark className="w-4 h-4 text-slate-500" />
                      Save
                    </Button>

                    {jobDetail.has_applied ? (
                      <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                        <CheckCircle className="w-4 h-4" />
                        Applied
                      </div>
                    ) : user?.role === "HIRER" ? (
                      <span className="text-xs text-slate-400 italic">Hirer view</span>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setApplyModalOpen(true)}
                        className="gap-1.5"
                      >
                        <Send className="w-4 h-4" />
                        Apply Now
                      </Button>
                    )}
                  </div>
                </div>

                {/* Skills Section */}
                {jobDetail.skills && jobDetail.skills.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Required Skills & Competencies
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {jobDetail.skills.map((s) => (
                        <span
                          key={s.id}
                          className="px-2.5 py-1 text-xs bg-blue-50 text-blue-700 rounded-lg font-medium border border-blue-200"
                        >
                          {s.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Job Description */}
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Role Description
                  </h4>
                  <div className="text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                    {jobDetail.description}
                  </div>
                </div>

                {/* Requirements */}
                {jobDetail.requirements && (
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Requirements & Qualifications
                    </h4>
                    <div className="text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                      {jobDetail.requirements}
                    </div>
                  </div>
                )}

                {/* Employer Details */}
                {jobDetail.organization && (
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      About {jobDetail.organization.name}
                    </h4>
                    {jobDetail.organization.description && (
                      <p className="text-xs text-slate-600 leading-relaxed mb-3">
                        {jobDetail.organization.description}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                      {jobDetail.organization.industry && (
                        <span>Industry: {jobDetail.organization.industry}</span>
                      )}
                      {jobDetail.organization.size && (
                        <span>Company Size: {jobDetail.organization.size}</span>
                      )}
                      {jobDetail.organization.location && (
                        <span>HQ: {jobDetail.organization.location}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Apply Modal */}
      <ApplyModal
        job={jobDetail}
        isOpen={applyModalOpen}
        onClose={() => setApplyModalOpen(false)}
        onSuccess={handleApplySuccess}
      />
    </div>
  );
};
