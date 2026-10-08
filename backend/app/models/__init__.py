"""
Central model exports for Career & Job Application Management Platform.
"""

from app.models.user import User, PasswordResetToken, RefreshToken
from app.models.candidate_profile import CandidateProfile, CandidatePreferences
from app.models.profile_items import (
    Education,
    Experience,
    Project,
    Skill,
    Certification,
    Achievement,
    Language,
    ProfileLink,
)
from app.models.resume import Resume
from app.models.document import Document
from app.models.organization import Organization
from app.models.job_posting import JobPosting, JobPostingSkill
from app.models.company import Company
from app.models.contact import Contact
from app.models.opportunity import Opportunity, SavedOpportunity
from app.models.application import (
    Application,
    ApplicationStageHistory,
    ApplicationNote,
    ApplicationFollowup,
    ApplicationDocument,
    ApplicationActivity,
)
from app.models.qa_vault import QAVaultEntry, ApplicationAnswer
from app.models.interview import Interview, InterviewPreparation
from app.models.task import Task
from app.models.notification import Notification

__all__ = [
    "User",
    "PasswordResetToken",
    "RefreshToken",
    "Organization",
    "JobPosting",
    "JobPostingSkill",
    "CandidateProfile",
    "CandidatePreferences",
    "Education",
    "Experience",
    "Project",
    "Skill",
    "Certification",
    "Achievement",
    "Language",
    "ProfileLink",
    "Resume",
    "Document",
    "Company",
    "Contact",
    "Opportunity",
    "SavedOpportunity",
    "Application",
    "ApplicationStageHistory",
    "ApplicationNote",
    "ApplicationFollowup",
    "ApplicationDocument",
    "ApplicationActivity",
    "QAVaultEntry",
    "ApplicationAnswer",
    "Interview",
    "InterviewPreparation",
    "Task",
    "Notification",
]
