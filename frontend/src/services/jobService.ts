/**
 * Job Postings & Recruiter Platform API Service.
 */

import { apiClient } from "@/lib/axios";
import type {
  CreateJobPayload,
  JobApplyPayload,
  JobPosting,
  JobPostingDetail,
  Organization,
  RecruiterApplicant,
  RecruiterApplicantDetail,
} from "@/types/job.types";

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const jobService = {
  // Candidate / Public Discovery
  async listPublishedJobs(params?: {
    search?: string;
    location?: string;
    location_type?: string;
    employment_type?: string;
    experience_level?: string;
    skill?: string;
    min_compensation?: number;
    currency?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResult<JobPosting>> {
    const res = await apiClient.get<PaginatedResult<JobPosting>>("/jobs", { params });
    return res.data;
  },

  async getPublishedJob(id: string): Promise<JobPostingDetail> {
    const res = await apiClient.get<JobPostingDetail>(`/jobs/${id}`);
    return res.data;
  },

  async saveJobToOpportunity(id: string): Promise<any> {
    const res = await apiClient.post(`/jobs/${id}/save`);
    return res.data;
  },

  async applyToJob(id: string, payload: JobApplyPayload): Promise<any> {
    const res = await apiClient.post(`/jobs/${id}/apply`, payload);
    return res.data;
  },

  // Recruiter Organization
  async getOrganization(): Promise<Organization> {
    const res = await apiClient.get<Organization>("/recruiter/organization");
    return res.data;
  },

  async updateOrganization(payload: Partial<Organization>): Promise<Organization> {
    const res = await apiClient.patch<Organization>("/recruiter/organization", payload);
    return res.data;
  },

  // Recruiter Job Postings
  async listRecruiterJobs(params?: {
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResult<JobPosting>> {
    const res = await apiClient.get<PaginatedResult<JobPosting>>("/recruiter/jobs", { params });
    return res.data;
  },

  async createJob(payload: CreateJobPayload): Promise<JobPosting> {
    const res = await apiClient.post<JobPosting>("/recruiter/jobs", payload);
    return res.data;
  },

  async getRecruiterJob(id: string): Promise<JobPosting> {
    const res = await apiClient.get<JobPosting>(`/recruiter/jobs/${id}`);
    return res.data;
  },

  async updateJob(id: string, payload: Partial<CreateJobPayload>): Promise<JobPosting> {
    const res = await apiClient.patch<JobPosting>(`/recruiter/jobs/${id}`, payload);
    return res.data;
  },

  async publishJob(id: string): Promise<JobPosting> {
    const res = await apiClient.post<JobPosting>(`/recruiter/jobs/${id}/publish`);
    return res.data;
  },

  async closeJob(id: string): Promise<JobPosting> {
    const res = await apiClient.post<JobPosting>(`/recruiter/jobs/${id}/close`);
    return res.data;
  },

  async archiveJob(id: string): Promise<JobPosting> {
    const res = await apiClient.post<JobPosting>(`/recruiter/jobs/${id}/archive`);
    return res.data;
  },

  // Recruiter Applicant Management
  async listApplicants(jobId: string, params?: { stage?: string; page?: number; page_size?: number }): Promise<PaginatedResult<RecruiterApplicant>> {
    const res = await apiClient.get<PaginatedResult<RecruiterApplicant>>(`/recruiter/jobs/${jobId}/applicants`, { params });
    return res.data;
  },

  async getApplicantDetail(applicationId: string): Promise<RecruiterApplicantDetail> {
    const res = await apiClient.get<RecruiterApplicantDetail>(`/recruiter/jobs/applications/${applicationId}`);
    return res.data;
  },

  async updateApplicantStage(applicationId: string, to_stage: string, notes?: string): Promise<RecruiterApplicantDetail> {
    const res = await apiClient.post<RecruiterApplicantDetail>(`/recruiter/jobs/applications/${applicationId}/stage`, {
      to_stage,
      notes,
    });
    return res.data;
  },

  getApplicantResumeDownloadUrl(applicationId: string): string {
    return `/api/v1/recruiter/jobs/applications/${applicationId}/resume`;
  },
};
