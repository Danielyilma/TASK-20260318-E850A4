from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.time import utcnow


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    deadline: datetime
    budget: Decimal = Field(gt=0)

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future(cls, value: datetime) -> datetime:
        if value <= utcnow():
            raise ValueError("deadline must be a future timestamp")
        return value


class ActivityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    deadline: datetime | None = None
    budget: Decimal | None = Field(default=None, gt=0)

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future_when_present(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value <= utcnow():
            raise ValueError("deadline must be a future timestamp")
        return value


class ActivityListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    deadline: datetime
    budget: Decimal
    is_active: bool
    created_at: datetime

    @field_serializer("budget")
    def serialize_budget(self, value: Decimal) -> float:
        return float(value)


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    deadline: datetime
    budget: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("budget")
    def serialize_budget(self, value: Decimal) -> float:
        return float(value)


class ActivityDeleteResponse(BaseModel):
    message: str


class ActivityListPage(BaseModel):
    items: list[ActivityListItem]
    total: int
    page: int
    per_page: int
    pages: int
