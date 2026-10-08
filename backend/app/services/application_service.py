"""
Application Service.
Stage 5 Master Implementation.
Orchestrates application lifecycle, pipeline Kanban, stage history, activity timelines,
notes, follow-ups, document attachments, Q&A answers, and health engine calculations.
All operations strictly enforce user ownership boundaries (user_id).
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.application import (
    Application,
    ApplicationActivity,
    ApplicationDocument,
    ApplicationFollowup,
    ApplicationNote,
    ApplicationStageHistory,
)
from app.models.contact import Contact
from app.models.document import Document
from app.models.opportunity import Opportunity
from app.models.qa_vault import ApplicationAnswer, QAVaultEntry
from app.models.resume import Resume
from app.schemas.contact import ContactSummary
from app.schemas.application import (
    ALLOWED_APPLICATION_STAGES,
    ApplicationConvertRequest,
    ApplicationCreate,
    ApplicationDocumentResponse,
    ApplicationFollowupCreate,
    ApplicationFollowupResponse,
    ApplicationFollowupUpdate,
    ApplicationFollowupWithAppResponse,
    ApplicationHealthResponse,
    ApplicationListResponse,
    ApplicationNoteCreate,
    ApplicationNoteResponse,
    ApplicationNoteUpdate,
    ApplicationResponse,
    ApplicationUpdate,
    DocumentMetaSummary,
    PipelineColumnResponse,
    PipelineResponse,
    ResumeSnapshotInfo,
    StageHistoryResponse,
    StageTransitionRequest,
    ApplicationActivityResponse,
)
from app.schemas.qa_vault import (
    ApplicationAnswerCreate,
    ApplicationAnswerResponse,
    ApplicationAnswerUpdate,
)
from app.services.application_health_service import application_health_service


STAGE_DISPLAY_NAMES = {
    "APPLIED": "Applied",
    "PHONE_SCREEN": "Phone Screen",
    "ASSESSMENT": "Assessment",
    "INTERVIEW": "Interview",
    "OFFER": "Offer",
    "ACCEPTED": "Accepted",
    "REJECTED": "Rejected",
    "WITHDRAWN": "Withdrawn",
}


class ApplicationService:

    # -----------------------------------------------------------------------
    # Helper / Validation
    # -----------------------------------------------------------------------

    async def _get_app_entity(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        load_relationships: bool = False,
    ) -> Application:
        """
        Fetch application by id and user_id.
        Raises NotFoundError if not found or owned by another user.
        """
        query = select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
        )
        if load_relationships:
            query = query.options(
                selectinload(Application.resume),
                selectinload(Application.contact).selectinload(Contact.company),
                selectinload(Application.notes),
                selectinload(Application.followups),
                selectinload(Application.documents).selectinload(ApplicationDocument.document),
                selectinload(Application.activity),
                selectinload(Application.stage_history),
                selectinload(Application.answers),
                selectinload(Application.interviews),
            )
        result = await db.execute(query)
        app = result.scalar_one_or_none()
        if not app:
            raise NotFoundError("Application not found")
        return app

    async def _validate_user_resume(
        self, db: AsyncSession, user_id: UUID, resume_id: Optional[UUID]
    ) -> Optional[Resume]:
        if not resume_id:
            return None
        res = await db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = res.scalar_one_or_none()
        if not resume:
            raise NotFoundError("Referenced resume not found or does not belong to user")
        return resume

    async def _validate_user_document(
        self, db: AsyncSession, user_id: UUID, doc_id: Optional[UUID]
    ) -> Optional[Document]:
        if not doc_id:
            return None
        res = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        )
        doc = res.scalar_one_or_none()
        if not doc:
            raise NotFoundError("Referenced document not found or does not belong to user")
        return doc

    async def _validate_user_contact(
        self, db: AsyncSession, user_id: UUID, contact_id: Optional[UUID]
    ) -> Optional[Contact]:
        if not contact_id:
            return None
        res = await db.execute(
            select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Referenced contact not found or does not belong to user")
        return contact

    def _build_response(
        self,
        app: Application,
        health: Optional[ApplicationHealthResponse] = None,
    ) -> ApplicationResponse:
        insp = inspect(app)

        resume_snapshot = None
        if "resume" not in insp.unloaded and app.resume:
            resume_snapshot = ResumeSnapshotInfo(
                id=app.resume.id,
                name=app.resume.name or "Resume",
                original_filename=app.resume.original_filename,
                version=app.resume.version or 1,
            )

        contact_snapshot = None
        if "contact" not in insp.unloaded and app.contact:
            company_name_val = None
            if "company" not in inspect(app.contact).unloaded and app.contact.company:
                company_name_val = app.contact.company.name
            contact_snapshot = ContactSummary(
                id=app.contact.id,
                first_name=app.contact.first_name,
                last_name=app.contact.last_name,
                role=app.contact.role,
                contact_type=app.contact.contact_type,
                email=app.contact.email,
                company_name=company_name_val,
            )

        notes_cnt = len(app.notes) if "notes" not in insp.unloaded and app.notes else 0
        followups_cnt = len(app.followups) if "followups" not in insp.unloaded and app.followups else 0
        docs_cnt = len(app.documents) if "documents" not in insp.unloaded and app.documents else 0
        interviews_cnt = len(app.interviews) if "interviews" not in insp.unloaded and app.interviews else 0

        return ApplicationResponse(
            id=app.id,
            user_id=app.user_id,
            job_title=app.job_title,
            company_name=app.company_name,
            company_id=app.company_id,
            opportunity_id=app.opportunity_id,
            job_posting_id=getattr(app, "job_posting_id", None),
            contact_id=app.contact_id,
            job_location=app.job_location,
            job_location_type=app.job_location_type,
            employment_type=app.employment_type,
            job_description=app.job_description,
            job_url=app.job_url,
            compensation_min=app.compensation_min,
            compensation_max=app.compensation_max,
            compensation_currency=app.compensation_currency,
            source=app.source,
            status=app.status,
            current_stage=app.current_stage,
            applied_date=app.applied_date,
            deadline_date=app.deadline_date,
            resume_id=app.resume_id,
            cover_letter_doc_id=app.cover_letter_doc_id,
            priority=app.priority,
            outcome=app.outcome,
            created_at=app.created_at,
            updated_at=app.updated_at,
            resume=resume_snapshot,
            contact=contact_snapshot,
            health=health,
            notes_count=notes_cnt,
            followups_count=followups_cnt,
            documents_count=docs_cnt,
            interviews_count=interviews_cnt,
        )

    # -----------------------------------------------------------------------
    # Application CRUD
    # -----------------------------------------------------------------------

    async def create_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: ApplicationCreate,
    ) -> ApplicationResponse:
        # Validate foreign keys belong to user
        if data.opportunity_id:
            opp_res = await db.execute(
                select(Opportunity).where(
                    Opportunity.id == data.opportunity_id,
                    Opportunity.user_id == user_id,
                )
            )
            if not opp_res.scalar_one_or_none():
                raise NotFoundError("Referenced opportunity not found or does not belong to user")

        if data.resume_id:
            await self._validate_user_resume(db, user_id, data.resume_id)

        if data.cover_letter_doc_id:
            await self._validate_user_document(db, user_id, data.cover_letter_doc_id)

        if data.contact_id:
            await self._validate_user_contact(db, user_id, data.contact_id)

        applied_date_val = data.applied_date

        app = Application(
            user_id=user_id,
            company_id=data.company_id,
            opportunity_id=data.opportunity_id,
            contact_id=data.contact_id,
            job_title=data.job_title,
            company_name=data.company_name,
            job_location=data.job_location,
            job_location_type=data.job_location_type,
            employment_type=data.employment_type,
            job_description=data.job_description,
            job_url=data.job_url,
            compensation_min=data.compensation_min,
            compensation_max=data.compensation_max,
            compensation_currency=data.compensation_currency or "USD",
            source=data.source or "MANUAL",
            status=data.status or "ACTIVE",
            current_stage=data.current_stage or "APPLIED",
            applied_date=applied_date_val,
            deadline_date=data.deadline_date,
            resume_id=data.resume_id,
            cover_letter_doc_id=data.cover_letter_doc_id,
            priority=data.priority or "MEDIUM",
            outcome=data.outcome,
        )
        db.add(app)
        await db.flush()

        # Initial append-only stage history
        stage_history = ApplicationStageHistory(
            application_id=app.id,
            from_stage=None,
            to_stage=app.current_stage,
            notes="Application created",
            changed_by_user=user_id,
        )
        db.add(stage_history)

        # Initial append-only activity
        activity = ApplicationActivity(
            application_id=app.id,
            user_id=user_id,
            event_type="APPLICATION_CREATED",
            description=f"Created application for {app.job_title} at {app.company_name}",
            event_data={"stage": app.current_stage, "applied_date": str(applied_date_val) if applied_date_val else None},
        )

        db.add(activity)

        # Initial note if provided
        if data.initial_notes and data.initial_notes.strip():
            note = ApplicationNote(
                application_id=app.id,
                user_id=user_id,
                content=data.initial_notes.strip(),
            )
            db.add(note)

        await db.commit()

        # Reload with relationships
        full_app = await self._get_app_entity(db, user_id, app.id, load_relationships=True)
        health = application_health_service.calculate_health(
            application=full_app,
            followups=full_app.followups,
            notes=full_app.notes,
            activities=full_app.activity,
        )
        return self._build_response(full_app, health=health)

    async def convert_opportunity_to_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        opportunity_id: UUID,
        data: ApplicationConvertRequest,
    ) -> ApplicationResponse:
        """
        Convert an Opportunity into an active Application.
        Snapshots job details.
        CRITICAL: Does NOT alter Opportunity.status to APPLIED.
        """
        res = await db.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.user_id == user_id,
            )
        )
        opp = res.scalar_one_or_none()
        if not opp:
            raise NotFoundError("Opportunity not found")

        app_create = ApplicationCreate(
            job_title=opp.title,
            company_name=opp.company_name or "Company",
            company_id=opp.company_id,
            opportunity_id=opp.id,
            contact_id=None,
            job_location=opp.location,
            job_location_type=opp.location_type,
            employment_type=opp.employment_type,
            job_description=opp.description,
            job_url=opp.source_url,
            compensation_min=opp.compensation_min,
            compensation_max=opp.compensation_max,
            compensation_currency=opp.compensation_currency,
            source=opp.source or "OPPORTUNITY_CONVERT",
            status="ACTIVE",
            current_stage=data.current_stage or "APPLIED",
            applied_date=data.applied_date or date.today(),
            resume_id=data.resume_id,
            cover_letter_doc_id=data.cover_letter_doc_id,
            priority=data.priority or "MEDIUM",
            initial_notes=data.initial_notes or opp.notes,
        )

        # Do NOT modify opp.status to APPLIED. Keep opportunity untouched.
        return await self.create_application(db=db, user_id=user_id, data=app_create)

    async def list_applications(
        self,
        db: AsyncSession,
        user_id: UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ApplicationListResponse:
        base_query = select(Application).where(Application.user_id == user_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Application.job_title.ilike(term),
                    Application.company_name.ilike(term),
                    Application.job_location.ilike(term),
                )
            )

        if status:
            base_query = base_query.where(Application.status == status)
        if stage:
            base_query = base_query.where(Application.current_stage == stage)
        if priority:
            base_query = base_query.where(Application.priority == priority)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Sorting
        sort_col = getattr(Application, sort_by, Application.created_at)
        if sort_order.lower() == "desc":
            base_query = base_query.order_by(sort_col.desc())
        else:
            base_query = base_query.order_by(sort_col.asc())

        # Pagination & Eager Loading
        offset = (page - 1) * page_size
        query = (
            base_query.offset(offset)
            .limit(page_size)
            .options(
                selectinload(Application.resume),
                selectinload(Application.contact).selectinload(Contact.company),
                selectinload(Application.notes),
                selectinload(Application.followups),
                selectinload(Application.documents),
                selectinload(Application.activity),
                selectinload(Application.interviews),
            )
        )
        result = await db.execute(query)
        apps = result.scalars().all()

        items = []
        for app in apps:
            health = application_health_service.calculate_health(
                application=app,
                followups=app.followups,
                notes=app.notes,
                activities=app.activity,
            )
            items.append(self._build_response(app, health=health))

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return ApplicationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationResponse:
        app = await self._get_app_entity(db, user_id, application_id, load_relationships=True)
        health = application_health_service.calculate_health(
            application=app,
            followups=app.followups,
            notes=app.notes,
            activities=app.activity,
        )
        return self._build_response(app, health=health)

    async def update_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        data: ApplicationUpdate,
    ) -> ApplicationResponse:
        app = await self._get_app_entity(db, user_id, application_id, load_relationships=True)

        if data.resume_id:
            await self._validate_user_resume(db, user_id, data.resume_id)
        if data.cover_letter_doc_id:
            await self._validate_user_document(db, user_id, data.cover_letter_doc_id)
        if data.contact_id:
            await self._validate_user_contact(db, user_id, data.contact_id)

        update_dict = data.model_dump(exclude_unset=True)

        # Stage change via update_application triggers history & activity
        if "current_stage" in update_dict and update_dict["current_stage"] != app.current_stage:
            if app.job_posting_id is not None and update_dict["current_stage"] != "WITHDRAWN":
                raise ForbiddenError(
                    "Recruitment stage for platform applications is managed by the employer. Candidates may only withdraw."
                )
            return await self.transition_stage(
                db=db,
                user_id=user_id,
                application_id=application_id,
                data=StageTransitionRequest(
                    to_stage=update_dict["current_stage"],
                    notes="Stage updated via application edit",
                ),
            )

        for field, value in update_dict.items():
            setattr(app, field, value)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(app)

        health = application_health_service.calculate_health(
            application=app,
            followups=app.followups,
            notes=app.notes,
            activities=app.activity,
        )
        return self._build_response(app, health=health)

    async def delete_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> None:
        app = await self._get_app_entity(db, user_id, application_id)
        if app.job_posting_id is not None:
            raise ValidationError(
                "Platform job applications cannot be permanently deleted. Please withdraw the application instead."
            )
        await db.delete(app)
        await db.commit()

    # -----------------------------------------------------------------------
    # Stage Transitions & History
    # -----------------------------------------------------------------------

    async def transition_stage(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        data: StageTransitionRequest,
    ) -> ApplicationResponse:
        """
        Transition application stage.
        Appends immutable stage history and activity record.
        """
        app = await self._get_app_entity(db, user_id, application_id, load_relationships=True)

        # Platform application: candidate cannot advance recruitment stages, only withdraw
        if app.job_posting_id is not None and data.to_stage != "WITHDRAWN":
            raise ForbiddenError(
                "Recruitment stage for platform applications is managed by the employer. Candidates may only withdraw."
            )

        from_stage = app.current_stage
        to_stage = data.to_stage

        app.current_stage = to_stage

        # Terminal stage handling
        if to_stage in {"ACCEPTED", "REJECTED", "WITHDRAWN"}:
            app.status = "CLOSED"
            app.outcome = to_stage
        elif app.status == "CLOSED" and to_stage in {"APPLIED", "PHONE_SCREEN", "ASSESSMENT", "INTERVIEW", "OFFER"}:
            app.status = "ACTIVE"
            app.outcome = None

        app.updated_at = datetime.now(timezone.utc)

        # Append immutable history
        history = ApplicationStageHistory(
            application_id=app.id,
            from_stage=from_stage,
            to_stage=to_stage,
            notes=data.notes,
            changed_by_user=user_id,
        )
        db.add(history)

        # Append activity
        activity = ApplicationActivity(
            application_id=app.id,
            user_id=user_id,
            event_type="STAGE_CHANGED",
            description=f"Recruitment stage changed from {from_stage} to {to_stage}",
            event_data={"from_stage": from_stage, "to_stage": to_stage, "notes": data.notes},
        )
        db.add(activity)

        await db.commit()
        await db.refresh(app)

        health = application_health_service.calculate_health(
            application=app,
            followups=app.followups,
            notes=app.notes,
            activities=app.activity,
        )
        return self._build_response(app, health=health)

    async def list_stage_history(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[StageHistoryResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationStageHistory)
            .where(ApplicationStageHistory.application_id == application_id)
            .order_by(ApplicationStageHistory.changed_at.asc())
        )
        res = await db.execute(query)
        items = res.scalars().all()
        responses = []
        for item in items:
            sh = StageHistoryResponse.model_validate(item)
            # Redact recruiter internal evaluation notes from candidate view
            if item.changed_by_user is not None and item.changed_by_user != user_id:
                sh.notes = None
            responses.append(sh)
        return responses

    async def list_activity(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationActivityResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationActivity)
            .where(
                ApplicationActivity.application_id == application_id,
                ApplicationActivity.user_id == user_id,
            )
            .order_by(ApplicationActivity.created_at.desc())
        )
        res = await db.execute(query)
        items = res.scalars().all()
        return [ApplicationActivityResponse.model_validate(item) for item in items]

    # -----------------------------------------------------------------------
    # Pipeline (Kanban)
    # -----------------------------------------------------------------------

    async def get_pipeline(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> PipelineResponse:
        """
        Group active applications by recruitment stage for Kanban board.
        """
        query = (
            select(Application)
            .where(
                Application.user_id == user_id,
                Application.status == "ACTIVE",
            )
            .options(
                selectinload(Application.resume),
                selectinload(Application.contact).selectinload(Contact.company),
                selectinload(Application.notes),
                selectinload(Application.followups),
                selectinload(Application.documents),
                selectinload(Application.activity),
                selectinload(Application.interviews),
            )
            .order_by(Application.created_at.desc())
        )
        res = await db.execute(query)
        apps = res.scalars().all()

        stage_buckets: Dict[str, List[ApplicationResponse]] = {
            stage: [] for stage in [
                "APPLIED",
                "PHONE_SCREEN",
                "ASSESSMENT",
                "INTERVIEW",
                "OFFER",
                "ACCEPTED",
                "REJECTED",
                "WITHDRAWN",
            ]
        }

        total_active = len(apps)
        for app in apps:
            health = application_health_service.calculate_health(
                application=app,
                followups=app.followups,
                notes=app.notes,
                activities=app.activity,
            )
            resp = self._build_response(app, health=health)
            if app.current_stage in stage_buckets:
                stage_buckets[app.current_stage].append(resp)
            else:
                stage_buckets["APPLIED"].append(resp)

        columns = [
            PipelineColumnResponse(
                stage=stage,
                name=STAGE_DISPLAY_NAMES.get(stage, stage),
                count=len(items),
                items=items,
            )
            for stage, items in stage_buckets.items()
        ]

        return PipelineResponse(columns=columns, total_active=total_active)

    # -----------------------------------------------------------------------
    # Application Notes
    # -----------------------------------------------------------------------

    async def list_notes(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationNoteResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationNote)
            .where(
                ApplicationNote.application_id == application_id,
                ApplicationNote.user_id == user_id,
            )
            .order_by(ApplicationNote.created_at.desc())
        )
        res = await db.execute(query)
        items = res.scalars().all()
        return [ApplicationNoteResponse.model_validate(item) for item in items]

    async def create_note(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        data: ApplicationNoteCreate,
    ) -> ApplicationNoteResponse:
        app = await self._get_app_entity(db, user_id, application_id)

        note = ApplicationNote(
            application_id=application_id,
            user_id=user_id,
            content=data.content,
        )
        db.add(note)

        # Activity
        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type="NOTE_ADDED",
            description=f"Added tracking note: {data.content[:60]}...",
        )
        db.add(activity)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(note)
        return ApplicationNoteResponse.model_validate(note)

    async def update_note(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        note_id: UUID,
        data: ApplicationNoteUpdate,
    ) -> ApplicationNoteResponse:
        await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationNote).where(
                ApplicationNote.id == note_id,
                ApplicationNote.application_id == application_id,
                ApplicationNote.user_id == user_id,
            )
        )
        note = res.scalar_one_or_none()
        if not note:
            raise NotFoundError("Note not found")

        note.content = data.content
        note.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(note)
        return ApplicationNoteResponse.model_validate(note)

    async def delete_note(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        note_id: UUID,
    ) -> None:
        await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationNote).where(
                ApplicationNote.id == note_id,
                ApplicationNote.application_id == application_id,
                ApplicationNote.user_id == user_id,
            )
        )
        note = res.scalar_one_or_none()
        if not note:
            raise NotFoundError("Note not found")

        await db.delete(note)
        await db.commit()

    # -----------------------------------------------------------------------
    # Application Follow-ups
    # -----------------------------------------------------------------------

    async def list_followups(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationFollowupResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationFollowup)
            .where(
                ApplicationFollowup.application_id == application_id,
                ApplicationFollowup.user_id == user_id,
            )
            .order_by(ApplicationFollowup.due_date.asc().nulls_last())
        )
        res = await db.execute(query)
        items = res.scalars().all()
        return [ApplicationFollowupResponse.model_validate(item) for item in items]

    async def create_followup(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        data: ApplicationFollowupCreate,
    ) -> ApplicationFollowupResponse:
        app = await self._get_app_entity(db, user_id, application_id)

        followup = ApplicationFollowup(
            application_id=application_id,
            user_id=user_id,
            due_date=data.due_date,
            note=data.note,
            is_completed=False,
        )
        db.add(followup)

        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type="FOLLOWUP_CREATED",
            description=f"Scheduled follow-up reminder for {data.due_date or 'unspecified date'}",
        )
        db.add(activity)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(followup)
        return ApplicationFollowupResponse.model_validate(followup)

    async def update_followup(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        followup_id: UUID,
        data: ApplicationFollowupUpdate,
    ) -> ApplicationFollowupResponse:
        app = await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationFollowup).where(
                ApplicationFollowup.id == followup_id,
                ApplicationFollowup.application_id == application_id,
                ApplicationFollowup.user_id == user_id,
            )
        )
        fol = res.scalar_one_or_none()
        if not fol:
            raise NotFoundError("Follow-up not found")

        update_data = data.model_dump(exclude_unset=True)

        if "is_completed" in update_data:
            new_completed = update_data["is_completed"]
            if new_completed and not fol.is_completed:
                fol.completed_at = datetime.now(timezone.utc)
                db.add(
                    ApplicationActivity(
                        application_id=application_id,
                        user_id=user_id,
                        event_type="FOLLOWUP_COMPLETED",
                        description=f"Completed follow-up: {fol.note or 'Follow-up'}",
                    )
                )
            elif not new_completed:
                fol.completed_at = None

        for field, value in update_data.items():
            setattr(fol, field, value)

        fol.updated_at = datetime.now(timezone.utc)
        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(fol)
        return ApplicationFollowupResponse.model_validate(fol)

    async def delete_followup(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        followup_id: UUID,
    ) -> None:
        await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationFollowup).where(
                ApplicationFollowup.id == followup_id,
                ApplicationFollowup.application_id == application_id,
                ApplicationFollowup.user_id == user_id,
            )
        )
        fol = res.scalar_one_or_none()
        if not fol:
            raise NotFoundError("Follow-up not found")

        await db.delete(fol)
        await db.commit()

    async def list_all_user_followups(
        self,
        db: AsyncSession,
        user_id: UUID,
        is_completed: Optional[bool] = None,
    ) -> List[ApplicationFollowupWithAppResponse]:
        """
        Global follow-ups queue across all user applications.
        """
        query = (
            select(ApplicationFollowup, Application)
            .join(Application, ApplicationFollowup.application_id == Application.id)
            .where(ApplicationFollowup.user_id == user_id)
        )
        if is_completed is not None:
            query = query.where(ApplicationFollowup.is_completed == is_completed)

        query = query.order_by(ApplicationFollowup.due_date.asc().nulls_last())

        res = await db.execute(query)
        rows = res.all()

        results = []
        for fol, app in rows:
            item = ApplicationFollowupWithAppResponse(
                id=fol.id,
                application_id=fol.application_id,
                user_id=fol.user_id,
                due_date=fol.due_date,
                note=fol.note,
                is_completed=fol.is_completed,
                completed_at=fol.completed_at,
                created_at=fol.created_at,
                updated_at=fol.updated_at,
                job_title=app.job_title,
                company_name=app.company_name,
                current_stage=app.current_stage,
                application_status=app.status,
            )
            results.append(item)
        return results

    # -----------------------------------------------------------------------
    # Application Documents
    # -----------------------------------------------------------------------

    async def list_documents(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationDocumentResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application_id)
            .options(selectinload(ApplicationDocument.document))
            .order_by(ApplicationDocument.attached_at.desc())
        )
        res = await db.execute(query)
        items = res.scalars().all()

        results = []
        for item in items:
            doc_summary = None
            if item.document:
                doc_summary = DocumentMetaSummary(
                    id=item.document.id,
                    name=item.document.name or "Document",
                    original_filename=item.document.original_filename,
                    doc_type=item.document.doc_type or "OTHER",
                    file_size_bytes=item.document.file_size_bytes or 0,
                )
            results.append(
                ApplicationDocumentResponse(
                    id=item.id,
                    application_id=item.application_id,
                    document_id=item.document_id,
                    attached_at=item.attached_at,
                    document=doc_summary,
                )
            )
        return results

    async def attach_document(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        document_id: UUID,
    ) -> ApplicationDocumentResponse:
        app = await self._get_app_entity(db, user_id, application_id)
        doc = await self._validate_user_document(db, user_id, document_id)

        # Check existing
        existing = await db.execute(
            select(ApplicationDocument).where(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.document_id == document_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Document is already attached to this application")

        app_doc = ApplicationDocument(
            application_id=application_id,
            document_id=document_id,
        )
        db.add(app_doc)

        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type="DOCUMENT_ATTACHED",
            description=f"Attached document: {doc.original_filename if doc else 'Document'}",
        )
        db.add(activity)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(app_doc)

        doc_summary = None
        if doc:
            doc_summary = DocumentMetaSummary(
                id=doc.id,
                name=doc.name or "Document",
                original_filename=doc.original_filename,
                doc_type=doc.doc_type or "OTHER",
                file_size_bytes=doc.file_size_bytes or 0,
            )

        return ApplicationDocumentResponse(
            id=app_doc.id,
            application_id=app_doc.application_id,
            document_id=app_doc.document_id,
            attached_at=app_doc.attached_at,
            document=doc_summary,
        )

    async def detach_document(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        document_id: UUID,
    ) -> None:
        app = await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationDocument).where(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.document_id == document_id,
            )
        )
        app_doc = res.scalar_one_or_none()
        if not app_doc:
            raise NotFoundError("Attached document not found")

        await db.delete(app_doc)

        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type="DOCUMENT_DETACHED",
            description="Detached document from application",
        )
        db.add(activity)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()

    # -----------------------------------------------------------------------
    # Application Q&A Answers
    # -----------------------------------------------------------------------

    async def list_answers(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationAnswerResponse]:
        await self._get_app_entity(db, user_id, application_id)
        query = (
            select(ApplicationAnswer)
            .where(ApplicationAnswer.application_id == application_id)
            .order_by(ApplicationAnswer.created_at.asc())
        )
        res = await db.execute(query)
        items = res.scalars().all()
        return [ApplicationAnswerResponse.model_validate(item) for item in items]

    async def create_answer(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        data: ApplicationAnswerCreate,
    ) -> ApplicationAnswerResponse:
        app = await self._get_app_entity(db, user_id, application_id)

        if data.qa_vault_entry_id:
            vault_res = await db.execute(
                select(QAVaultEntry).where(
                    QAVaultEntry.id == data.qa_vault_entry_id,
                    QAVaultEntry.user_id == user_id,
                )
            )
            if not vault_res.scalar_one_or_none():
                raise NotFoundError("Referenced Q&A Vault template not found")

        answer = ApplicationAnswer(
            application_id=application_id,
            qa_vault_entry_id=data.qa_vault_entry_id,
            question=data.question,
            answer=data.answer,
        )
        db.add(answer)

        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type="ANSWER_ADDED",
            description=f"Recorded application response for: {data.question[:50]}...",
        )
        db.add(activity)

        app.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(answer)
        return ApplicationAnswerResponse.model_validate(answer)

    async def update_answer(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        answer_id: UUID,
        data: ApplicationAnswerUpdate,
    ) -> ApplicationAnswerResponse:
        await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationAnswer).where(
                ApplicationAnswer.id == answer_id,
                ApplicationAnswer.application_id == application_id,
            )
        )
        ans = res.scalar_one_or_none()
        if not ans:
            raise NotFoundError("Answer record not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ans, field, value)

        ans.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(ans)
        return ApplicationAnswerResponse.model_validate(ans)

    async def delete_answer(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        answer_id: UUID,
    ) -> None:
        await self._get_app_entity(db, user_id, application_id)
        res = await db.execute(
            select(ApplicationAnswer).where(
                ApplicationAnswer.id == answer_id,
                ApplicationAnswer.application_id == application_id,
            )
        )
        ans = res.scalar_one_or_none()
        if not ans:
            raise NotFoundError("Answer record not found")

        await db.delete(ans)
        await db.commit()

    # -----------------------------------------------------------------------
    # Health Calculation
    # -----------------------------------------------------------------------

    async def get_application_health(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationHealthResponse:
        app = await self._get_app_entity(db, user_id, application_id, load_relationships=True)
        return application_health_service.calculate_health(
            application=app,
            followups=app.followups,
            notes=app.notes,
            activities=app.activity,
        )


application_service = ApplicationService()
