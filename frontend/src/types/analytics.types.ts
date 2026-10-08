/**
 * Analytics and Dashboard Types.
 * Stage 9: Analytics & Settings.
 */

export interface AnalyticsOverviewResponse {
  total_applications: number;
  active_applications: number;
  total_opportunities: number;
  saved_opportunities: number;
  interviews_scheduled: number;
  offers_received: number;
  accepted_offers: number;
  rejected_applications: number;
  withdrawn_applications: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  acceptance_rate: number;
}

export interface ApplicationTrendPoint {
  date: string;
  label: string;
  count: number;
  interviews_count: number;
  offers_count: number;
}

export interface ApplicationTrendsResponse {
  range: string;
  points: ApplicationTrendPoint[];
  total_in_period: number;
}

export interface PipelineStageMetric {
  stage: string;
  label: string;
  count: number;
  cumulative_count: number;
  conversion_rate: number;
}

export interface PipelineAnalyticsResponse {
  stages: PipelineStageMetric[];
  rejected_count: number;
  withdrawn_count: number;
  total_applications: number;
}

export interface CompanyAnalyticsItem {
  company_name: string;
  company_id?: string | null;
  total_applications: number;
  active_applications: number;
  interviews_count: number;
  offers_count: number;
  accepted_count: number;
  rejected_count: number;
  response_rate: number;
}

export interface CompanyAnalyticsResponse {
  companies: CompanyAnalyticsItem[];
  total_companies: number;
}

export interface OutcomeMetric {
  outcome: string;
  label: string;
  count: number;
  percentage: number;
}

export interface OutcomeAnalyticsResponse {
  total_outcomes: number;
  active_count: number;
  breakdown: OutcomeMetric[];
}

export interface StageDurationMetric {
  stage: string;
  label: string;
  avg_days: number;
}

export interface TimeAnalyticsResponse {
  avg_days_to_first_response?: number | null;
  avg_days_to_interview?: number | null;
  avg_days_to_offer?: number | null;
  avg_days_overall_lifecycle?: number | null;
  stage_durations: StageDurationMetric[];
}

export interface DashboardSummaryResponse {
  role?: string;
  profile_completeness: number;
  active_applications: number;
  upcoming_interviews: number;
  tasks_due_today: number;
  pending_followups: number;
  offers_in_review: number;
  saved_opportunities_count: number;
  pipeline_counts: Record<string, number>;
  recent_activity: Array<{
    type: string;
    title: string;
    description: string;
    timestamp: string;
    id?: string;
  }>;
  total_jobs_posted?: number | null;
  active_jobs_posted?: number | null;
  total_applicants?: number | null;
  new_applicants_this_week?: number | null;
  total_interviews?: number | null;
  total_offers?: number | null;
  total_hires?: number | null;
}
