from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Uuid, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MaterialChecklist(Base):
    __tablename__ = "material_checklists"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("registrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_types: Mapped[list] = mapped_column(JSON, nullable=False)
    max_file_size_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    registration = relationship("Registration", back_populates="checklist_items")
    versions = relationship("MaterialVersion", back_populates="checklist_item", cascade="all, delete-orphan")
