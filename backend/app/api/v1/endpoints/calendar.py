"""
Calendar API endpoints — pure aggregation of cross-domain career schedule events.
Stage 8: Tasks, Calendar & Notifications.
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.calendar import CalendarScheduleResponse
from app.services.calendar_service import calendar_service

router = APIRouter(dependencies=[Depends(require_candidate)])


@router.get("", response_model=CalendarScheduleResponse)
async def get_calendar_schedule(
    start_date: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    event_types: Optional[List[str]] = Query(None, description="Event type filters: INTERVIEW, TASK, FOLLOW_UP, DEADLINE"),
    event_type: Optional[str] = Query(None, description="Single event type filter: INTERVIEW, TASK, FOLLOW_UP, DEADLINE"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated schedule events across interviews, tasks, follow-ups, and application deadlines.
    Pure read aggregation over domain models with tenant isolation.
    """
    merged_types = list(event_types) if event_types else []
    if event_type and event_type not in merged_types:
        merged_types.append(event_type)

    return await calendar_service.get_schedule(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        event_types=merged_types if merged_types else None,
    )
