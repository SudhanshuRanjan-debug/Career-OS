"""
Job Posting Service — recruiter postings lifecycle and candidate public discovery.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.application import (
    Application,
    ApplicationActivity,
    ApplicationNote,
    ApplicationStageHistory,
)
from app.models.candidate_profile import CandidateProfile
from app.models.document import Document
from app.models.job_posting import JobPosting, JobPostingSkill
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.organization import Organization
from app.models.resume import Resume
from app.models.user import User
from app.schemas.application import (
    ApplicationNoteResponse,
    ApplicationResponse,
    CandidateApplicationSummary,
    JobApplyRequest,
    RecruiterApplicantDetailResponse,
    RecruiterApplicantListItem,
    ResumeSnapshotInfo,
    StageHistoryResponse,
    StageTransitionRequest,
)
from app.schemas.job_posting import (
    JobPostingCreate,
    JobPostingDetailResponse,
    JobPostingResponse,
    JobPostingSkillResponse,
    JobPostingUpdate,
)
from app.schemas.organization import OrganizationResponse


class JobPostingService:

    async def _get_recruiter_organization(self, db: AsyncSession, recruiter_user_id: UUID) -> Organization:
        """Find the recruiter's organization; raises NotFoundError if none."""
        stmt = select(Organization).where(Organization.owner_user_id == recruiter_user_id)
        res = await db.execute(stmt)
        org = res.scalar_one_or_none()
        if not org:
            raise NotFoundError("Recruiter organization profile not found")
        return org

    # =========================================================================
    # Recruiter Operations
    # =========================================================================

    async def list_recruiter_jobs(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List job postings for the authenticated recruiter's organization."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        query = (
            select(JobPosting)
            .where(JobPosting.organization_id == org.id)
            .options(selectinload(JobPosting.skills))
        )

        if status:
            query = query.where(JobPosting.status == status.upper())

        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    JobPosting.title.ilike(s),
                    JobPosting.description.ilike(s),
                    JobPosting.location.ilike(s),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        # Order and paginate
        query = (
            query.order_by(JobPosting.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db.execute(query)
        postings = list(res.scalars().all())

        # Fetch applicant counts per job posting
        job_ids = [p.id for p in postings]
        applicant_counts: dict[UUID, int] = {}
        if job_ids:
            counts_stmt = (
                select(Application.job_posting_id, func.count(Application.id))
                .where(Application.job_posting_id.in_(job_ids))
                .group_by(Application.job_posting_id)
            )
            count_rows = (await db.execute(counts_stmt)).all()
            for jid, cnt in count_rows:
                applicant_counts[jid] = cnt

        items = []
        for p in postings:
            resp = JobPostingResponse.model_validate(p)
            resp.organization_name = org.name
            resp.applicant_count = applicant_counts.get(p.id, 0)
            items.append(resp)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def create_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        data: JobPostingCreate,
    ) -> JobPostingResponse:
        """Create a new job posting in DRAFT status for recruiter's organization."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)
        now = datetime.now(timezone.utc)

        posting = JobPosting(
            organization_id=org.id,
            created_by_user_id=recruiter_user_id,
            title=data.title,
            description=data.description,
            requirements=data.requirements,
            location=data.location,
            location_type=data.location_type,
            employment_type=data.employment_type,
            experience_level=data.experience_level,
            compensation_min=data.compensation_min,
            compensation_max=data.compensation_max,
            compensation_currency=data.compensation_currency,
            deadline_date=data.deadline_date,
            status="DRAFT",
            created_at=now,
            updated_at=now,
        )
        db.add(posting)
        await db.flush()

        # Add skills
        unique_skills = set(s.strip() for s in data.skills if s.strip())
        for skill_name in sorted(unique_skills):
            db.add(JobPostingSkill(job_posting_id=posting.id, name=skill_name))

        await db.commit()

        # Reload with relationships
        return await self.get_recruiter_job_posting(db, recruiter_user_id, posting.id)

    async def get_recruiter_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
    ) -> JobPostingResponse:
        """Get single job posting ensuring recruiter ownership."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
            .options(selectinload(JobPosting.skills))
        )
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        # Count applicants
        cnt_stmt = select(func.count(Application.id)).where(Application.job_posting_id == job_id)
        cnt = (await db.execute(cnt_stmt)).scalar_one()

        resp = JobPostingResponse.model_validate(posting)
        resp.organization_name = org.name
        resp.applicant_count = cnt
        return resp

    async def update_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
        data: JobPostingUpdate,
    ) -> JobPostingResponse:
        """Update job posting details and skills."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
            .options(selectinload(JobPosting.skills))
        )
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        if posting.status == "ARCHIVED":
            raise ValidationError("Archived job postings cannot be edited")

        update_dict = data.model_dump(exclude_unset=True)
        skills_data = update_dict.pop("skills", None)

        for field, value in update_dict.items():
            setattr(posting, field, value)

        # Replace skills if explicitly supplied
        if skills_data is not None:
            # Delete old skills
            del_stmt = select(JobPostingSkill).where(JobPostingSkill.job_posting_id == job_id)
            old_skills = (await db.execute(del_stmt)).scalars().all()
            for os in old_skills:
                await db.delete(os)
            await db.flush()

            # Insert new skills
            unique_skills = set(s.strip() for s in skills_data if s.strip())
            for skill_name in sorted(unique_skills):
                db.add(JobPostingSkill(job_posting_id=job_id, name=skill_name))

        posting.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return await self.get_recruiter_job_posting(db, recruiter_user_id, job_id)

    async def publish_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
    ) -> JobPostingResponse:
        """Transition job posting to PUBLISHED."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)
        stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        if posting.status == "ARCHIVED":
            raise ValidationError("Archived job postings cannot be republished")

        now = datetime.now(timezone.utc)
        posting.status = "PUBLISHED"
        if not posting.published_at:
            posting.published_at = now
        posting.updated_at = now

        await db.commit()
        return await self.get_recruiter_job_posting(db, recruiter_user_id, job_id)

    async def close_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
    ) -> JobPostingResponse:
        """Transition job posting to CLOSED (no new applications accepted)."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)
        stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        if posting.status == "ARCHIVED":
            raise ValidationError("Archived job postings cannot be closed")

        posting.status = "CLOSED"
        posting.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await self.get_recruiter_job_posting(db, recruiter_user_id, job_id)

    async def archive_job_posting(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
    ) -> JobPostingResponse:
        """Transition job posting to ARCHIVED."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)
        stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        posting.status = "ARCHIVED"
        posting.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await self.get_recruiter_job_posting(db, recruiter_user_id, job_id)

    # =========================================================================
    # Candidate & Public Discovery Operations
    # =========================================================================

    async def list_published_jobs(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        location: Optional[str] = None,
        location_type: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        skill: Optional[str] = None,
        min_compensation: Optional[Decimal] = None,
        currency: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Browse published job listings with multi-dimensional filtering."""
        query = (
            select(JobPosting)
            .join(JobPosting.organization)
            .where(JobPosting.status == "PUBLISHED")
            .options(
                selectinload(JobPosting.skills),
                selectinload(JobPosting.organization),
            )
        )

        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    JobPosting.title.ilike(s),
                    JobPosting.description.ilike(s),
                    JobPosting.location.ilike(s),
                    Organization.name.ilike(s),
                )
            )

        if location:
            query = query.where(JobPosting.location.ilike(f"%{location.strip()}%"))

        if location_type:
            query = query.where(JobPosting.location_type == location_type.upper())

        if employment_type:
            query = query.where(JobPosting.employment_type == employment_type.upper())

        if experience_level:
            query = query.where(JobPosting.experience_level == experience_level.upper())

        if currency:
            query = query.where(JobPosting.compensation_currency == currency.upper())

        if min_compensation is not None:
            query = query.where(
                or_(
                    JobPosting.compensation_min >= min_compensation,
                    JobPosting.compensation_max >= min_compensation,
                )
            )

        if skill:
            skill_subquery = (
                select(JobPostingSkill.job_posting_id)
                .where(JobPostingSkill.name.ilike(f"%{skill.strip()}%"))
                .subquery()
            )
            query = query.where(JobPosting.id.in_(select(skill_subquery)))

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Order and paginate
        query = (
            query.order_by(JobPosting.published_at.desc().nullslast(), JobPosting.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db.execute(query)
        postings = list(res.scalars().all())

        items = []
        for p in postings:
            resp = JobPostingResponse.model_validate(p)
            resp.organization_name = p.organization.name if p.organization else None
            items.append(resp)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_published_job_detail(
        self,
        db: AsyncSession,
        job_id: UUID,
        candidate_user_id: Optional[UUID] = None,
    ) -> JobPostingDetailResponse:
        """Get detail of published job posting with application & save status for candidate."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id, JobPosting.status.in_(["PUBLISHED", "CLOSED"]))
            .options(
                selectinload(JobPosting.skills),
                selectinload(JobPosting.organization),
            )
        )
        res = await db.execute(stmt)
        posting = res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found or not currently active")

        resp = JobPostingDetailResponse.model_validate(posting)
        resp.organization_name = posting.organization.name if posting.organization else None
        if posting.organization:
            resp.organization = OrganizationResponse.model_validate(posting.organization)

        # Check candidate-specific interaction states if candidate is logged in
        if candidate_user_id:
            # Check applied
            app_stmt = select(Application.id).where(
                Application.job_posting_id == job_id,
                Application.user_id == candidate_user_id,
            )
            has_app = (await db.execute(app_stmt)).scalar_one_or_none()
            resp.has_applied = has_app is not None

            # Check saved opportunity
            opp_stmt = select(SavedOpportunity.id).join(Opportunity).where(
                Opportunity.job_posting_id == job_id,
                SavedOpportunity.user_id == candidate_user_id,
            )
            saved_id = (await db.execute(opp_stmt)).scalar_one_or_none()
            resp.saved_opportunity_id = saved_id

        return resp

    async def save_job_to_opportunities(
        self,
        db: AsyncSession,
        candidate_user_id: UUID,
        job_id: UUID,
    ) -> Opportunity:
        """Save a published job posting into candidate's personal opportunities pipeline."""
        posting_stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id, JobPosting.status == "PUBLISHED")
            .options(selectinload(JobPosting.organization))
        )
        p_res = await db.execute(posting_stmt)
        posting = p_res.scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Published job posting {job_id} not found")

        # Check if candidate already has an opportunity for this job
        existing_opp_stmt = select(Opportunity).where(
            Opportunity.user_id == candidate_user_id,
            Opportunity.job_posting_id == job_id,
        )
        existing_opp = (await db.execute(existing_opp_stmt)).scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if not existing_opp:
            existing_opp = Opportunity(
                user_id=candidate_user_id,
                job_posting_id=job_id,
                title=posting.title,
                company_name=posting.organization.name if posting.organization else "Employer",
                source="PLATFORM",
                location=posting.location,
                location_type=posting.location_type,
                employment_type=posting.employment_type,
                description=posting.description,
                requirements=posting.requirements,
                compensation_min=posting.compensation_min,
                compensation_max=posting.compensation_max,
                compensation_currency=posting.compensation_currency,
                posted_date=posting.published_at.date() if posting.published_at else None,
                expiry_date=posting.deadline_date,
                status="SAVED",
                created_at=now,
                updated_at=now,
            )
            db.add(existing_opp)
            await db.flush()

        # Add to SavedOpportunity bookmark table if not present
        saved_check = select(SavedOpportunity).where(
            SavedOpportunity.user_id == candidate_user_id,
            SavedOpportunity.opportunity_id == existing_opp.id,
        )
        is_saved = (await db.execute(saved_check)).scalar_one_or_none()
        if not is_saved:
            db.add(SavedOpportunity(
                user_id=candidate_user_id,
                opportunity_id=existing_opp.id,
                saved_at=now,
            ))

        await db.commit()
        await db.refresh(existing_opp)
        return existing_opp

    async def apply_to_job(
        self,
        db: AsyncSession,
        candidate_user_id: UUID,
        job_id: UUID,
        data: JobApplyRequest,
    ) -> Application:
        """Submit a candidate application to a published job posting."""
        posting_stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id, JobPosting.status == "PUBLISHED")
            .options(selectinload(JobPosting.organization))
        )
        posting = (await db.execute(posting_stmt)).scalar_one_or_none()
        if not posting:
            raise ValidationError("This job posting is not open for applications")

        # Check duplicate
        dup_stmt = select(Application.id).where(
            Application.job_posting_id == job_id,
            Application.user_id == candidate_user_id,
        )
        if (await db.execute(dup_stmt)).scalar_one_or_none():
            raise ConflictError("You have already applied to this job posting")

        # Validate resume belongs to candidate
        resume_stmt = select(Resume).where(Resume.id == data.resume_id, Resume.user_id == candidate_user_id)
        resume = (await db.execute(resume_stmt)).scalar_one_or_none()
        if not resume:
            raise NotFoundError("Referenced resume not found or does not belong to user")

        if data.cover_letter_doc_id:
            doc_stmt = select(Document).where(Document.id == data.cover_letter_doc_id, Document.user_id == candidate_user_id)
            if not (await db.execute(doc_stmt)).scalar_one_or_none():
                raise NotFoundError("Referenced cover letter document not found or does not belong to user")

        now = datetime.now(timezone.utc)
        today = now.date()

        if posting.deadline_date and posting.deadline_date < today:
            raise ValidationError("This job posting has reached its application deadline")

        app = Application(
            user_id=candidate_user_id,
            job_posting_id=job_id,
            job_title=posting.title,
            company_name=posting.organization.name if posting.organization else "Employer",
            job_location=posting.location,
            job_location_type=posting.location_type,
            employment_type=posting.employment_type,
            job_description=posting.description,
            compensation_min=posting.compensation_min,
            compensation_max=posting.compensation_max,
            compensation_currency=posting.compensation_currency,
            source="PLATFORM",
            status="ACTIVE",
            current_stage="APPLIED",
            applied_date=today,
            deadline_date=posting.deadline_date,
            resume_id=data.resume_id,
            cover_letter_doc_id=data.cover_letter_doc_id,
            priority="MEDIUM",
            created_at=now,
            updated_at=now,
        )
        db.add(app)
        await db.flush()

        # Initial stage history
        db.add(ApplicationStageHistory(
            application_id=app.id,
            from_stage=None,
            to_stage="APPLIED",
            changed_at=now,
            notes=data.notes or "Applied via platform",
            changed_by_user=candidate_user_id,
        ))

        # Initial activity
        db.add(ApplicationActivity(
            application_id=app.id,
            user_id=candidate_user_id,
            event_type="CREATED",
            event_data={"source": "PLATFORM", "job_posting_id": str(job_id)},
            description=f"Applied to {posting.title} at {app.company_name}",
            created_at=now,
        ))

        # If candidate added application notes
        if data.notes:
            db.add(ApplicationNote(
                application_id=app.id,
                user_id=candidate_user_id,
                content=data.notes,
                created_at=now,
                updated_at=now,
            ))

        # If candidate previously saved this opportunity, mark opportunity status as APPLIED
        opp_stmt = select(Opportunity).where(
            Opportunity.user_id == candidate_user_id,
            Opportunity.job_posting_id == job_id,
        )
        opp = (await db.execute(opp_stmt)).scalar_one_or_none()
        if opp:
            opp.status = "APPLIED"
            opp.updated_at = now

        try:
            await db.commit()
            await db.refresh(app)
            return app
        except IntegrityError:
            await db.rollback()
            raise ConflictError("You have already applied to this job posting")

    # =========================================================================
    # Recruiter Applicant Management
    # =========================================================================

    async def list_job_applicants(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        job_id: UUID,
        stage: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List applicants for a recruiter's job posting (scoped candidate summary)."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)
        job_stmt = select(JobPosting).where(JobPosting.id == job_id, JobPosting.organization_id == org.id)
        posting = (await db.execute(job_stmt)).scalar_one_or_none()
        if not posting:
            raise NotFoundError(f"Job posting {job_id} not found")

        query = (
            select(Application)
            .where(Application.job_posting_id == job_id)
            .options(
                selectinload(Application.resume),
            )
        )

        if stage:
            query = query.where(Application.current_stage == stage.upper())

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        query = (
            query.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        apps = list((await db.execute(query)).scalars().all())

        # Load candidate profiles
        candidate_user_ids = [a.user_id for a in apps]
        users_map = {}
        profiles_map = {}
        if candidate_user_ids:
            u_stmt = select(User).where(User.id.in_(candidate_user_ids))
            users_map = {u.id: u for u in (await db.execute(u_stmt)).scalars().all()}

            p_stmt = select(CandidateProfile).where(CandidateProfile.user_id.in_(candidate_user_ids))
            profiles_map = {p.user_id: p for p in (await db.execute(p_stmt)).scalars().all()}

        items = []
        for a in apps:
            u = users_map.get(a.user_id)
            p = profiles_map.get(a.user_id)
            full_name = "Candidate"
            loc = None
            if p:
                names = [p.first_name, p.last_name]
                combined = " ".join(filter(None, names)).strip()
                full_name = combined or p.preferred_name or (u.username if u else "Candidate")
                loc_parts = [p.location_city, p.location_state, p.location_country]
                loc = ", ".join(filter(None, loc_parts)).strip() or None
            elif u:
                full_name = u.username

            summary = CandidateApplicationSummary(
                candidate_user_id=a.user_id,
                full_name=full_name,
                headline=p.headline if p else None,
                email=u.email if u else "",
                phone=p.phone if p else None,
                location=loc,
            )
            items.append(RecruiterApplicantListItem(
                application_id=a.id,
                job_posting_id=job_id,
                candidate=summary,
                current_stage=a.current_stage,
                status=a.status,
                applied_date=a.applied_date,
                created_at=a.created_at,
                resume_id=a.resume_id,
                resume_name=a.resume.name if a.resume else None,
                resume_filename=a.resume.original_filename if a.resume else None,
            ))

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_applicant_detail(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        application_id: UUID,
    ) -> RecruiterApplicantDetailResponse:
        """Get full applicant review detail under strict recruiter isolation."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        stmt = (
            select(Application)
            .join(JobPosting, Application.job_posting_id == JobPosting.id)
            .where(
                Application.id == application_id,
                JobPosting.organization_id == org.id,
            )
            .options(
                selectinload(Application.resume),
                selectinload(Application.stage_history),
                selectinload(Application.notes),
                selectinload(Application.job_posting),
            )
        )
        app = (await db.execute(stmt)).scalar_one_or_none()
        if not app:
            raise NotFoundError(f"Applicant record {application_id} not found")

        u_stmt = select(User).where(User.id == app.user_id)
        user = (await db.execute(u_stmt)).scalar_one_or_none()

        p_stmt = select(CandidateProfile).where(CandidateProfile.user_id == app.user_id)
        prof = (await db.execute(p_stmt)).scalar_one_or_none()

        full_name = "Candidate"
        loc = None
        if prof:
            names = [prof.first_name, prof.last_name]
            combined = " ".join(filter(None, names)).strip()
            full_name = combined or prof.preferred_name or (user.username if user else "Candidate")
            loc_parts = [prof.location_city, prof.location_state, prof.location_country]
            loc = ", ".join(filter(None, loc_parts)).strip() or None
        elif user:
            full_name = user.username

        cand_summary = CandidateApplicationSummary(
            candidate_user_id=app.user_id,
            full_name=full_name,
            headline=prof.headline if prof else None,
            email=user.email if user else "",
            phone=prof.phone if prof else None,
            location=loc,
        )

        resume_info = None
        if app.resume:
            resume_info = ResumeSnapshotInfo(
                id=app.resume.id,
                name=app.resume.name,
                original_filename=app.resume.original_filename,
                version=app.resume.version,
            )

        stage_histories = [
            StageHistoryResponse.model_validate(sh) for sh in sorted(app.stage_history, key=lambda x: x.changed_at)
        ]
        # Candidate-private notes must NEVER be serialized to recruiters.
        # Only recruiter-authored notes (where n.user_id != app.user_id) are visible to recruiters.
        notes = [
            ApplicationNoteResponse.model_validate(n)
            for n in sorted(app.notes, key=lambda x: x.created_at, reverse=True)
            if n.user_id != app.user_id
        ]
        # Cover note: extract from initial application stage history
        initial_sh = next(
            (sh for sh in sorted(app.stage_history, key=lambda x: x.changed_at) if sh.from_stage is None),
            None,
        )
        cover_notes = initial_sh.notes if initial_sh else None

        return RecruiterApplicantDetailResponse(
            application_id=app.id,
            job_posting_id=app.job_posting_id,
            job_title=app.job_title,
            candidate=cand_summary,
            current_stage=app.current_stage,
            status=app.status,
            applied_date=app.applied_date,
            created_at=app.created_at,
            resume=resume_info,
            cover_letter_doc_id=app.cover_letter_doc_id,
            cover_notes=cover_notes,
            stage_history=stage_histories,
            notes=notes,
        )

    async def update_applicant_stage(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        application_id: UUID,
        data: StageTransitionRequest,
    ) -> RecruiterApplicantDetailResponse:
        """Advance or update applicant recruitment stage."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        stmt = (
            select(Application)
            .join(JobPosting, Application.job_posting_id == JobPosting.id)
            .where(
                Application.id == application_id,
                JobPosting.organization_id == org.id,
            )
        )
        app = (await db.execute(stmt)).scalar_one_or_none()
        if not app:
            raise NotFoundError(f"Applicant record {application_id} not found")

        old_stage = app.current_stage
        now = datetime.now(timezone.utc)
        app.current_stage = data.to_stage
        app.updated_at = now

        if data.to_stage in ("ACCEPTED", "REJECTED", "WITHDRAWN"):
            app.status = "CLOSED"
            app.outcome = data.to_stage

        # Stage history with authoritative recruiter identity
        db.add(ApplicationStageHistory(
            application_id=app.id,
            from_stage=old_stage,
            to_stage=data.to_stage,
            changed_at=now,
            notes=data.notes,
            changed_by_user=recruiter_user_id,
        ))

        # Recruiter audit activity
        db.add(ApplicationActivity(
            application_id=app.id,
            user_id=recruiter_user_id,
            event_type="STAGE_CHANGE",
            event_data={"from_stage": old_stage, "to_stage": data.to_stage, "actor": "RECRUITER"},
            description=f"Recruiter moved application stage to {data.to_stage}",
            created_at=now,
        ))

        await db.commit()
        return await self.get_applicant_detail(db, recruiter_user_id, application_id)

    async def get_applicant_resume_file(
        self,
        db: AsyncSession,
        recruiter_user_id: UUID,
        application_id: UUID,
    ) -> tuple[str, str, str]:
        """Fetch applicant's submitted resume file key, filename, and mime type."""
        org = await self._get_recruiter_organization(db, recruiter_user_id)

        stmt = (
            select(Application)
            .join(JobPosting, Application.job_posting_id == JobPosting.id)
            .where(
                Application.id == application_id,
                JobPosting.organization_id == org.id,
            )
            .options(selectinload(Application.resume))
        )
        app = (await db.execute(stmt)).scalar_one_or_none()
        if not app:
            raise NotFoundError(f"Applicant record {application_id} not found")

        if not app.resume:
            raise NotFoundError("No resume was attached to this application")

        return (app.resume.storage_key, app.resume.original_filename, app.resume.mime_type or "application/pdf")


job_posting_service = JobPostingService()
