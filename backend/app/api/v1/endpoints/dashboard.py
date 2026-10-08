"""
Dashboard Command Center API Router.
Stage 9: Analytics & Settings.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import DashboardSummaryResponse
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse, summary="Career Command Center Summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified command center aggregation (profile completeness, pipeline counts,
    upcoming interviews, today's tasks, pending follow-ups, saved opportunities, quick stats).
    """
    return await analytics_service.get_dashboard_summary(db=db, user_id=current_user.id)
