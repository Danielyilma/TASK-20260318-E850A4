from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BackupListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    backup_type: str
    backup_path: str
    size_bytes: int
    status: str
    created_at: datetime
    restored_at: datetime | None


class BackupListPage(BaseModel):
    items: list[BackupListItem]
    total: int
    page: int
    per_page: int
    pages: int


class BackupCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    backup_type: str
    status: str
    backup_path: str
    size_bytes: int
    created_at: datetime


class BackupRestoreResponse(BaseModel):
    message: str
    backup_id: UUID
    restored_at: datetime
