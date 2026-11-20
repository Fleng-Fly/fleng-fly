"""User/profile read dependency and endpoint schemas."""

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import EmailStr, Field, field_validator

from app.core.levels import LearningLevel
from app.core.schemas import CamelModel


class UserResponse(CamelModel):
    id: UUID
    email: str
    display_name: str
    level: int
    xp: int
    english_level: str = "A1"
    preferred_language: str = "English"
    daily_lessons_goal: int = 1
    daily_words_goal: int = 10
    timezone: str | None = None
    created_at: datetime


class ProfileUpdate(CamelModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    english_level: LearningLevel | None = None
    preferred_language: str | None = Field(default=None, min_length=1, max_length=40)
    daily_lessons_goal: int | None = Field(default=None, ge=1, le=10)
    daily_words_goal: int | None = Field(default=None, ge=1, le=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("timezone")
    @classmethod
    def known_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Unknown IANA time zone") from None
        return value

    @field_validator("display_name", "preferred_language")
    @classmethod
    def non_blank(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            raise ValueError("Must not be null or blank")
        return value.strip()


class PasswordChange(CamelModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class EmailChangeRequest(CamelModel):
    email: EmailStr
    current_password: str = Field(min_length=1, max_length=128)


class EmailChangeConfirm(CamelModel):
    token: str = Field(min_length=32, max_length=128)
