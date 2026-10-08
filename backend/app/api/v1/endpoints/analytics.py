"""
Career Analytics & Pipeline Metrics API Router.
Stage 9: Analytics & Settings.
Strict user isolation via current_user.id.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ApplicationTrendsResponse,
    CompanyAnalyticsResponse,
    DashboardSummaryResponse,
    OutcomeAnalyticsResponse,
    PipelineAnalyticsResponse,
    TimeAnalyticsResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("", response_model=AnalyticsOverviewResponse, summary="Career Analytics Overview KPIs")
@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Career Analytics Overview KPIs")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve high-level deterministic KPIs: total applications, active count,
    interviews, offers, response rate, interview conversion, and acceptance rate.
    """
    return await analytics_service.get_overview(db=db, user_id=current_user.id)


@router.get("/trends", response_model=ApplicationTrendsResponse, summary="Application Submission & Velocity Trends")
async def get_trends(
    range: str = Query("30d", pattern="^(7d|30d|90d|6m|1y|all)$", description="Date range: 7d, 30d, 90d, 6m, 1y, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Time-series application velocity and interview milestones grouped by day or month.
    """
    return await analytics_service.get_trends(db=db, user_id=current_user.id, range_key=range)


@router.get("/pipeline", response_model=PipelineAnalyticsResponse, summary="Pipeline Funnel Conversion Analytics")
async def get_pipeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Funnel stage progression analysis and stage-to-stage conversion rates.
    """
    return await analytics_service.get_pipeline(db=db, user_id=current_user.id)


@router.get("/companies", response_model=CompanyAnalyticsResponse, summary="Employer-Level Analytics & Response Rates")
async def get_companies(
    limit: int = Query(20, ge=1, le=100, description="Max companies to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Breakdown of applications, interviews, offers, and response rates by target company.
    """
    return await analytics_service.get_companies(db=db, user_id=current_user.id, limit=limit)


@router.get("/outcomes", response_model=OutcomeAnalyticsResponse, summary="Outcome Distribution Breakdown")
async def get_outcomes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Distribution of terminal application outcomes: Accepted, Offers, Rejections, Withdrawn, Active.
    """
    return await analytics_service.get_outcomes(db=db, user_id=current_user.id)


@router.get("/time", response_model=TimeAnalyticsResponse, summary="Progression Velocity & Duration Analytics")
async def get_time_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Time-to-first-response, time-to-interview, time-to-offer, and stage duration metrics.
    """
    return await analytics_service.get_time_metrics(db=db, user_id=current_user.id)


@router.get("/dashboard", response_model=DashboardSummaryResponse, summary="Command Center Summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified dashboard aggregation combining profile completeness, pipeline, and events.
    """
    return await analytics_service.get_dashboard_summary(db=db, user_id=current_user.id)
