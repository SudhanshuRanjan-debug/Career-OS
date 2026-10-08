import type { ContactSummary } from "./contact.types";

export type ApplicationStage =
  | "APPLIED"
  | "PHONE_SCREEN"
  | "ASSESSMENT"
  | "INTERVIEW"
  | "OFFER"
  | "ACCEPTED"
  | "REJECTED"
  | "WITHDRAWN";

export type ApplicationStatus = "ACTIVE" | "CLOSED" | "ARCHIVED";
export type ApplicationPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";
export type ApplicationOutcome = "ACCEPTED" | "REJECTED" | "WITHDRAWN" | "OFFER_DECLINED";
export type HealthStatus = "EXCELLENT" | "GOOD" | "NEEDS_ATTENTION" | "POOR";

export interface ResumeSnapshotInfo {
  id: string;
  name: string;
  original_filename: string;
  version: number;
}

export interface ApplicationHealthCheck {
  check_id: string;
  name: string;
  category: "REQUIRED" | "PENALTY" | "SUGGESTION";
  passed: boolean;
  impact: number;
  message: string;
}

export interface ApplicationHealth {
  score: number;
  status: HealthStatus;
  checks: ApplicationHealthCheck[];
}

export interface Application {
  id: string;
  user_id: string;
  company_id: string | null;
  opportunity_id: string | null;
  contact_id: string | null;
  job_title: string;
  company_name: string;
  job_location: string | null;
  job_location_type: string | null;
  employment_type: string | null;
  job_description: string | null;
  job_url: string | null;
  compensation_min: number | null;
  compensation_max: number | null;
  compensation_currency: string | null;
  source: string | null;
  status: ApplicationStatus;
  current_stage: ApplicationStage;
  applied_date: string | null;
  deadline_date: string | null;
  resume_id: string | null;
  cover_letter_doc_id: string | null;
  priority: ApplicationPriority;
  outcome: ApplicationOutcome | null;
  created_at: string;
  updated_at: string;
  resume?: ResumeSnapshotInfo | null;
  contact?: ContactSummary | null;
  health?: ApplicationHealth | null;
  notes_count?: number;
  followups_count?: number;
  documents_count?: number;
}

export interface ApplicationCreateInput {
  job_title: string;
  company_name: string;
  company_id?: string | null;
  opportunity_id?: string | null;
  contact_id?: string | null;
  job_location?: string | null;
  job_location_type?: string | null;
  employment_type?: string | null;
  job_description?: string | null;
  job_url?: string | null;
  compensation_min?: number | null;
  compensation_max?: number | null;
  compensation_currency?: string | null;
  source?: string | null;
  status?: ApplicationStatus;
  current_stage?: ApplicationStage;
  applied_date?: string | null;
  deadline_date?: string | null;
  resume_id?: string | null;
  cover_letter_doc_id?: string | null;
  priority?: ApplicationPriority;
  initial_notes?: string | null;
}

export interface ApplicationUpdateInput {
  job_title?: string;
  company_name?: string;
  company_id?: string | null;
  contact_id?: string | null;
  job_location?: string | null;
  job_location_type?: string | null;
  employment_type?: string | null;
  job_description?: string | null;
  job_url?: string | null;
  compensation_min?: number | null;
  compensation_max?: number | null;
  compensation_currency?: string | null;
  source?: string | null;
  status?: ApplicationStatus;
  current_stage?: ApplicationStage;
  applied_date?: string | null;
  deadline_date?: string | null;
  resume_id?: string | null;
  cover_letter_doc_id?: string | null;
  priority?: ApplicationPriority;
  outcome?: ApplicationOutcome | null;
}

export interface ApplicationConvertInput {
  resume_id?: string | null;
  cover_letter_doc_id?: string | null;
  current_stage?: ApplicationStage;
  applied_date?: string | null;
  priority?: ApplicationPriority;
  initial_notes?: string | null;
}

export interface ApplicationListResponse {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StageHistory {
  id: string;
  application_id: string;
  from_stage: string | null;
  to_stage: ApplicationStage;
  changed_at: string;
  notes: string | null;
  changed_by_user: string | null;
}

export interface ApplicationNote {
  id: string;
  application_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationFollowup {
  id: string;
  application_id: string;
  user_id: string;
  due_date: string | null;
  note: string | null;
  is_completed: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationFollowupWithApp extends ApplicationFollowup {
  job_title?: string | null;
  company_name?: string | null;
  current_stage?: string | null;
  application_status?: string | null;
}

export interface DocumentMetaSummary {
  id: string;
  name: string;
  original_filename: string;
  doc_type: string;
  file_size_bytes: number;
}

export interface ApplicationDocument {
  id: string;
  application_id: string;
  document_id: string;
  attached_at: string;
  document?: DocumentMetaSummary | null;
}

export interface ApplicationActivity {
  id: string;
  application_id: string;
  user_id: string;
  event_type: string;
  event_data: Record<string, any> | null;
  description: string;
  created_at: string;
}

export interface PipelineColumn {
  stage: ApplicationStage;
  name: string;
  count: number;
  items: Application[];
}

export interface PipelineResponse {
  columns: PipelineColumn[];
  total_active: number;
}

export interface QAVaultEntry {
  id: string;
  user_id: string;
  question: string;
  answer: string;
  category: string | null;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationAnswer {
  id: string;
  application_id: string;
  qa_vault_entry_id: string | null;
  question: string;
  answer: string;
  created_at: string;
  updated_at: string;
}
