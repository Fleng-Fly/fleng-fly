"""Pydantic request/response schemas for the auth module."""

from pydantic import EmailStr, Field

from app.core.schemas import CamelModel
from app.modules.users.schemas import UserResponse

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class AccessTokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
