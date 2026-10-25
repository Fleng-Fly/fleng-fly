"""User/profile read dependency and endpoint schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.schemas import CamelModel


class UserResponse(CamelModel):
    id: UUID
    email: str
    display_name: str
    level: int
    xp: int
    english_level: str = "A1"
    preferred_language: str = "English"
    created_at: datetime


class ProfileUpdate(CamelModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    english_level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None = None
    preferred_language: str | None = Field(default=None, min_length=1, max_length=40)

    @field_validator("display_name", "preferred_language")
    @classmethod
    def non_blank(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            raise ValueError("Must not be null or blank")
        return value.strip()


class PasswordChange(CamelModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
