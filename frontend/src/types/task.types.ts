export type TaskPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";
export type TaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
export type TaskRelatedType = "APPLICATION" | "INTERVIEW" | "COMPANY" | "CONTACT" | "GENERAL";

export interface TaskApplicationSummary {
  id: string;
  job_title: string;
  company_name: string;
  current_stage: string;
  status: string;
  applied_date?: string | null;
}

export interface TaskInterviewSummary {
  id: string;
  stage?: string | null;
  interview_type: string;
  status: string;
  scheduled_at: string;
}

export interface TaskCompanySummary {
  id: string;
  name: string;
  website?: string | null;
  industry?: string | null;
}

export interface TaskContactSummary {
  id: string;
  first_name: string;
  last_name?: string | null;
  role?: string | null;
  contact_type?: string | null;
  email?: string | null;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  due_date?: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  is_completed: boolean;
  completed_at?: string | null;
  related_type?: TaskRelatedType | null;
  application_id?: string | null;
  interview_id?: string | null;
  company_id?: string | null;
  contact_id?: string | null;
  application?: TaskApplicationSummary | null;
  interview?: TaskInterviewSummary | null;
  company?: TaskCompanySummary | null;
  contact?: TaskContactSummary | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateInput {
  title: string;
  description?: string | null;
  due_date?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  related_type?: TaskRelatedType;
  application_id?: string | null;
  interview_id?: string | null;
  company_id?: string | null;
  contact_id?: string | null;
}

export interface TaskUpdateInput {
  title?: string;
  description?: string | null;
  due_date?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  is_completed?: boolean;
  related_type?: TaskRelatedType;
  application_id?: string | null;
  interview_id?: string | null;
  company_id?: string | null;
  contact_id?: string | null;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
}
