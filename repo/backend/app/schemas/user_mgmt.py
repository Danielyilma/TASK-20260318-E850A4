from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.password_policy import validate_password_complexity, validate_username
from app.models.enums import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1)
    role: UserRole
    id_number: str | None = None
    contact_info: str | None = None

    @field_validator("username")
    @classmethod
    def username_rules(cls, v: str) -> str:
        validate_username(v)
        return v

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        validate_password_complexity(v)
        return v


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    contact_info: str | None = None
    id_number: str | None = None


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    role: UserRole
    is_locked: bool
    created_at: datetime


class UserListPage(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    per_page: int
    pages: int


class UserAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    role: UserRole
    id_number: str | None
    contact_info: str | None
    is_locked: bool
    failed_login_attempts: int
    created_at: datetime
    updated_at: datetime


class UserDeactivateResponse(BaseModel):
    message: str


class UserUnlockResponse(BaseModel):
    message: str
    user_id: UUID
