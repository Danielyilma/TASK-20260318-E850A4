from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import RegistrationStatus


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    form_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    requested_funding: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[RegistrationStatus] = mapped_column(
        String(32),
        nullable=False,
        default=RegistrationStatus.draft,
    )
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    supplementary_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supplementary_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supplementary_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    checklist_items = relationship("MaterialChecklist", back_populates="registration", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="registration", cascade="all, delete-orphan")
    funding_account = relationship("FundingAccount", back_populates="registration", uselist=False)
