"""
Pydantic schemas for the Q&A Vault and Application Answers domain.
Stage 5 Master Implementation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_QA_CATEGORIES = {"GENERAL", "BEHAVIORAL", "TECHNICAL", "SALARY", "LOGISTICS"}


class QAVaultEntryBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Reusable question prompt")
    answer: str = Field(..., min_length=1, description="Reusable answer template content")
    category: Optional[str] = Field("GENERAL", max_length=100, description="Category of question")
    is_template: bool = Field(False, description="Whether this is a reusable template")

    @field_validator("question", "answer", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Question and answer cannot be empty")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            upper_v = v.upper()
            if upper_v in ALLOWED_QA_CATEGORIES:
                return upper_v
            return v
        return v


class QAVaultEntryCreate(QAVaultEntryBase):
    pass


class QAVaultEntryUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    is_template: Optional[bool] = None

    @field_validator("question", "answer", mode="before")
    @classmethod
    def validate_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Question and answer cannot be empty")
        return v


class QAVaultEntryResponse(QAVaultEntryBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QAVaultListResponse(BaseModel):
    items: List[QAVaultEntryResponse]
    total: int


# ---------------------------------------------------------------------------
# Application Answers (Application-Specific Q&A)
# ---------------------------------------------------------------------------

class ApplicationAnswerBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Question asked on application")
    answer: str = Field(..., min_length=1, description="Answer submitted for this application")
    qa_vault_entry_id: Optional[UUID] = Field(None, description="Optional link to Q&A Vault template")

    @field_validator("question", "answer", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Question and answer cannot be empty")
        return v


class ApplicationAnswerCreate(ApplicationAnswerBase):
    pass


class ApplicationAnswerUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1)
    qa_vault_entry_id: Optional[UUID] = None

    @field_validator("question", "answer", mode="before")
    @classmethod
    def validate_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Question and answer cannot be empty")
        return v


class ApplicationAnswerResponse(ApplicationAnswerBase):
    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
