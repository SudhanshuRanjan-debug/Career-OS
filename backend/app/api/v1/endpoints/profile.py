"""
Candidate Profile API Endpoints: Overview, Personal, Professional, Preferences, Completeness,
and Normalized Collections (Education, Experience, Projects, Skills, Certifications, Achievements, Languages, Links).
Strictly derives ownership from current_user.id.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_candidate
from app.db.session import get_db
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
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.profile import (
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    CandidatePreferencesResponse,
    CandidatePreferencesUpdate,
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
    PersonalInfoResponse,
    PersonalInfoUpdate,
    ProfessionalInfoResponse,
    ProfessionalInfoUpdate,
    ProfileCompletenessResponse,
    ProfileLinkCreate,
    ProfileLinkResponse,
    ProfileLinkUpdate,
    ProfileOverviewResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)
from app.services.profile_service import profile_service

router = APIRouter(dependencies=[Depends(require_candidate)])


# ---------------------------------------------------------------------------
# Aggregated Overview & Completeness
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=ProfileOverviewResponse)
async def get_profile_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.get_overview(db, current_user)


@router.get("/completeness", response_model=ProfileCompletenessResponse)
async def get_profile_completeness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.calculate_completeness(db, current_user.id)


# ---------------------------------------------------------------------------
# Personal Information
# ---------------------------------------------------------------------------

@router.get("/personal", response_model=PersonalInfoResponse)
async def get_personal_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.get_personal_info(db, current_user)


@router.put("/personal", response_model=PersonalInfoResponse)
async def update_personal_info(
    payload: PersonalInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.update_personal_info(db, current_user, payload)


# ---------------------------------------------------------------------------
# Professional Information
# ---------------------------------------------------------------------------

@router.get("/professional", response_model=ProfessionalInfoResponse)
async def get_professional_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.get_professional_info(db, current_user.id)


@router.put("/professional", response_model=ProfessionalInfoResponse)
async def update_professional_info(
    payload: ProfessionalInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.update_professional_info(db, current_user.id, payload)


# ---------------------------------------------------------------------------
# Job Preferences
# ---------------------------------------------------------------------------

@router.get("/preferences", response_model=CandidatePreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.get_preferences(db, current_user.id)


@router.put("/preferences", response_model=CandidatePreferencesResponse)
async def update_preferences(
    payload: CandidatePreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.update_preferences(db, current_user.id, payload)


# ---------------------------------------------------------------------------
# Education CRUD
# ---------------------------------------------------------------------------

@router.get("/education", response_model=list[EducationResponse])
async def list_educations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Education, current_user.id)
    return [EducationResponse.model_validate(item) for item in items]


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def create_education(
    payload: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Education, current_user.id, payload.model_dump())
    return EducationResponse.model_validate(item)


@router.put("/education/{item_id}", response_model=EducationResponse)
async def update_education(
    item_id: UUID,
    payload: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Education, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return EducationResponse.model_validate(item)


@router.delete("/education/{item_id}", response_model=MessageResponse)
async def delete_education(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Education, current_user.id, item_id)
    return MessageResponse(message="Education record deleted successfully")


# ---------------------------------------------------------------------------
# Experience CRUD
# ---------------------------------------------------------------------------

@router.get("/experience", response_model=list[ExperienceResponse])
async def list_experiences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Experience, current_user.id)
    return [ExperienceResponse.model_validate(item) for item in items]


@router.post("/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    payload: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Experience, current_user.id, payload.model_dump())
    return ExperienceResponse.model_validate(item)


@router.put("/experience/{item_id}", response_model=ExperienceResponse)
async def update_experience(
    item_id: UUID,
    payload: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Experience, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return ExperienceResponse.model_validate(item)


@router.delete("/experience/{item_id}", response_model=MessageResponse)
async def delete_experience(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Experience, current_user.id, item_id)
    return MessageResponse(message="Experience record deleted successfully")


# ---------------------------------------------------------------------------
# Projects CRUD
# ---------------------------------------------------------------------------

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Project, current_user.id)
    return [ProjectResponse.model_validate(item) for item in items]


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Project, current_user.id, payload.model_dump())
    return ProjectResponse.model_validate(item)


@router.put("/projects/{item_id}", response_model=ProjectResponse)
async def update_project(
    item_id: UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Project, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return ProjectResponse.model_validate(item)


@router.delete("/projects/{item_id}", response_model=MessageResponse)
async def delete_project(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Project, current_user.id, item_id)
    return MessageResponse(message="Project deleted successfully")


# ---------------------------------------------------------------------------
# Skills CRUD
# ---------------------------------------------------------------------------

@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Skill, current_user.id)
    return [SkillResponse.model_validate(item) for item in items]


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Skill, current_user.id, payload.model_dump())
    return SkillResponse.model_validate(item)


@router.put("/skills/{item_id}", response_model=SkillResponse)
async def update_skill(
    item_id: UUID,
    payload: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Skill, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return SkillResponse.model_validate(item)


@router.delete("/skills/{item_id}", response_model=MessageResponse)
async def delete_skill(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Skill, current_user.id, item_id)
    return MessageResponse(message="Skill deleted successfully")


# ---------------------------------------------------------------------------
# Certifications CRUD
# ---------------------------------------------------------------------------

@router.get("/certifications", response_model=list[CertificationResponse])
async def list_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Certification, current_user.id)
    return [CertificationResponse.model_validate(item) for item in items]


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_certification(
    payload: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Certification, current_user.id, payload.model_dump())
    return CertificationResponse.model_validate(item)


@router.put("/certifications/{item_id}", response_model=CertificationResponse)
async def update_certification(
    item_id: UUID,
    payload: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Certification, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return CertificationResponse.model_validate(item)


@router.delete("/certifications/{item_id}", response_model=MessageResponse)
async def delete_certification(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Certification, current_user.id, item_id)
    return MessageResponse(message="Certification deleted successfully")


# ---------------------------------------------------------------------------
# Achievements CRUD
# ---------------------------------------------------------------------------

@router.get("/achievements", response_model=list[AchievementResponse])
async def list_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Achievement, current_user.id)
    return [AchievementResponse.model_validate(item) for item in items]


@router.post("/achievements", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_achievement(
    payload: AchievementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Achievement, current_user.id, payload.model_dump())
    return AchievementResponse.model_validate(item)


@router.put("/achievements/{item_id}", response_model=AchievementResponse)
async def update_achievement(
    item_id: UUID,
    payload: AchievementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Achievement, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return AchievementResponse.model_validate(item)


@router.delete("/achievements/{item_id}", response_model=MessageResponse)
async def delete_achievement(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Achievement, current_user.id, item_id)
    return MessageResponse(message="Achievement deleted successfully")


# ---------------------------------------------------------------------------
# Languages CRUD
# ---------------------------------------------------------------------------

@router.get("/languages", response_model=list[LanguageResponse])
async def list_languages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, Language, current_user.id)
    return [LanguageResponse.model_validate(item) for item in items]


@router.post("/languages", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
async def create_language(
    payload: LanguageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, Language, current_user.id, payload.model_dump())
    return LanguageResponse.model_validate(item)


@router.put("/languages/{item_id}", response_model=LanguageResponse)
async def update_language(
    item_id: UUID,
    payload: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, Language, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return LanguageResponse.model_validate(item)


@router.delete("/languages/{item_id}", response_model=MessageResponse)
async def delete_language(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, Language, current_user.id, item_id)
    return MessageResponse(message="Language deleted successfully")


# ---------------------------------------------------------------------------
# Profile Links CRUD
# ---------------------------------------------------------------------------

@router.get("/links", response_model=list[ProfileLinkResponse])
async def list_links(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await profile_service.list_items(db, ProfileLink, current_user.id)
    return [ProfileLinkResponse.model_validate(item) for item in items]


@router.post("/links", response_model=ProfileLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: ProfileLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.create_item(db, ProfileLink, current_user.id, payload.model_dump())
    return ProfileLinkResponse.model_validate(item)


@router.put("/links/{item_id}", response_model=ProfileLinkResponse)
async def update_link(
    item_id: UUID,
    payload: ProfileLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await profile_service.update_item(
        db, ProfileLink, current_user.id, item_id, payload.model_dump(exclude_unset=True)
    )
    return ProfileLinkResponse.model_validate(item)


@router.delete("/links/{item_id}", response_model=MessageResponse)
async def delete_link(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_item(db, ProfileLink, current_user.id, item_id)
    return MessageResponse(message="Profile link deleted successfully")
