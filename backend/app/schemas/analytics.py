"""
Analytics & Dashboard Pydantic Schemas.
Stage 9: Analytics & Settings.
"""

from datetime import date as dt_date, datetime as dt_datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_applications: int = Field(0, description="Total applications submitted or tracked")
    active_applications: int = Field(0, description="Applications currently in active consideration")
    total_opportunities: int = Field(0, description="Total opportunities discovered or tracked")
    saved_opportunities: int = Field(0, description="Opportunities bookmarked as saved")
    interviews_scheduled: int = Field(0, description="Total interview sessions scheduled or held")
    offers_received: int = Field(0, description="Total job offers extended")
    accepted_offers: int = Field(0, description="Accepted job offers")
    rejected_applications: int = Field(0, description="Applications ended in rejection")
    withdrawn_applications: int = Field(0, description="Applications withdrawn by candidate")
    response_rate: float = Field(0.0, description="Percentage of applications that progressed past initial APPLIED stage")
    interview_rate: float = Field(0.0, description="Percentage of applications that reached an interview")
    offer_rate: float = Field(0.0, description="Percentage of applications that resulted in an offer")
    acceptance_rate: float = Field(0.0, description="Percentage of received offers that were accepted")


class ApplicationTrendPoint(BaseModel):
    date: str = Field(..., description="Date or period bucket identifier (YYYY-MM-DD or YYYY-WW or YYYY-MM)")
    label: str = Field(..., description="Human-readable period label")
    count: int = Field(0, description="Applications submitted in this period")
    interviews_count: int = Field(0, description="Interviews held or scheduled in this period")
    offers_count: int = Field(0, description="Offers received in this period")


class ApplicationTrendsResponse(BaseModel):
    range: str = Field(..., description="Active time range: 7d, 30d, 90d, 6m, 1y, all")
    points: List[ApplicationTrendPoint] = Field(default_factory=list)
    total_in_period: int = Field(0, description="Total applications submitted within range")


class PipelineStageMetric(BaseModel):
    stage: str = Field(..., description="Application stage name")
    label: str = Field(..., description="Human-readable stage label")
    count: int = Field(0, description="Current number of applications at this stage")
    cumulative_count: int = Field(0, description="Total applications that have ever reached this stage")
    conversion_rate: float = Field(0.0, description="Conversion percentage from preceding pipeline stage")


class PipelineAnalyticsResponse(BaseModel):
    stages: List[PipelineStageMetric] = Field(default_factory=list)
    rejected_count: int = Field(0, description="Applications in REJECTED stage")
    withdrawn_count: int = Field(0, description="Applications in WITHDRAWN stage")
    total_applications: int = Field(0, description="Total applications tracked")


class CompanyAnalyticsItem(BaseModel):
    company_name: str = Field(..., description="Employer name")
    company_id: Optional[UUID] = Field(None, description="Linked company UUID if available")
    total_applications: int = Field(0, description="Applications submitted to this company")
    active_applications: int = Field(0, description="Active applications at this company")
    interviews_count: int = Field(0, description="Interviews held with this company")
    offers_count: int = Field(0, description="Offers received from this company")
    accepted_count: int = Field(0, description="Accepted offers from this company")
    rejected_count: int = Field(0, description="Rejected applications from this company")
    response_rate: float = Field(0.0, description="Percentage of applications receiving response")


class CompanyAnalyticsResponse(BaseModel):
    companies: List[CompanyAnalyticsItem] = Field(default_factory=list)
    total_companies: int = Field(0, description="Count of distinct employers")


class OutcomeMetric(BaseModel):
    outcome: str = Field(..., description="Outcome identifier: ACCEPTED, OFFER, REJECTED, WITHDRAWN, ACTIVE")
    label: str = Field(..., description="Human-readable outcome name")
    count: int = Field(0, description="Count of applications with this outcome")
    percentage: float = Field(0.0, description="Percentage of total applications")


class OutcomeAnalyticsResponse(BaseModel):
    total_outcomes: int = Field(0, description="Total completed/terminal applications")
    active_count: int = Field(0, description="Applications currently active in pipeline")
    breakdown: List[OutcomeMetric] = Field(default_factory=list)


class StageDurationMetric(BaseModel):
    stage: str = Field(..., description="Stage identifier")
    label: str = Field(..., description="Human-readable stage name")
    avg_days: float = Field(0.0, description="Average days applications remain in this stage")


class TimeAnalyticsResponse(BaseModel):
    avg_days_to_first_response: Optional[float] = Field(None, description="Average days from submission to first stage change or interview")
    avg_days_to_interview: Optional[float] = Field(None, description="Average days from submission to first interview")
    avg_days_to_offer: Optional[float] = Field(None, description="Average days from submission to job offer")
    avg_days_overall_lifecycle: Optional[float] = Field(None, description="Average days from submission to terminal outcome")
    stage_durations: List[StageDurationMetric] = Field(default_factory=list)


class DashboardSummaryResponse(BaseModel):
    role: str = Field("CANDIDATE", description="CANDIDATE or HIRER")
    profile_completeness: int = Field(0, description="Profile completeness percentage (0-100)")
    active_applications: int = Field(0, description="Current active applications count")
    upcoming_interviews: int = Field(0, description="Count of scheduled upcoming interviews")
    tasks_due_today: int = Field(0, description="Action items due today")
    pending_followups: int = Field(0, description="Application follow-ups due today or overdue")
    offers_in_review: int = Field(0, description="Offers received currently in review")
    saved_opportunities_count: int = Field(0, description="Saved opportunities count")
    pipeline_counts: Dict[str, int] = Field(default_factory=dict, description="Applications count by stage")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Latest activity items across pipeline")

    # Recruiter-specific summary metrics (HIRER role)
    total_jobs_posted: Optional[int] = Field(None, description="Total jobs created by employer")
    active_jobs_posted: Optional[int] = Field(None, description="Currently published jobs count")
    total_applicants: Optional[int] = Field(None, description="Total applicants received across all jobs")
    new_applicants_this_week: Optional[int] = Field(None, description="Applicants received in last 7 days")
    total_interviews: Optional[int] = Field(None, description="Applicants in interview stage")
    total_offers: Optional[int] = Field(None, description="Applicants with offers")
    total_hires: Optional[int] = Field(None, description="Applicants hired/accepted")
