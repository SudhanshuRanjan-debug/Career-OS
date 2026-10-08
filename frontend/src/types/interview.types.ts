/**
 * Interview & Interview Preparation Domain Types.
 * Stage 7: Interviews & Interview Preparation.
 */

export type InterviewType =
  | "PHONE"
  | "VIDEO"
  | "ON_SITE"
  | "TECHNICAL"
  | "PANEL"
  | "HR"
  | "SYSTEM_DESIGN"
  | "BEHAVIORAL";

export type InterviewStatus =
  | "SCHEDULED"
  | "COMPLETED"
  | "CANCELLED"
  | "RESCHEDULED";

export type InterviewResult =
  | "PASSED"
  | "FAILED"
  | "PENDING"
  | "CANCELLED";

export interface InterviewApplicationSummary {
  id: string;
  job_title: string;
  company_name: string;
  current_stage: string;
  status: string;
}

export interface InterviewContactSummary {
  id: string;
  first_name: string;
  last_name?: string | null;
  role?: string | null;
  email?: string | null;
  phone?: string | null;
  contact_type?: string | null;
  company_name?: string | null;
}

export interface InterviewCompanySummary {
  id: string;
  name: string;
  website?: string | null;
  logo_url?: string | null;
}

export interface ChecklistItem {
  id: string;
  label: string;
  done: boolean;
}

export interface InterviewPreparation {
  id: string;
  interview_id: string;
  company_research?: string | null;
  role_research?: string | null;
  questions_to_ask?: string | null;
  personal_notes?: string | null;
  preparation_checklist: ChecklistItem[];
  post_interview_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Interview {
  id: string;
  user_id: string;
  application_id: string;
  company_id?: string | null;
  contact_id?: string | null;
  interview_type: InterviewType;
  round_number?: number | null;
  round_name?: string | null;
  status: InterviewStatus;
  scheduled_at: string;
  duration_minutes?: number | null;
  location?: string | null;
  meeting_url?: string | null;
  interviewer_names?: string | null;
  result?: InterviewResult | null;
  notes?: string | null;
  feedback?: string | null;
  created_at: string;
  updated_at: string;
  application?: InterviewApplicationSummary | null;
  company?: InterviewCompanySummary | null;
  contact?: InterviewContactSummary | null;
  preparation?: InterviewPreparation | null;
}

export interface InterviewSummary {
  id: string;
  application_id: string;
  interview_type: InterviewType;
  round_name?: string | null;
  status: InterviewStatus;
  scheduled_at: string;
  duration_minutes?: number | null;
  meeting_url?: string | null;
  interviewer_names?: string | null;
  result?: InterviewResult | null;
  job_title?: string | null;
  company_name?: string | null;
}

export interface InterviewCreateInput {
  application_id: string;
  company_id?: string | null;
  contact_id?: string | null;
  interview_type: InterviewType;
  round_number?: number | null;
  round_name?: string | null;
  status?: InterviewStatus;
  scheduled_at: string;
  duration_minutes?: number | null;
  location?: string | null;
  meeting_url?: string | null;
  interviewer_names?: string | null;
  result?: InterviewResult | null;
  notes?: string | null;
  feedback?: string | null;
}

export interface InterviewUpdateInput {
  interview_type?: InterviewType;
  round_number?: number | null;
  round_name?: string | null;
  status?: InterviewStatus;
  scheduled_at?: string;
  duration_minutes?: number | null;
  location?: string | null;
  meeting_url?: string | null;
  contact_id?: string | null;
  interviewer_names?: string | null;
  result?: InterviewResult | null;
  notes?: string | null;
  feedback?: string | null;
}

export interface InterviewListResponse {
  items: Interview[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface InterviewPreparationUpdateInput {
  company_research?: string | null;
  role_research?: string | null;
  questions_to_ask?: string | null;
  personal_notes?: string | null;
  preparation_checklist?: ChecklistItem[];
  post_interview_notes?: string | null;
}
