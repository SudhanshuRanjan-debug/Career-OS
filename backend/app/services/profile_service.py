"""
Profile service — candidate profile, preferences, normalized collections, and deterministic completeness.
Strictly isolates user resources via current_user.id.
"""

from decimal import Decimal
from typing import Any, Type, TypeVar
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidatePreferences, CandidateProfile
from app.models.document import Document
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
from app.models.user import User
from app.schemas.profile import (
    CandidatePreferencesResponse,
    CandidatePreferencesUpdate,
    PersonalInfoResponse,
    PersonalInfoUpdate,
    ProfessionalInfoResponse,
    ProfessionalInfoUpdate,
    ProfileCompletenessResponse,
    ProfileOverviewResponse,
    SectionCompleteness,
)

T = TypeVar("T", Education, Experience, Project, Skill, Certification, Achievement, Language, ProfileLink)


class ProfileService:
    """Service layer for Candidate Profile and sub-sections."""

    # -----------------------------------------------------------------------
    # Candidate Profile (Personal & Professional)
    # -----------------------------------------------------------------------

    async def get_or_create_profile(self, db: AsyncSession, user_id: UUID) -> CandidateProfile:
        result = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = CandidateProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    async def get_personal_info(self, db: AsyncSession, user: User) -> PersonalInfoResponse:
        profile = await self.get_or_create_profile(db, user.id)
        return PersonalInfoResponse(
            id=profile.id,
            user_id=user.id,
            email=user.email,
            first_name=profile.first_name,
            last_name=profile.last_name,
            preferred_name=profile.preferred_name,
            phone=profile.phone,
            location_city=profile.location_city,
            location_state=profile.location_state,
            location_country=profile.location_country,
            timezone=profile.timezone,
            headline=profile.headline,
            website=profile.website,
            profile_photo_key=profile.profile_photo_key,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def update_personal_info(
        self, db: AsyncSession, user: User, payload: PersonalInfoUpdate
    ) -> PersonalInfoResponse:
        profile = await self.get_or_create_profile(db, user.id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        await db.commit()
        await db.refresh(profile)

        return PersonalInfoResponse(
            id=profile.id,
            user_id=user.id,
            email=user.email,
            first_name=profile.first_name,
            last_name=profile.last_name,
            preferred_name=profile.preferred_name,
            phone=profile.phone,
            location_city=profile.location_city,
            location_state=profile.location_state,
            location_country=profile.location_country,
            timezone=profile.timezone,
            headline=profile.headline,
            website=profile.website,
            profile_photo_key=profile.profile_photo_key,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def get_professional_info(self, db: AsyncSession, user_id: UUID) -> ProfessionalInfoResponse:
        profile = await self.get_or_create_profile(db, user_id)
        return ProfessionalInfoResponse.model_validate(profile)

    async def update_professional_info(
        self, db: AsyncSession, user_id: UUID, payload: ProfessionalInfoUpdate
    ) -> ProfessionalInfoResponse:
        profile = await self.get_or_create_profile(db, user_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        await db.commit()
        await db.refresh(profile)
        return ProfessionalInfoResponse.model_validate(profile)

    # -----------------------------------------------------------------------
    # Job Preferences
    # -----------------------------------------------------------------------

    async def get_or_create_preferences(self, db: AsyncSession, user_id: UUID) -> CandidatePreferences:
        result = await db.execute(select(CandidatePreferences).where(CandidatePreferences.user_id == user_id))
        preferences = result.scalar_one_or_none()
        if not preferences:
            preferences = CandidatePreferences(user_id=user_id)
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        return preferences

    async def get_preferences(self, db: AsyncSession, user_id: UUID) -> CandidatePreferencesResponse:
        prefs = await self.get_or_create_preferences(db, user_id)
        return CandidatePreferencesResponse.model_validate(prefs)

    async def update_preferences(
        self, db: AsyncSession, user_id: UUID, payload: CandidatePreferencesUpdate
    ) -> CandidatePreferencesResponse:
        prefs = await self.get_or_create_preferences(db, user_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(prefs, field, value)

        await db.commit()
        await db.refresh(prefs)
        return CandidatePreferencesResponse.model_validate(prefs)

    # -----------------------------------------------------------------------
    # Normalized Items Generic CRUD (Education, Experience, Project, etc.)
    # -----------------------------------------------------------------------

    async def list_items(self, db: AsyncSession, model: Type[T], user_id: UUID) -> list[T]:
        result = await db.execute(
            select(model).where(model.user_id == user_id).order_by(model.sort_order.asc(), model.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_item(self, db: AsyncSession, model: Type[T], user_id: UUID, data: dict[str, Any]) -> T:
        item = model(user_id=user_id, **data)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def get_item(self, db: AsyncSession, model: Type[T], user_id: UUID, item_id: UUID) -> T:
        result = await db.execute(
            select(model).where(model.id == item_id, model.user_id == user_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found or access denied",
            )
        return item

    async def update_item(
        self, db: AsyncSession, model: Type[T], user_id: UUID, item_id: UUID, data: dict[str, Any]
    ) -> T:
        item = await self.get_item(db, model, user_id, item_id)
        for field, value in data.items():
            setattr(item, field, value)
        await db.commit()
        await db.refresh(item)
        return item

    async def delete_item(self, db: AsyncSession, model: Type[T], user_id: UUID, item_id: UUID) -> None:
        item = await self.get_item(db, model, user_id, item_id)
        await db.delete(item)
        await db.commit()

    # -----------------------------------------------------------------------
    # Deterministic Profile Completeness
    # -----------------------------------------------------------------------

    async def calculate_completeness(self, db: AsyncSession, user_id: UUID) -> ProfileCompletenessResponse:
        """
        Explainable, deterministic profile completeness calculation.
        Weights sum to 100%:
          - Personal Info: 15%
          - Professional Summary: 15%
          - Education: 15%
          - Experience: 15%
          - Skills: 15%
          - Resume: 15%
          - Job Preferences: 10%
        """
        sections: dict[str, SectionCompleteness] = {}

        # 1. Personal Info (15%)
        profile_res = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
        profile = profile_res.scalar_one_or_none()
        personal_missing = []
        if not profile or not profile.first_name:
            personal_missing.append("First Name")
        if not profile or not profile.last_name:
            personal_missing.append("Last Name")
        if not profile or not profile.phone:
            personal_missing.append("Phone Number")
        if not profile or not profile.location_city:
            personal_missing.append("City")

        sections["personal"] = SectionCompleteness(
            completed=len(personal_missing) == 0,
            weight=15,
            missing_fields=personal_missing,
        )

        # 2. Professional Summary (15%)
        prof_missing = []
        if not profile or not profile.headline:
            prof_missing.append("Professional Headline")
        if not profile or not profile.professional_summary:
            prof_missing.append("Professional Summary")

        sections["professional"] = SectionCompleteness(
            completed=len(prof_missing) == 0,
            weight=15,
            missing_fields=prof_missing,
        )

        # 3. Education (15%)
        edu_count_res = await db.execute(
            select(func.count(Education.id)).where(Education.user_id == user_id)
        )
        edu_count = edu_count_res.scalar() or 0
        sections["education"] = SectionCompleteness(
            completed=edu_count > 0,
            weight=15,
            missing_fields=[] if edu_count > 0 else ["At least one education record"],
        )

        # 4. Experience (15%)
        exp_count_res = await db.execute(
            select(func.count(Experience.id)).where(Experience.user_id == user_id)
        )
        exp_count = exp_count_res.scalar() or 0
        sections["experience"] = SectionCompleteness(
            completed=exp_count > 0,
            weight=15,
            missing_fields=[] if exp_count > 0 else ["At least one work experience record"],
        )

        # 5. Skills (15%)
        skills_count_res = await db.execute(
            select(func.count(Skill.id)).where(Skill.user_id == user_id)
        )
        skills_count = skills_count_res.scalar() or 0
        sections["skills"] = SectionCompleteness(
            completed=skills_count >= 3,
            weight=15,
            missing_fields=[] if skills_count >= 3 else [f"Add at least 3 skills ({skills_count}/3 added)"],
        )

        # 6. Resume (15%)
        resume_count_res = await db.execute(
            select(func.count(Resume.id)).where(
                Resume.user_id == user_id,
                Resume.deleted_at.is_(None),
            )
        )
        resume_count = resume_count_res.scalar() or 0
        sections["resumes"] = SectionCompleteness(
            completed=resume_count > 0,
            weight=15,
            missing_fields=[] if resume_count > 0 else ["Upload at least one resume file"],
        )

        # 7. Preferences (10%)
        prefs_res = await db.execute(select(CandidatePreferences).where(CandidatePreferences.user_id == user_id))
        prefs = prefs_res.scalar_one_or_none()
        pref_missing = []
        if not prefs or not prefs.desired_job_titles or len(prefs.desired_job_titles) == 0:
            pref_missing.append("Desired Job Titles")
        if not prefs or not prefs.preferred_locations or len(prefs.preferred_locations) == 0:
            pref_missing.append("Preferred Locations")

        sections["preferences"] = SectionCompleteness(
            completed=len(pref_missing) == 0,
            weight=10,
            missing_fields=pref_missing,
        )

        # Calculate overall score
        score = sum(sec.weight for sec in sections.values() if sec.completed)

        return ProfileCompletenessResponse(
            overall_score=score,
            sections=sections,
        )

    # -----------------------------------------------------------------------
    # Aggregated Overview
    # -----------------------------------------------------------------------

    async def get_overview(self, db: AsyncSession, user: User) -> ProfileOverviewResponse:
        personal = await self.get_personal_info(db, user)
        professional = await self.get_professional_info(db, user.id)
        preferences = await self.get_preferences(db, user.id)
        completeness = await self.calculate_completeness(db, user.id)

        # Get counts for all subsections
        counts: dict[str, int] = {}
        for name, model in [
            ("education", Education),
            ("experience", Experience),
            ("projects", Project),
            ("skills", Skill),
            ("certifications", Certification),
            ("achievements", Achievement),
            ("languages", Language),
            ("links", ProfileLink),
        ]:
            res = await db.execute(select(func.count(model.id)).where(model.user_id == user.id))
            counts[name] = res.scalar() or 0

        res_resumes = await db.execute(
            select(func.count(Resume.id)).where(Resume.user_id == user.id, Resume.deleted_at.is_(None))
        )
        counts["resumes"] = res_resumes.scalar() or 0

        res_docs = await db.execute(
            select(func.count(Document.id)).where(Document.user_id == user.id, Document.deleted_at.is_(None))
        )
        counts["documents"] = res_docs.scalar() or 0

        return ProfileOverviewResponse(
            personal=personal,
            professional=professional,
            preferences=preferences,
            completeness=completeness,
            counts=counts,
        )


profile_service = ProfileService()
