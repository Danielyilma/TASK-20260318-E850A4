from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BackupRecord(Base):
    """Metadata for on-disk SQL + uploads archives (see BackupService)."""

    __tablename__ = "backup_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backup_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    backup_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_detail: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
