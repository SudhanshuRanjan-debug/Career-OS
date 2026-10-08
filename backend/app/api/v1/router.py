"""
API v1 router aggregation.
Includes all active endpoint routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    profile,
    resumes,
    documents,
    opportunities,
    applications,
    companies,
    interviews,
    tasks,
    calendar,
    network,
    analytics,
    notifications,
    settings,
    qa_vault,
    dashboard,
    recruiter_organization,
    recruiter_jobs,
    jobs,
)

api_router = APIRouter()


# System / Health
api_router.include_router(health.router, tags=["system"])

# Domain Routers (Stage 1 architectural boundaries)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(network.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(network.router, prefix="/network/contacts", tags=["network"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(qa_vault.router, prefix="/qa-vault", tags=["qa-vault"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Two-Sided Platform Routers
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(recruiter_organization.router, prefix="/recruiter/organization", tags=["recruiter-organization"])
api_router.include_router(recruiter_jobs.router, prefix="/recruiter/jobs", tags=["recruiter-jobs"])
