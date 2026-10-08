"""
Settings Service — account management, security, session controls, GDPR export, and notifications.
Stage 9: Analytics & Settings.
Strict multi-user tenant isolation.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import hash_password, hash_token, verify_password
from app.models.application import (
    Application,
    ApplicationActivity,
    ApplicationDocument,
    ApplicationFollowup,
    ApplicationNote,
    ApplicationStageHistory,
)
from app.models.qa_vault import ApplicationAnswer, QAVaultEntry
from app.models.candidate_profile import CandidatePreferences, CandidateProfile
from app.models.company import Company
from app.models.contact import Contact
from app.models.document import Document
from app.models.interview import Interview, InterviewPreparation
from app.models.notification import Notification
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.profile_items import (
    Achievement,
    Certification,
    Education,
    Experience,
    Language,
    ProfileLink,
    Project,
    Skill,
)
from app.models.resume import Resume
from app.models.task import Task
from app.models.user import RefreshToken, User
from app.schemas.auth import SessionResponse
from app.schemas.settings import (
    AccountDetailsResponse,
    AccountUpdateRequest,
    DataExportResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)


class SettingsService:
    """Manages candidate account settings, sessions, security, and exports."""

    # -------------------------------------------------------------------------
    # Account Information
    # -------------------------------------------------------------------------

    async def get_account(self, db: AsyncSession, user_id: UUID) -> AccountDetailsResponse:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return AccountDetailsResponse.model_validate(user)

    async def update_account(
        self, db: AsyncSession, user_id: UUID, data: AccountUpdateRequest
    ) -> AccountDetailsResponse:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if data.username and data.username != user.username:
            conflict = await db.execute(
                select(User.id).where(User.username == data.username, User.id != user_id)
            )
            if conflict.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username is already taken by another account",
                )
            user.username = data.username

        if data.email and data.email != user.email:
            conflict = await db.execute(
                select(User.id).where(User.email == data.email, User.id != user_id)
            )
            if conflict.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already in use",
                )
            user.email = data.email

        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return AccountDetailsResponse.model_validate(user)

    # -------------------------------------------------------------------------
    # Password Management
    # -------------------------------------------------------------------------

    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New password must be at least 8 characters long",
            )

        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        # Invalidate all active sessions for security
        now = datetime.now(timezone.utc)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.commit()

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------

    async def list_sessions(
        self, db: AsyncSession, user_id: UUID, current_cookie: Optional[str]
    ) -> List[SessionResponse]:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.desc())
        )
        records = result.scalars().all()
        current_hash = hash_token(current_cookie) if current_cookie else None

        return [
            SessionResponse(
                id=r.id,
                created_at=r.created_at,
                expires_at=r.expires_at,
                user_agent=r.user_agent,
                ip_address=r.ip_address,
                is_current=(r.token_hash == current_hash),
            )
            for r in records
        ]

    async def revoke_session(
        self, db: AsyncSession, user_id: UUID, session_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.id == session_id,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already revoked",
            )
        record.revoked_at = now
        await db.commit()

    async def revoke_all_sessions(
        self, db: AsyncSession, user_id: UUID, current_cookie: Optional[str]
    ) -> int:
        now = datetime.now(timezone.utc)
        current_hash = hash_token(current_cookie) if current_cookie else None

        stmt = update(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        if current_hash:
            stmt = stmt.where(RefreshToken.token_hash != current_hash)

        stmt = stmt.values(revoked_at=now)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    # -------------------------------------------------------------------------
    # Notification Preferences
    # -------------------------------------------------------------------------

    async def get_notification_settings(
        self, db: AsyncSession, user_id: UUID
    ) -> NotificationSettingsResponse:
        res = await db.execute(
            select(CandidatePreferences).where(CandidatePreferences.user_id == user_id)
        )
        prefs = res.scalar_one_or_none()

        if prefs and prefs.notes:
            try:
                data = json.loads(prefs.notes)
                if isinstance(data, dict) and "notifications" in data:
                    n = data["notifications"]
                    return NotificationSettingsResponse(
                        in_app_alerts=n.get("in_app_alerts", True),
                        interview_reminders=n.get("interview_reminders", True),
                        deadline_reminders=n.get("deadline_reminders", True),
                        task_reminders=n.get("task_reminders", True),
                    )
            except Exception:
                pass

        return NotificationSettingsResponse(
            in_app_alerts=True,
            interview_reminders=True,
            deadline_reminders=True,
            task_reminders=True,
        )

    async def update_notification_settings(
        self, db: AsyncSession, user_id: UUID, data: NotificationSettingsUpdate
    ) -> NotificationSettingsResponse:
        res = await db.execute(
            select(CandidatePreferences).where(CandidatePreferences.user_id == user_id)
        )
        prefs = res.scalar_one_or_none()
        if not prefs:
            prefs = CandidatePreferences(user_id=user_id)
            db.add(prefs)
            await db.flush()

        current_notes: Dict[str, Any] = {}
        if prefs.notes:
            try:
                parsed = json.loads(prefs.notes)
                if isinstance(parsed, dict):
                    current_notes = parsed
            except Exception:
                current_notes = {}

        notifs = current_notes.get("notifications", {})
        if data.in_app_alerts is not None:
            notifs["in_app_alerts"] = data.in_app_alerts
        if data.interview_reminders is not None:
            notifs["interview_reminders"] = data.interview_reminders
        if data.deadline_reminders is not None:
            notifs["deadline_reminders"] = data.deadline_reminders
        if data.task_reminders is not None:
            notifs["task_reminders"] = data.task_reminders

        current_notes["notifications"] = notifs
        prefs.notes = json.dumps(current_notes)
        prefs.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return NotificationSettingsResponse(
            in_app_alerts=notifs.get("in_app_alerts", True),
            interview_reminders=notifs.get("interview_reminders", True),
            deadline_reminders=notifs.get("deadline_reminders", True),
            task_reminders=notifs.get("task_reminders", True),
        )

    # -------------------------------------------------------------------------
    # GDPR Complete Data Export
    # -------------------------------------------------------------------------

    async def export_user_data(
        self, db: AsyncSession, user_id: UUID
    ) -> DataExportResponse:
        # 1. User Account
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one()

        # 2. Profile & Preferences
        prof_res = await db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        )
        profile = prof_res.scalar_one_or_none()

        pref_res = await db.execute(
            select(CandidatePreferences).where(CandidatePreferences.user_id == user_id)
        )
        prefs = pref_res.scalar_one_or_none()

        # 3. Sub-profile entities
        edu = (await db.execute(select(Education).where(Education.user_id == user_id))).scalars().all()
        exp = (await db.execute(select(Experience).where(Experience.user_id == user_id))).scalars().all()
        proj = (await db.execute(select(Project).where(Project.user_id == user_id))).scalars().all()
        skills = (await db.execute(select(Skill).where(Skill.user_id == user_id))).scalars().all()
        certs = (await db.execute(select(Certification).where(Certification.user_id == user_id))).scalars().all()
        achievements = (await db.execute(select(Achievement).where(Achievement.user_id == user_id))).scalars().all()
        languages = (await db.execute(select(Language).where(Language.user_id == user_id))).scalars().all()
        links = (await db.execute(select(ProfileLink).where(ProfileLink.user_id == user_id))).scalars().all()

        # 4. Resumes & Documents
        resumes = (
            await db.execute(
                select(Resume).where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
            )
        ).scalars().all()
        documents = (
            await db.execute(
                select(Document).where(Document.user_id == user_id, Document.deleted_at.is_(None))
            )
        ).scalars().all()

        # 5. QA Vault
        qa_entries = (
            await db.execute(select(QAVaultEntry).where(QAVaultEntry.user_id == user_id))
        ).scalars().all()

        # 6. Applications & Sub-resources
        apps = (
            await db.execute(
                select(Application)
                .where(Application.user_id == user_id)
                .options(
                    selectinload(Application.stage_history),
                    selectinload(Application.notes),
                    selectinload(Application.followups),
                    selectinload(Application.answers),
                    selectinload(Application.activity),
                    selectinload(Application.documents),
                )
            )
        ).scalars().all()

        # 7. Opportunities & Saved Opportunities
        opps = (await db.execute(select(Opportunity).where(Opportunity.user_id == user_id))).scalars().all()
        saved_opps = (
            await db.execute(select(SavedOpportunity).where(SavedOpportunity.user_id == user_id))
        ).scalars().all()

        # 8. Interviews & Prep
        interviews = (
            await db.execute(
                select(Interview)
                .where(Interview.user_id == user_id)
                .options(selectinload(Interview.preparation))
            )
        ).scalars().all()

        # 9. Contacts & Companies
        contacts = (await db.execute(select(Contact).where(Contact.user_id == user_id))).scalars().all()
        companies = (await db.execute(select(Company).where(Company.user_id == user_id))).scalars().all()

        # 10. Tasks & Notifications
        tasks = (await db.execute(select(Task).where(Task.user_id == user_id))).scalars().all()
        notifs = (await db.execute(select(Notification).where(Notification.user_id == user_id))).scalars().all()

        bundle: Dict[str, Any] = {
            "account": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            },
            "profile": {
                "first_name": profile.first_name if profile else None,
                "last_name": profile.last_name if profile else None,
                "preferred_name": profile.preferred_name if profile else None,
                "phone": profile.phone if profile else None,
                "location_city": profile.location_city if profile else None,
                "location_state": profile.location_state if profile else None,
                "location_country": profile.location_country if profile else None,
                "timezone": profile.timezone if profile else None,
                "headline": profile.headline if profile else None,
                "summary": profile.professional_summary if profile else None,
                "career_objective": profile.career_objective if profile else None,
                "current_role": profile.current_role if profile else None,
                "total_experience_yrs": float(profile.total_experience_yrs) if profile and profile.total_experience_yrs else None,
                "notice_period_days": profile.notice_period_days if profile else None,
                "open_to_work": profile.open_to_work if profile else True,
                "website": profile.website if profile else None,
            },
            "preferences": {
                "desired_job_titles": prefs.desired_job_titles if prefs else None,
                "preferred_industries": prefs.preferred_industries if prefs else None,
                "preferred_locations": prefs.preferred_locations if prefs else None,
                "work_arrangement": prefs.work_arrangement if prefs else None,
                "employment_type": prefs.employment_type if prefs else None,
                "min_compensation": float(prefs.min_compensation) if prefs and prefs.min_compensation else None,
                "target_compensation": float(prefs.target_compensation) if prefs and prefs.target_compensation else None,
                "compensation_currency": prefs.compensation_currency if prefs else None,
            },
            "education": [
                {
                    "institution": e.institution,
                    "degree": e.degree,
                    "field_of_study": e.field_of_study,
                    "grade": e.grade,
                    "description": e.description,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "is_current": e.is_current,
                    "location": e.location,
                }
                for e in edu
            ],
            "experience": [
                {
                    "company": e.company_name,
                    "title": getattr(e, "title", getattr(e, "job_title", None)),
                    "employment_type": e.employment_type,
                    "location": e.location,
                    "location_type": e.location_type,
                    "description": e.description,
                    "responsibilities": e.responsibilities,
                    "achievements": e.achievements,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "is_current": e.is_current,
                }
                for e in exp
            ],
            "projects": [
                {
                    "name": getattr(e, "name", getattr(e, "title", None)),
                    "description": e.description,
                    "role": e.role,
                    "tech_stack": e.tech_stack,
                    "url": e.url,
                    "repo_url": e.repo_url,
                    "project_type": e.project_type,
                    "achievements": e.achievements,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "is_ongoing": e.is_ongoing,
                }
                for e in proj
            ],
            "skills": [
                {
                    "name": s.name,
                    "category": s.category,
                    "proficiency": s.proficiency,
                    "years_of_exp": float(s.years_of_exp) if s.years_of_exp else None,
                }
                for s in skills
            ],
            "certifications": [
                {
                    "name": c.name,
                    "issuer": getattr(c, "issuing_org", getattr(c, "issuing_organization", None)),
                    "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                    "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                    "credential_id": c.credential_id,
                    "credential_url": c.credential_url,
                    "description": c.description,
                }
                for c in certs
            ],
            "achievements": [
                {
                    "title": a.title,
                    "description": a.description,
                    "category": a.category,
                    "date": a.date.isoformat() if a.date else None,
                    "issuer": a.issuer,
                    "url": a.url,
                }
                for a in achievements
            ],
            "languages": [
                {
                    "name": l.name,
                    "proficiency": l.proficiency,
                }
                for l in languages
            ],
            "profile_links": [
                {
                    "platform": pl.platform,
                    "label": pl.label,
                    "url": pl.url,
                }
                for pl in links
            ],
            "resumes": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "original_filename": r.original_filename,
                    "version": r.version,
                    "is_default": r.is_default,
                    "file_size_bytes": r.file_size_bytes,
                    "mime_type": r.mime_type,
                    "uploaded_at": r.uploaded_at.isoformat(),
                }
                for r in resumes
            ],
            "documents": [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "doc_type": d.doc_type,
                    "original_filename": d.original_filename,
                    "version": d.version,
                    "file_size_bytes": d.file_size_bytes,
                    "mime_type": d.mime_type,
                    "description": d.description,
                    "uploaded_at": d.uploaded_at.isoformat(),
                }
                for d in documents
            ],
            "qa_vault": [
                {
                    "id": str(q.id),
                    "question": q.question,
                    "answer": q.answer,
                    "category": q.category,
                    "is_template": q.is_template,
                    "created_at": q.created_at.isoformat(),
                }
                for q in qa_entries
            ],
            "applications": [
                {
                    "id": str(a.id),
                    "job_title": a.job_title,
                    "company_name": a.company_name,
                    "current_stage": a.current_stage,
                    "status": a.status,
                    "priority": a.priority,
                    "outcome": a.outcome,
                    "applied_date": a.applied_date.isoformat() if a.applied_date else None,
                    "deadline_date": a.deadline_date.isoformat() if a.deadline_date else None,
                    "compensation_min": float(a.compensation_min) if a.compensation_min else None,
                    "compensation_max": float(a.compensation_max) if a.compensation_max else None,
                    "compensation_currency": a.compensation_currency,
                    "stage_history": [
                        {
                            "from": h.from_stage,
                            "to": h.to_stage,
                            "at": h.changed_at.isoformat(),
                            "notes": h.notes,
                        }
                        for h in a.stage_history
                    ],
                    "notes": [{"note": n.content, "at": n.created_at.isoformat()} for n in a.notes],
                    "followups": [
                        {
                            "due": f.due_date.isoformat() if f.due_date else None,
                            "note": f.note,
                            "is_completed": f.is_completed,
                            "completed_at": f.completed_at.isoformat() if f.completed_at else None,
                        }
                        for f in a.followups
                    ],
                    "answers": [
                        {
                            "id": str(ans.id),
                            "question": ans.question,
                            "answer": ans.answer,
                            "at": ans.created_at.isoformat(),
                        }
                        for ans in a.answers
                    ],
                    "activity": [
                        {
                            "id": str(act.id),
                            "event_type": act.event_type,
                            "description": act.description,
                            "at": act.created_at.isoformat(),
                        }
                        for act in a.activity
                    ],
                    "documents": [
                        {
                            "id": str(doc.id),
                            "document_id": str(doc.document_id),
                            "attached_at": doc.attached_at.isoformat(),
                        }
                        for doc in a.documents
                    ],
                }
                for a in apps
            ],
            "opportunities": [
                {
                    "id": str(o.id),
                    "title": o.title,
                    "company": o.company_name,
                    "status": o.status,
                    "location": o.location,
                    "source_url": o.source_url,
                    "source": o.source,
                    "description": o.description,
                    "compensation_min": float(o.compensation_min) if o.compensation_min else None,
                    "compensation_max": float(o.compensation_max) if o.compensation_max else None,
                    "compensation_currency": o.compensation_currency,
                    "created_at": o.created_at.isoformat(),
                }
                for o in opps
            ],
            "saved_opportunities": [
                {
                    "id": str(so.id),
                    "opportunity_id": str(so.opportunity_id),
                    "saved_at": so.saved_at.isoformat(),
                    "notes": so.notes,
                }
                for so in saved_opps
            ],
            "interviews": [
                {
                    "id": str(i.id),
                    "title": i.title or i.stage,
                    "type": i.interview_type,
                    "stage": i.stage,
                    "scheduled_at": i.scheduled_at.isoformat() if i.scheduled_at else None,
                    "duration_mins": i.duration_mins,
                    "status": i.status,
                    "result": i.result,
                    "location": i.location,
                    "meeting_link": i.meeting_link,
                    "interviewer_names": i.interviewer_names,
                    "notes": i.notes,
                    "preparation": (
                        {
                            "company_research": i.preparation.company_research,
                            "role_research": i.preparation.role_research,
                            "questions_to_ask": i.preparation.questions_to_ask,
                            "personal_notes": i.preparation.personal_notes,
                            "post_interview_notes": i.preparation.post_interview_notes,
                        }
                        if i.preparation
                        else None
                    ),
                }
                for i in interviews
            ],
            "contacts": [
                {
                    "id": str(c.id),
                    "name": f"{c.first_name} {c.last_name or ''}".strip(),
                    "email": c.email,
                    "phone": c.phone,
                    "role": c.role,
                    "notes": c.notes,
                }
                for c in contacts
            ],
            "companies": [
                {
                    "id": str(comp.id),
                    "name": comp.name,
                    "website": comp.website,
                    "industry": comp.industry,
                    "location": comp.location,
                    "notes": comp.notes,
                }
                for comp in companies
            ],
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "status": t.status,
                    "related_type": t.related_type,
                    "application_id": str(t.application_id) if t.application_id else None,
                    "interview_id": str(t.interview_id) if t.interview_id else None,
                    "company_id": str(t.company_id) if t.company_id else None,
                    "contact_id": str(t.contact_id) if t.contact_id else None,
                    "due": t.due_date.isoformat() if t.due_date else None,
                    "is_completed": t.is_completed,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                }
                for t in tasks
            ],
            "notifications": [
                {
                    "id": str(n.id),
                    "title": n.title,
                    "message": n.message,
                    "type": n.notification_type,
                    "is_read": n.is_read,
                    "at": n.created_at.isoformat(),
                }
                for n in notifs
            ],
        }

        return DataExportResponse(
            exported_at=datetime.now(timezone.utc),
            user_id=str(user.id),
            email=user.email,
            data=bundle,
        )

    # -------------------------------------------------------------------------
    # Account Deletion
    # -------------------------------------------------------------------------

    async def delete_account(
        self, db: AsyncSession, user_id: UUID, password: str
    ) -> None:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation failed. Account deletion aborted.",
            )

        # Cascading delete removes candidate profile, resumes, applications, interviews, contacts, etc.
        await db.delete(user)
        await db.commit()


settings_service = SettingsService()
