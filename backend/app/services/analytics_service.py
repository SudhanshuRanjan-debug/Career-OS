"""
Analytics Service — deterministic relational query aggregations across Career OS data.
Stage 9: Analytics & Settings.
Strictly read-only, user-isolated projections.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import (
    Application,
    ApplicationActivity,
    ApplicationFollowup,
    ApplicationStageHistory,
)
from app.models.interview import Interview
from app.models.job_posting import JobPosting
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.organization import Organization
from app.models.task import Task
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ApplicationTrendPoint,
    ApplicationTrendsResponse,
    CompanyAnalyticsItem,
    CompanyAnalyticsResponse,
    DashboardSummaryResponse,
    OutcomeAnalyticsResponse,
    OutcomeMetric,
    PipelineAnalyticsResponse,
    PipelineStageMetric,
    StageDurationMetric,
    TimeAnalyticsResponse,
)
from app.services.profile_service import profile_service


FUNNEL_STAGES = [
    ("APPLIED", "Applied"),
    ("PHONE_SCREEN", "Phone Screen"),
    ("ASSESSMENT", "Assessment"),
    ("INTERVIEW", "Interview"),
    ("OFFER", "Offer"),
    ("ACCEPTED", "Accepted"),
]

STAGE_ORDER = {
    "APPLIED": 1,
    "PHONE_SCREEN": 2,
    "ASSESSMENT": 3,
    "INTERVIEW": 4,
    "OFFER": 5,
    "ACCEPTED": 6,
    "REJECTED": 99,
    "WITHDRAWN": 99,
}


class AnalyticsService:
    """Calculates deterministic career metrics and pipeline projections."""

    async def get_overview(self, db: AsyncSession, user_id: UUID) -> AnalyticsOverviewResponse:
        """
        High-level KPI overview across all applications, opportunities, and interviews.
        """
        # 1. Total applications
        total_apps_res = await db.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        total_applications = total_apps_res.scalar() or 0

        # 2. Active applications (status == ACTIVE and not in terminal stages)
        active_apps_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status == "ACTIVE",
                Application.current_stage.not_in(["REJECTED", "WITHDRAWN", "ACCEPTED"]),
            )
        )
        active_applications = active_apps_res.scalar() or 0

        # 3. Opportunities
        opps_res = await db.execute(
            select(func.count(Opportunity.id)).where(Opportunity.user_id == user_id)
        )
        total_opportunities = opps_res.scalar() or 0

        saved_opps_res = await db.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.user_id == user_id,
                or_(
                    Opportunity.status == "SAVED",
                    Opportunity.id.in_(
                        select(SavedOpportunity.opportunity_id).where(
                            SavedOpportunity.user_id == user_id
                        )
                    ),
                ),
            )
        )
        saved_opportunities = saved_opps_res.scalar() or 0

        # 4. Interviews
        interviews_res = await db.execute(
            select(func.count(Interview.id)).where(Interview.user_id == user_id)
        )
        interviews_scheduled = interviews_res.scalar() or 0

        # 5. Offers, Accepted, Rejected, Withdrawn
        offers_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                or_(
                    Application.current_stage == "OFFER",
                    Application.current_stage == "ACCEPTED",
                    Application.outcome == "OFFER",
                ),
            )
        )
        offers_received = offers_res.scalar() or 0

        accepted_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                or_(
                    Application.current_stage == "ACCEPTED",
                    Application.outcome == "ACCEPTED",
                ),
            )
        )
        accepted_offers = accepted_res.scalar() or 0

        rejected_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                or_(
                    Application.current_stage == "REJECTED",
                    Application.outcome == "REJECTED",
                ),
            )
        )
        rejected_applications = rejected_res.scalar() or 0

        withdrawn_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                or_(
                    Application.current_stage == "WITHDRAWN",
                    Application.outcome == "WITHDRAWN",
                ),
            )
        )
        withdrawn_applications = withdrawn_res.scalar() or 0

        # 6. Response rate (applications that moved past initial APPLIED stage)
        responded_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.current_stage != "APPLIED",
            )
        )
        responded_count = responded_res.scalar() or 0

        # 7. Interviewed applications (distinct applications with an interview or current_stage in interview+)
        interviewed_apps_res = await db.execute(
            select(func.count(func.distinct(Interview.application_id))).where(
                Interview.user_id == user_id
            )
        )
        apps_with_interviews = interviewed_apps_res.scalar() or 0

        # Deterministic rates
        response_rate = (
            round((responded_count / total_applications) * 100.0, 1)
            if total_applications > 0
            else 0.0
        )
        interview_rate = (
            round((apps_with_interviews / total_applications) * 100.0, 1)
            if total_applications > 0
            else 0.0
        )
        offer_rate = (
            round((offers_received / total_applications) * 100.0, 1)
            if total_applications > 0
            else 0.0
        )
        acceptance_rate = (
            round((accepted_offers / offers_received) * 100.0, 1)
            if offers_received > 0
            else 0.0
        )

        return AnalyticsOverviewResponse(
            total_applications=total_applications,
            active_applications=active_applications,
            total_opportunities=total_opportunities,
            saved_opportunities=saved_opportunities,
            interviews_scheduled=interviews_scheduled,
            offers_received=offers_received,
            accepted_offers=accepted_offers,
            rejected_applications=rejected_applications,
            withdrawn_applications=withdrawn_applications,
            response_rate=response_rate,
            interview_rate=interview_rate,
            offer_rate=offer_rate,
            acceptance_rate=acceptance_rate,
        )

    async def get_trends(
        self, db: AsyncSession, user_id: UUID, range_key: str = "30d"
    ) -> ApplicationTrendsResponse:
        """
        Time-series volume for applications and interviews within the requested date range.
        Engine-neutral: groups in Python for 100% SQLite/PostgreSQL compatibility.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        days_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "6m": 180,
            "1y": 365,
        }
        days_back = days_map.get(range_key)
        start_date = today - timedelta(days=days_back) if days_back else None

        # Fetch applications for user
        app_query = select(Application).where(Application.user_id == user_id)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            app_query = app_query.where(Application.created_at >= start_dt)

        apps = (await db.execute(app_query)).scalars().all()

        # Fetch interviews for user
        int_query = select(Interview).where(Interview.user_id == user_id)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            int_query = int_query.where(Interview.scheduled_at >= start_dt)
        interviews = (await db.execute(int_query)).scalars().all()

        # Determine bucketing:
        # <= 30 days: daily buckets
        # > 30 days and <= 180 days: weekly buckets
        # > 180 days: monthly buckets
        span_days = days_back if days_back else (365 if not apps else max(30, (today - apps[-1].created_at.date()).days))

        points_dict: Dict[str, Dict[str, Any]] = {}

        if span_days <= 30:
            # Daily buckets
            num_days = span_days or 30
            for i in range(num_days - 1, -1, -1):
                d = today - timedelta(days=i)
                key = d.isoformat()
                label = d.strftime("%b %d")
                points_dict[key] = {
                    "date": key,
                    "label": label,
                    "count": 0,
                    "interviews_count": 0,
                    "offers_count": 0,
                }

            for a in apps:
                d_key = (a.applied_date or a.created_at.date()).isoformat()
                if d_key in points_dict:
                    points_dict[d_key]["count"] += 1
                    if a.current_stage in ("OFFER", "ACCEPTED") or a.outcome == "OFFER":
                        points_dict[d_key]["offers_count"] += 1

            for iv in interviews:
                if iv.scheduled_at:
                    d_key = iv.scheduled_at.date().isoformat()
                    if d_key in points_dict:
                        points_dict[d_key]["interviews_count"] += 1

        else:
            # Monthly buckets (YYYY-MM)
            # Build month sequence
            months_count = min(12, max(3, (span_days // 30) + 1))
            cur_year = today.year
            cur_month = today.month

            for i in range(months_count - 1, -1, -1):
                m_offset = cur_month - 1 - i
                y = cur_year + (m_offset // 12)
                m = (m_offset % 12) + 1
                key = f"{y:04d}-{m:02d}"
                d_sample = date(y, m, 1)
                label = d_sample.strftime("%b %Y")
                points_dict[key] = {
                    "date": key,
                    "label": label,
                    "count": 0,
                    "interviews_count": 0,
                    "offers_count": 0,
                }

            for a in apps:
                a_date = a.applied_date or a.created_at.date()
                m_key = f"{a_date.year:04d}-{a_date.month:02d}"
                if m_key in points_dict:
                    points_dict[m_key]["count"] += 1
                    if a.current_stage in ("OFFER", "ACCEPTED") or a.outcome == "OFFER":
                        points_dict[m_key]["offers_count"] += 1

            for iv in interviews:
                if iv.scheduled_at:
                    iv_date = iv.scheduled_at.date()
                    m_key = f"{iv_date.year:04d}-{iv_date.month:02d}"
                    if m_key in points_dict:
                        points_dict[m_key]["interviews_count"] += 1

        points = [ApplicationTrendPoint(**p) for p in points_dict.values()]
        total_in_period = sum(p.count for p in points)

        return ApplicationTrendsResponse(
            range=range_key,
            points=points,
            total_in_period=total_in_period,
        )

    async def get_pipeline(self, db: AsyncSession, user_id: UUID) -> PipelineAnalyticsResponse:
        """
        Analyze applications through the canonical recruitment funnel stages.
        """
        # Fetch all user applications and their stage histories
        apps_res = await db.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .options(selectinload(Application.stage_history))
        )
        apps = apps_res.scalars().all()
        total_applications = len(apps)

        # Count current stage distribution
        current_counts: Dict[str, int] = {}
        for a in apps:
            current_counts[a.current_stage] = current_counts.get(a.current_stage, 0) + 1

        rejected_count = current_counts.get("REJECTED", 0)
        withdrawn_count = current_counts.get("WITHDRAWN", 0)

        # Calculate cumulative progression through the canonical funnel
        # An app has reached a stage if it explicitly visited that stage or reached a subsequent stage,
        # including applications that later became REJECTED or WITHDRAWN.
        cumulative_counts: Dict[str, int] = {s[0]: 0 for s in FUNNEL_STAGES}

        for a in apps:
            visited_stages = {a.current_stage}
            for h in a.stage_history:
                if h.to_stage:
                    visited_stages.add(h.to_stage)
                if h.from_stage:
                    visited_stages.add(h.from_stage)

            # Determine highest funnel stage reached across the full lifecycle
            valid_orders = [
                STAGE_ORDER[s]
                for s in visited_stages
                if s in STAGE_ORDER and STAGE_ORDER[s] < 99
            ]
            highest_funnel_order = max(valid_orders) if valid_orders else 1

            for s_name, _ in FUNNEL_STAGES:
                s_order = STAGE_ORDER.get(s_name, 1)
                # Count in cumulative progression if the app visited or progressed past this stage
                if s_name in visited_stages or highest_funnel_order >= s_order:
                    cumulative_counts[s_name] += 1

        # Build pipeline metrics
        stage_metrics: List[PipelineStageMetric] = []
        prev_cumulative = None

        for s_name, s_label in FUNNEL_STAGES:
            c_count = cumulative_counts[s_name]
            curr_count = current_counts.get(s_name, 0)

            if prev_cumulative is None or prev_cumulative == 0:
                conv_rate = 100.0 if c_count > 0 else 0.0
            else:
                conv_rate = round((c_count / prev_cumulative) * 100.0, 1)

            stage_metrics.append(
                PipelineStageMetric(
                    stage=s_name,
                    label=s_label,
                    count=curr_count,
                    cumulative_count=c_count,
                    conversion_rate=conv_rate,
                )
            )
            prev_cumulative = c_count

        return PipelineAnalyticsResponse(
            stages=stage_metrics,
            rejected_count=rejected_count,
            withdrawn_count=withdrawn_count,
            total_applications=total_applications,
        )

    async def get_companies(
        self, db: AsyncSession, user_id: UUID, limit: int = 20
    ) -> CompanyAnalyticsResponse:
        """
        Group application velocity and outcome breakdown by target employer.
        """
        apps_res = await db.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .options(selectinload(Application.interviews))
        )
        apps = apps_res.scalars().all()

        companies_map: Dict[str, Dict[str, Any]] = {}

        for a in apps:
            name = (a.company_name or "Unknown Company").strip()
            if name not in companies_map:
                companies_map[name] = {
                    "company_name": name,
                    "company_id": a.company_id,
                    "total_applications": 0,
                    "active_applications": 0,
                    "interviews_count": 0,
                    "offers_count": 0,
                    "accepted_count": 0,
                    "rejected_count": 0,
                    "responded_count": 0,
                }

            entry = companies_map[name]
            entry["total_applications"] += 1

            if a.status == "ACTIVE" and a.current_stage not in ("REJECTED", "WITHDRAWN", "ACCEPTED"):
                entry["active_applications"] += 1

            entry["interviews_count"] += len(a.interviews)

            if a.current_stage in ("OFFER", "ACCEPTED") or a.outcome == "OFFER":
                entry["offers_count"] += 1

            if a.current_stage == "ACCEPTED" or a.outcome == "ACCEPTED":
                entry["accepted_count"] += 1

            if a.current_stage == "REJECTED" or a.outcome == "REJECTED":
                entry["rejected_count"] += 1

            if a.current_stage != "APPLIED" or len(a.interviews) > 0:
                entry["responded_count"] += 1

        items: List[CompanyAnalyticsItem] = []
        for c in companies_map.values():
            tot = c["total_applications"]
            resp_rate = round((c["responded_count"] / tot) * 100.0, 1) if tot > 0 else 0.0
            items.append(
                CompanyAnalyticsItem(
                    company_name=c["company_name"],
                    company_id=c["company_id"],
                    total_applications=tot,
                    active_applications=c["active_applications"],
                    interviews_count=c["interviews_count"],
                    offers_count=c["offers_count"],
                    accepted_count=c["accepted_count"],
                    rejected_count=c["rejected_count"],
                    response_rate=resp_rate,
                )
            )

        # Sort by total applications descending
        items.sort(key=lambda x: x.total_applications, reverse=True)
        items = items[:limit]

        return CompanyAnalyticsResponse(
            companies=items,
            total_companies=len(companies_map),
        )

    async def get_outcomes(self, db: AsyncSession, user_id: UUID) -> OutcomeAnalyticsResponse:
        """
        Distribution of application outcomes (Terminal and In-Progress).
        """
        apps_res = await db.execute(
            select(Application).where(Application.user_id == user_id)
        )
        apps = apps_res.scalars().all()
        total_apps = len(apps)

        counts = {
            "ACCEPTED": 0,
            "OFFER": 0,
            "REJECTED": 0,
            "WITHDRAWN": 0,
            "ACTIVE": 0,
        }

        for a in apps:
            if a.current_stage == "ACCEPTED" or a.outcome == "ACCEPTED":
                counts["ACCEPTED"] += 1
            elif a.current_stage == "OFFER" or a.outcome == "OFFER":
                counts["OFFER"] += 1
            elif a.current_stage == "REJECTED" or a.outcome == "REJECTED":
                counts["REJECTED"] += 1
            elif a.current_stage == "WITHDRAWN" or a.outcome == "WITHDRAWN":
                counts["WITHDRAWN"] += 1
            else:
                counts["ACTIVE"] += 1

        # Concluded / terminal outcomes strictly comprise ACCEPTED, REJECTED, and WITHDRAWN.
        # Applications in OFFER stage are in-flight (pending candidate decision/review) and grouped with active pipeline.
        terminal_total = (
            counts["ACCEPTED"] + counts["REJECTED"] + counts["WITHDRAWN"]
        )
        active_total = counts["ACTIVE"] + counts["OFFER"]

        labels = {
            "ACCEPTED": "Accepted Offers",
            "OFFER": "Pending Offers",
            "REJECTED": "Rejections",
            "WITHDRAWN": "Withdrawn",
            "ACTIVE": "Active / In Progress",
        }

        breakdown = []
        for key in ["ACCEPTED", "OFFER", "REJECTED", "WITHDRAWN", "ACTIVE"]:
            cnt = counts[key]
            # Documented denominator is total_applications across all categories
            pct = round((cnt / total_apps) * 100.0, 1) if total_apps > 0 else 0.0
            breakdown.append(
                OutcomeMetric(
                    outcome=key,
                    label=labels[key],
                    count=cnt,
                    percentage=pct,
                )
            )

        return OutcomeAnalyticsResponse(
            total_outcomes=terminal_total,
            active_count=active_total,
            breakdown=breakdown,
        )

    async def get_time_metrics(self, db: AsyncSession, user_id: UUID) -> TimeAnalyticsResponse:
        """
        Deterministic velocity metrics: time-to-first-response, time-to-interview, time-to-offer, stage durations.
        """
        apps_res = await db.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .options(
                selectinload(Application.stage_history),
                selectinload(Application.interviews),
            )
        )
        apps = apps_res.scalars().all()

        first_response_days: List[float] = []
        interview_days: List[float] = []
        offer_days: List[float] = []
        lifecycle_days: List[float] = []

        stage_stay_totals: Dict[str, List[float]] = {}

        for a in apps:
            start_date = a.applied_date or a.created_at.date()
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )

            # Sort stage history by changed_at
            histories = sorted(a.stage_history, key=lambda h: h.changed_at)

            # 1. First response: first history event moving away from APPLIED
            for h in histories:
                if h.to_stage and h.to_stage != "APPLIED":
                    h_date = h.changed_at.date()
                    delta = max(0, (h_date - start_date).days)
                    first_response_days.append(float(delta))
                    break

            # 2. Time to interview: earliest scheduled_at or stage transition to INTERVIEW
            interview_dates: List[date] = []
            for iv in a.interviews:
                if iv.scheduled_at:
                    interview_dates.append(iv.scheduled_at.date())
            for h in histories:
                if h.to_stage == "INTERVIEW":
                    interview_dates.append(h.changed_at.date())

            if interview_dates:
                earliest_iv = min(interview_dates)
                interview_days.append(float(max(0, (earliest_iv - start_date).days)))

            # 3. Time to offer
            for h in histories:
                if h.to_stage in ("OFFER", "ACCEPTED"):
                    delta = max(0, (h.changed_at.date() - start_date).days)
                    offer_days.append(float(delta))
                    break

            # 4. Lifecycle duration: if application reached terminal outcome
            if a.current_stage in ("ACCEPTED", "REJECTED", "WITHDRAWN"):
                terminal_date = a.updated_at.date()
                if histories:
                    terminal_date = histories[-1].changed_at.date()
                delta = max(0, (terminal_date - start_date).days)
                lifecycle_days.append(float(delta))

            # 5. Stage durations
            def _to_naive_utc(dt: datetime) -> datetime:
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt

            for i, h in enumerate(histories):
                stg = h.from_stage or "APPLIED"
                next_dt = _to_naive_utc(h.changed_at)
                prev_dt = (
                    _to_naive_utc(histories[i - 1].changed_at)
                    if i > 0
                    else _to_naive_utc(start_dt)
                )
                duration_days = max(0.0, (next_dt - prev_dt).total_seconds() / 86400.0)
                if stg not in stage_stay_totals:
                    stage_stay_totals[stg] = []
                stage_stay_totals[stg].append(duration_days)

        avg_resp = (
            round(sum(first_response_days) / len(first_response_days), 1)
            if first_response_days
            else None
        )
        avg_interview = (
            round(sum(interview_days) / len(interview_days), 1)
            if interview_days
            else None
        )
        avg_offer = (
            round(sum(offer_days) / len(offer_days), 1)
            if offer_days
            else None
        )
        avg_lifecycle = (
            round(sum(lifecycle_days) / len(lifecycle_days), 1)
            if lifecycle_days
            else None
        )

        stage_metrics: List[StageDurationMetric] = []
        labels_map = dict(FUNNEL_STAGES)
        labels_map["REJECTED"] = "Rejected"
        labels_map["WITHDRAWN"] = "Withdrawn"

        for stg, days_list in stage_stay_totals.items():
            if days_list and stg in labels_map:
                stage_metrics.append(
                    StageDurationMetric(
                        stage=stg,
                        label=labels_map.get(stg, stg),
                        avg_days=round(sum(days_list) / len(days_list), 1),
                    )
                )

        return TimeAnalyticsResponse(
            avg_days_to_first_response=avg_resp,
            avg_days_to_interview=avg_interview,
            avg_days_to_offer=avg_offer,
            avg_days_overall_lifecycle=avg_lifecycle,
            stage_durations=stage_metrics,
        )

    async def get_dashboard_summary(
        self, db: AsyncSession, user_id: UUID
    ) -> DashboardSummaryResponse:
        """
        Unified Career Command Center summary.
        Role-aware: returns candidate job search metrics for CANDIDATE,
        or recruiting funnel metrics for HIRER.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        # Check user role
        user_res = await db.execute(select(User.role).where(User.id == user_id))
        user_role = user_res.scalar_one_or_none() or "CANDIDATE"

        if user_role == "HIRER":
            org_res = await db.execute(select(Organization.id).where(Organization.owner_user_id == user_id))
            org_id = org_res.scalar_one_or_none()

            if not org_id:
                return DashboardSummaryResponse(
                    role="HIRER",
                    total_jobs_posted=0,
                    active_jobs_posted=0,
                    total_applicants=0,
                    new_applicants_this_week=0,
                )

            # Total and active jobs
            total_jobs = (await db.execute(
                select(func.count(JobPosting.id)).where(JobPosting.organization_id == org_id)
            )).scalar() or 0

            active_jobs = (await db.execute(
                select(func.count(JobPosting.id)).where(
                    JobPosting.organization_id == org_id,
                    JobPosting.status == "PUBLISHED",
                )
            )).scalar() or 0

            # Applicants via applications join job_postings
            applicants_query = (
                select(Application)
                .join(JobPosting, Application.job_posting_id == JobPosting.id)
                .where(JobPosting.organization_id == org_id)
            )

            total_applicants = (await db.execute(
                select(func.count()).select_from(applicants_query.subquery())
            )).scalar() or 0

            seven_days_ago = now - timedelta(days=7)
            new_this_week = (await db.execute(
                select(func.count(Application.id))
                .join(JobPosting, Application.job_posting_id == JobPosting.id)
                .where(
                    JobPosting.organization_id == org_id,
                    Application.created_at >= seven_days_ago,
                )
            )).scalar() or 0

            # Pipeline stage breakdown for recruiter
            stage_rows = (await db.execute(
                select(Application.current_stage, func.count(Application.id))
                .join(JobPosting, Application.job_posting_id == JobPosting.id)
                .where(JobPosting.organization_id == org_id)
                .group_by(Application.current_stage)
            )).all()
            pipeline_counts = {st: cnt for st, cnt in stage_rows}
            total_interviews = pipeline_counts.get("INTERVIEW", 0)
            total_offers = pipeline_counts.get("OFFER", 0)
            total_hires = pipeline_counts.get("ACCEPTED", 0)

            return DashboardSummaryResponse(
                role="HIRER",
                total_jobs_posted=total_jobs,
                active_jobs_posted=active_jobs,
                total_applicants=total_applicants,
                new_applicants_this_week=new_this_week,
                total_interviews=total_interviews,
                total_offers=total_offers,
                total_hires=total_hires,
                upcoming_interviews=total_interviews,
                offers_in_review=total_offers,
                pipeline_counts=pipeline_counts,
            )

        # Default: Candidate metrics
        # 1. Profile completeness score
        completeness_res = await profile_service.calculate_completeness(db, user_id)
        profile_score = completeness_res.overall_score

        # 2. Active applications count
        active_apps_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status == "ACTIVE",
                Application.current_stage.not_in(["REJECTED", "WITHDRAWN", "ACCEPTED"]),
            )
        )
        active_applications = active_apps_res.scalar() or 0

        # 3. Upcoming interviews (scheduled_at >= now)
        interviews_res = await db.execute(
            select(func.count(Interview.id)).where(
                Interview.user_id == user_id,
                Interview.status == "SCHEDULED",
                Interview.scheduled_at >= now,
            )
        )
        upcoming_interviews = interviews_res.scalar() or 0

        # 4. Tasks due today
        tasks_res = await db.execute(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.is_completed.is_(False),
                Task.due_date <= today,
            )
        )
        tasks_due_today = tasks_res.scalar() or 0

        # 5. Pending follow-ups
        followups_res = await db.execute(
            select(func.count(ApplicationFollowup.id)).where(
                ApplicationFollowup.user_id == user_id,
                ApplicationFollowup.is_completed.is_(False),
                ApplicationFollowup.due_date <= today,
            )
        )
        pending_followups = followups_res.scalar() or 0

        # 6. Offers in review
        offers_res = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.current_stage == "OFFER",
            )
        )
        offers_in_review = offers_res.scalar() or 0

        # 7. Saved opportunities
        saved_opps_res = await db.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.user_id == user_id,
                or_(
                    Opportunity.status == "SAVED",
                    Opportunity.id.in_(
                        select(SavedOpportunity.opportunity_id).where(
                            SavedOpportunity.user_id == user_id
                        )
                    ),
                ),
            )
        )
        saved_opps_count = saved_opps_res.scalar() or 0

        # 8. Pipeline stage breakdown
        stage_group_res = await db.execute(
            select(Application.current_stage, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.current_stage)
        )
        pipeline_counts = {stage: count for stage, count in stage_group_res.all()}

        # 9. Recent activity items (up to 5)
        activity_res = await db.execute(
            select(ApplicationActivity)
            .join(Application, ApplicationActivity.application_id == Application.id)
            .where(Application.user_id == user_id)
            .order_by(ApplicationActivity.created_at.desc())
            .limit(5)
        )
        recent_activity_records = activity_res.scalars().all()
        recent_activity = [
            {
                "id": str(act.id),
                "application_id": str(act.application_id),
                "event_type": act.event_type,
                "description": act.description,
                "created_at": act.created_at.isoformat(),
            }
            for act in recent_activity_records
        ]

        return DashboardSummaryResponse(
            profile_completeness=profile_score,
            active_applications=active_applications,
            upcoming_interviews=upcoming_interviews,
            tasks_due_today=tasks_due_today,
            pending_followups=pending_followups,
            offers_in_review=offers_in_review,
            saved_opportunities_count=saved_opps_count,
            pipeline_counts=pipeline_counts,
            recent_activity=recent_activity,
        )


analytics_service = AnalyticsService()
