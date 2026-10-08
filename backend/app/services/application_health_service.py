"""
Deterministic Application Health Engine.
Stage 5 Master Implementation.
Zero AI, Zero LLMs, Zero external dependencies.
Calculates transparent, rule-based health score, status, and actionable checks.
"""

from datetime import date, datetime, timezone, timedelta
from typing import Any, List, Optional
from uuid import UUID

from app.models.application import Application, ApplicationFollowup, ApplicationNote, ApplicationActivity
from app.schemas.application import ApplicationHealthCheck, ApplicationHealthResponse


class ApplicationHealthService:
    """
    Deterministic rule engine calculating application health strictly per specifications:
    - Required checks (20 pts each):
        1. Job title present
        2. Company name present
        3. Resume attached (resume_id is not null)
        4. Current stage set
        5. Application date set
    - Penalty (-20 pts):
        Active application stale > 14 days without activity/updates
    - Suggestions (0 pts):
        1. Primary recruiter/contact linked
        2. Follow-up scheduled
        3. Notes added
    - Status values: EXCELLENT (>=90), GOOD (>=75), NEEDS_ATTENTION (>=50), POOR (<50)
    """

    @staticmethod
    def calculate_health(
        application: Application,
        followups: Optional[List[ApplicationFollowup]] = None,
        notes: Optional[List[ApplicationNote]] = None,
        activities: Optional[List[ApplicationActivity]] = None,
        as_of_time: Optional[datetime] = None,
    ) -> ApplicationHealthResponse:
        now = as_of_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        checks: List[ApplicationHealthCheck] = []
        score = 0

        # -------------------------------------------------------------------
        # 1. Required Checks (+20 points each)
        # -------------------------------------------------------------------
        # Check 1: Job title present
        has_title = bool(application.job_title and application.job_title.strip())
        score += 20 if has_title else 0
        checks.append(
            ApplicationHealthCheck(
                check_id="req_job_title",
                name="Job Title Specified",
                category="REQUIRED",
                passed=has_title,
                impact=20 if has_title else 0,
                message="Job title is specified." if has_title else "Missing job title.",
            )
        )

        # Check 2: Company name present
        has_company = bool(application.company_name and application.company_name.strip())
        score += 20 if has_company else 0
        checks.append(
            ApplicationHealthCheck(
                check_id="req_company_name",
                name="Company Name Specified",
                category="REQUIRED",
                passed=has_company,
                impact=20 if has_company else 0,
                message="Employer / company name is specified." if has_company else "Missing company name.",
            )
        )

        # Check 3: Resume attached
        has_resume = application.resume_id is not None
        score += 20 if has_resume else 0
        checks.append(
            ApplicationHealthCheck(
                check_id="req_resume_attached",
                name="Resume Version Attached",
                category="REQUIRED",
                passed=has_resume,
                impact=20 if has_resume else 0,
                message="Resume version is linked to this application." if has_resume else "No resume version linked to application.",
            )
        )

        # Check 4: Current stage set
        has_stage = bool(application.current_stage and application.current_stage.strip())
        score += 20 if has_stage else 0
        checks.append(
            ApplicationHealthCheck(
                check_id="req_current_stage",
                name="Current Stage Set",
                category="REQUIRED",
                passed=has_stage,
                impact=20 if has_stage else 0,
                message=f"Current recruitment stage is '{application.current_stage}'." if has_stage else "Missing recruitment stage.",
            )
        )

        # Check 5: Application date set
        has_date = application.applied_date is not None
        score += 20 if has_date else 0
        checks.append(
            ApplicationHealthCheck(
                check_id="req_applied_date",
                name="Application Date Set",
                category="REQUIRED",
                passed=has_date,
                impact=20 if has_date else 0,
                message=f"Application date recorded ({application.applied_date})." if has_date else "Missing application date.",
            )
        )

        # -------------------------------------------------------------------
        # 2. Staleness Penalty (-20 points if active and stale > 14 days)
        # -------------------------------------------------------------------
        is_active = (application.status == "ACTIVE")
        is_stale = False

        if is_active:
            timestamps = []
            if application.updated_at:
                app_updated = application.updated_at if application.updated_at.tzinfo else application.updated_at.replace(tzinfo=timezone.utc)
                timestamps.append(app_updated)
            if application.created_at:
                app_created = application.created_at if application.created_at.tzinfo else application.created_at.replace(tzinfo=timezone.utc)
                timestamps.append(app_created)
            if application.applied_date:
                applied_dt = datetime.combine(application.applied_date, datetime.min.time(), tzinfo=timezone.utc)
                timestamps.append(applied_dt)

            if activities:
                for act in activities:
                    if act.created_at:
                        act_dt = act.created_at if act.created_at.tzinfo else act.created_at.replace(tzinfo=timezone.utc)
                        timestamps.append(act_dt)

            if notes:
                for n in notes:
                    dt = n.updated_at or n.created_at
                    if dt:
                        dt_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                        timestamps.append(dt_aware)

            if followups:
                for f in followups:
                    dt = f.updated_at or f.created_at
                    if dt:
                        dt_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                        timestamps.append(dt_aware)

            if timestamps:
                latest_timestamp = max(timestamps)
                days_since_activity = (now - latest_timestamp).days
                if days_since_activity > 14:
                    is_stale = True

        if is_active and is_stale:
            score -= 20
            checks.append(
                ApplicationHealthCheck(
                    check_id="pen_stale_application",
                    name="Application Staleness Check",
                    category="PENALTY",
                    passed=False,
                    impact=-20,
                    message="Active application has had no updates, follow-ups, or activity for > 14 days.",
                )
            )
        else:
            checks.append(
                ApplicationHealthCheck(
                    check_id="pen_stale_application",
                    name="Application Staleness Check",
                    category="PENALTY",
                    passed=True,
                    impact=0,
                    message="Application is recently updated or not in active state.",
                )
            )

        # -------------------------------------------------------------------
        # 3. Actionable Suggestions (0 points impact)
        # -------------------------------------------------------------------
        # Suggestion 1: Primary recruiter / contact linked
        has_contact = application.contact_id is not None
        checks.append(
            ApplicationHealthCheck(
                check_id="sug_contact_linked",
                name="Primary Recruiter / Contact",
                category="SUGGESTION",
                passed=has_contact,
                impact=0,
                message="Primary recruiter / hiring manager is linked." if has_contact else "Recommendation: Link a recruiter or primary contact to track communications.",
            )
        )

        # Suggestion 2: Follow-up scheduled
        has_pending_followup = False
        if followups:
            today = now.date()
            for f in followups:
                if not f.is_completed:
                    has_pending_followup = True
                    break
                if f.due_date and f.due_date >= today:
                    has_pending_followup = True
                    break

        checks.append(
            ApplicationHealthCheck(
                check_id="sug_followup_scheduled",
                name="Follow-up Reminder Scheduled",
                category="SUGGESTION",
                passed=has_pending_followup,
                impact=0,
                message="Active follow-up reminder is scheduled." if has_pending_followup else "Recommendation: Schedule a follow-up reminder for this application.",
            )
        )

        # Suggestion 3: Notes added
        has_notes = bool(notes and len(notes) > 0)
        checks.append(
            ApplicationHealthCheck(
                check_id="sug_notes_added",
                name="Application Notes Added",
                category="SUGGESTION",
                passed=has_notes,
                impact=0,
                message=f"{len(notes)} tracking notes recorded." if has_notes else "Recommendation: Record debrief notes or interview impressions.",
            )
        )

        # -------------------------------------------------------------------
        # Final Score & Status Determination
        # -------------------------------------------------------------------
        final_score = max(0, min(100, score))

        if final_score >= 90:
            status = "EXCELLENT"
        elif final_score >= 75:
            status = "GOOD"
        elif final_score >= 50:
            status = "NEEDS_ATTENTION"
        else:
            status = "POOR"

        return ApplicationHealthResponse(
            score=final_score,
            status=status,
            checks=checks,
        )


application_health_service = ApplicationHealthService()
