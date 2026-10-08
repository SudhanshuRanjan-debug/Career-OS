export type JobStatus = "DRAFT" | "PUBLISHED" | "CLOSED" | "ARCHIVED";
export type LocationType = "REMOTE" | "HYBRID" | "ON_SITE";
export type EmploymentType = "FULL_TIME" | "PART_TIME" | "CONTRACT" | "INTERNSHIP";
export type ExperienceLevel = "ENTRY" | "MID" | "SENIOR" | "LEAD" | "EXECUTIVE";

export interface JobPostingSkill {
  id: string;
  job_posting_id: string;
  name: string;
}

export interface Organization {
  id: string;
  owner_user_id: string;
  name: string;
  slug?: string | null;
  website?: string | null;
  industry?: string | null;
  size?: string | null;
  location?: string | null;
  description?: string | null;
  logo_url?: string | null;
  linkedin_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobPosting {
  id: string;
  organization_id: string;
  created_by_user_id: string;
  title: string;
  description: string;
  requirements?: string | null;
  location?: string | null;
  location_type: LocationType;
  employment_type: EmploymentType;
  experience_level?: ExperienceLevel | null;
  compensation_min?: number | null;
  compensation_max?: number | null;
  compensation_currency: string;
  status: JobStatus;
  deadline_date?: string | null;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
  skills: JobPostingSkill[];
  organization_name?: string | null;
  applicant_count: number;
}

export interface JobPostingDetail extends JobPosting {
  organization?: Organization | null;
  has_applied?: boolean;
  saved_opportunity_id?: string | null;
}

export interface CreateJobPayload {
  title: string;
  description: string;
  requirements?: string;
  location?: string;
  location_type: LocationType;
  employment_type: EmploymentType;
  experience_level?: ExperienceLevel;
  compensation_min?: number;
  compensation_max?: number;
  compensation_currency?: string;
  deadline_date?: string;
  skills: string[];
}

export interface CandidateApplicationSummary {
  candidate_user_id: string;
  full_name?: string | null;
  headline?: string | null;
  email: string;
  phone?: string | null;
  location?: string | null;
}

export interface RecruiterApplicant {
  application_id: string;
  job_posting_id: string;
  candidate: CandidateApplicationSummary;
  current_stage: string;
  status: string;
  applied_date?: string | null;
  created_at: string;
  resume_id?: string | null;
  resume_name?: string | null;
}

export interface RecruiterApplicantDetail {
  application_id: string;
  job_posting_id: string;
  job_title: string;
  candidate: CandidateApplicationSummary;
  current_stage: string;
  status: string;
  applied_date?: string | null;
  created_at: string;
  resume?: {
    id: string;
    name: string;
    file_name: string;
    file_size_bytes?: number;
    created_at: string;
  } | null;
  cover_letter_doc_id?: string | null;
  stage_history: Array<{
    id: string;
    from_stage?: string | null;
    to_stage: string;
    changed_at: string;
    notes?: string | null;
  }>;
  notes: Array<{
    id: string;
    content: string;
    created_at: string;
  }>;
}

export interface JobApplyPayload {
  resume_id: string;
  cover_letter_doc_id?: string;
  notes?: string;
}
