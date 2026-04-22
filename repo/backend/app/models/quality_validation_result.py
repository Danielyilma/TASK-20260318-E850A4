from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QualityValidationResult(Base):
    __tablename__ = "quality_validation_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_collection_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    registration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("registrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
