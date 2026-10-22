from pydantic import EmailStr, Field

from app.core.schemas import CamelModel


class ResetRequest(CamelModel):
    email: EmailStr = Field(max_length=254)


class ResetConfirm(CamelModel):
    token: str = Field(min_length=32, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class ResetResponse(CamelModel):
    message: str = "If the account exists, password reset instructions will be sent."
