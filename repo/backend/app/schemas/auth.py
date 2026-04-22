from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.password_policy import validate_password_complexity
from app.models.enums import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    role: UserRole
    created_at: datetime


class LoginResponse(BaseModel):
    user: LoginUser
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class LogoutResponse(BaseModel):
    message: str


class AuthMeResponse(BaseModel):
    id: UUID
    username: str
    role: UserRole
    id_number: str | None
    contact_info: str | None
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class AuthMeUpdate(BaseModel):
    contact_info: str | None = None
    id_number: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> AuthMeUpdate:
        if self.contact_info is None and self.id_number is None:
            raise ValueError("At least one field is required")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        try:
            validate_password_complexity(value)
        except ValueError:
            raise ValueError("New password does not meet complexity requirements")
        return value


class ChangePasswordResponse(BaseModel):
    message: str
