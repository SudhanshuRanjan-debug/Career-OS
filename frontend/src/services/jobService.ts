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

  /**
   * Securely download an applicant's resume using the authenticated API client.
   * Reuses the existing Bearer token / HttpOnly refresh token cookie interceptor mechanism.
   * Parses Content-Disposition header (supporting filename and filename*), creates a Blob object URL,
   * triggers browser download, and revokes the URL after download has initiated.
   */
  async downloadApplicantResume(applicationId: string, fallbackFilename?: string): Promise<void> {
    try {
      const res = await apiClient.get(`/recruiter/jobs/applications/${applicationId}/resume`, {
        responseType: "blob",
      });

      const disposition = res.headers["content-disposition"] as string | undefined;
      const serverFilename = extractFilenameFromContentDisposition(disposition);
      const filename = serverFilename || (fallbackFilename ? sanitizeFilename(fallbackFilename) : "applicant_resume.pdf");

      const contentType = (res.headers["content-type"] as string | undefined) || "application/pdf";
      const blob = new Blob([res.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

      // Revoke the Blob object URL after the browser has had a chance to initiate the download
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 1500);
    } catch (err: unknown) {
      const userMessage = await parseApiErrorMessage(err);
      const downloadError = new Error(userMessage);
      (downloadError as any).cause = err;
      throw downloadError;
    }
  },

  /**
   * Legacy raw endpoint URL generator.
   * @deprecated Use downloadApplicantResume() instead to ensure authorization headers are included.
   */
  getApplicantResumeDownloadUrl(applicationId: string): string {
    return `/api/v1/recruiter/jobs/applications/${applicationId}/resume`;
  },
};

/**
 * Extract filename from Content-Disposition header (RFC 6266 / RFC 5987).
 * Supports both filename* and filename parameters with URI decoding.
 */
export function extractFilenameFromContentDisposition(disposition?: string | null): string | null {
  if (!disposition) return null;

  // 1. Try RFC 5987 / RFC 6266 filename* (e.g., filename*=UTF-8''encoded_name.pdf or filename*=utf-8'en'encoded.pdf)
  const starMatch = disposition.match(/filename\*\s*=\s*([^;]+)/i);
  if (starMatch && starMatch[1]) {
    const rawVal = starMatch[1].trim().replace(/^['"]|['"]$/g, "");
    // Extract charset, language, and encoded text
    const parts = rawVal.split("''");
    const encoded = parts.length > 1 ? parts.slice(1).join("''") : parts[0];
    try {
      const decoded = decodeURIComponent(encoded);
      if (decoded.trim()) {
        return sanitizeFilename(decoded.trim());
      }
    } catch {
      // Fall through to standard filename if decoding fails
    }
  }

  // 2. Try standard filename parameter: filename="name.pdf" or filename=name.pdf
  const standardMatch = disposition.match(/filename\s*=\s*(?:"([^"]+)"|([^;\s]+))/i);
  if (standardMatch) {
    const rawName = standardMatch[1] || standardMatch[2];
    if (rawName && rawName.trim()) {
      return sanitizeFilename(rawName.trim());
    }
  }

  return null;
}

/**
 * Sanitize filename to prevent directory traversal or invalid characters.
 */
export function sanitizeFilename(filename: string): string {
  const clean = filename.replace(/^.*[\\/]/, "").replace(/[<>:"/\\|?*\x00-\x1F]/g, "_").trim();
  return clean || "applicant_resume.pdf";
}

/**
 * Extract user-friendly error message from failed API responses,
 * including cases where Axios receives error payloads as Blobs.
 */
export async function parseApiErrorMessage(
  err: unknown,
  fallbackMessage = "Failed to download resume. Please try again."
): Promise<string> {
  const axiosErr = err as {
    response?: {
      status?: number;
      data?: unknown;
    };
    message?: string;
  };

  if (!axiosErr?.response) {
    return axiosErr?.message || fallbackMessage;
  }

  const { status, data } = axiosErr.response;
  let parsedDetail: string | null = null;

  if (data instanceof Blob) {
    try {
      const text = await data.text();
      const json = JSON.parse(text);
      if (json && typeof json.detail === "string") {
        parsedDetail = json.detail;
      } else if (json && typeof json.message === "string") {
        parsedDetail = json.message;
      }
    } catch {
      // Not JSON Blob
    }
  } else if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === "string") {
      parsedDetail = obj.detail;
    } else if (typeof obj.message === "string") {
      parsedDetail = obj.message;
    }
  }

  if (parsedDetail) {
    return parsedDetail;
  }

  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }
  if (status === 403) {
    return "You are not authorized to view or download this candidate's resume.";
  }
  if (status === 404) {
    return "No resume was found for this applicant.";
  }

  return fallbackMessage;
}

