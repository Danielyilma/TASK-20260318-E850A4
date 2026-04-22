from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MaterialVersionLabel, RegistrationStatus, ReviewAction, TransactionType


class RegistrationFormData(BaseModel):
    project_title: str = Field(min_length=1, max_length=500)
    project_description: str = Field(min_length=1, max_length=10000)
    target_beneficiaries: int = Field(gt=0)
    start_date: str = Field(min_length=1, max_length=32)
    end_date: str = Field(min_length=1, max_length=32)

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, end_date: str, info):
        start_date = info.data.get("start_date")
        try:
            start_dt = datetime.fromisoformat(str(start_date))
            end_dt = datetime.fromisoformat(str(end_date))
        except ValueError as exc:
            raise ValueError("start_date and end_date must be ISO-8601 date strings") from exc
        if end_dt < start_dt:
            raise ValueError("end_date must be greater than or equal to start_date")
        return end_date


class RegistrationCreate(BaseModel):
    activity_id: UUID
    form_data: dict[str, Any]
    requested_funding: Decimal = Field(gt=0)

    @field_validator("form_data")
    @classmethod
    def validate_form(cls, v: dict[str, Any]) -> dict[str, Any]:
        RegistrationFormData.model_validate(v)
        return v


class RegistrationUpdate(BaseModel):
    form_data: dict[str, Any] | None = None
    requested_funding: Decimal | None = Field(default=None, gt=0)

    @field_validator("form_data")
    @classmethod
    def validate_form(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None:
            RegistrationFormData.model_validate(v)
        return v


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    applicant_id: UUID
    activity_id: UUID
    form_data: dict[str, Any]
    requested_funding: Decimal
    status: RegistrationStatus
    deadline: datetime
    is_locked: bool
    supplementary_used: bool
    supplementary_requested_at: datetime | None
    supplementary_deadline: datetime | None
    created_at: datetime
    updated_at: datetime


class RegistrationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    applicant_id: UUID
    activity_id: UUID
    status: RegistrationStatus
    requested_funding: Decimal
    deadline: datetime
    is_locked: bool
    created_at: datetime


class RegistrationListPage(BaseModel):
    items: list[RegistrationListItem]
    total: int
    page: int
    per_page: int
    pages: int


class RegistrationSubmitResponse(BaseModel):
    id: UUID
    status: RegistrationStatus
    updated_at: datetime


class RegistrationCancelResponse(BaseModel):
    id: UUID
    status: RegistrationStatus
    updated_at: datetime


class RegistrationDeleteResponse(BaseModel):
    message: str


class ChecklistItemCreate(BaseModel):
    item_name: str = Field(min_length=1, max_length=255)
    is_required: bool = True
    allowed_types: list[str]
    max_file_size_mb: int = Field(default=20, ge=1, le=20)

    @field_validator("allowed_types")
    @classmethod
    def allowed(cls, v: list[str]) -> list[str]:
        allowed = {"pdf", "jpg", "png"}
        for t in v:
            if t not in allowed:
                raise ValueError(f"Invalid type {t}")
        if not v:
            raise ValueError("allowed_types must not be empty")
        return v


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_id: UUID
    item_name: str
    is_required: bool
    allowed_types: list[str]
    max_file_size_mb: int
    created_at: datetime


class ChecklistItemUpdate(BaseModel):
    item_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_required: bool | None = None
    allowed_types: list[str] | None = None
    max_file_size_mb: int | None = Field(default=None, ge=1, le=20)

    @field_validator("allowed_types")
    @classmethod
    def allowed(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        allowed = {"pdf", "jpg", "png"}
        for t in v:
            if t not in allowed:
                raise ValueError(f"Invalid type {t}")
        if not v:
            raise ValueError("allowed_types must not be empty")
        return v


class ChecklistListItem(BaseModel):
    id: UUID
    item_name: str
    is_required: bool
    allowed_types: list[str]
    max_file_size_mb: int
    versions_count: int
    latest_version_label: str | None
    created_at: datetime


class ChecklistListResponse(BaseModel):
    items: list[ChecklistListItem]
    total: int


class MaterialVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    file_name: str
    file_size_bytes: int
    file_type: str
    sha256_hash: str
    label: MaterialVersionLabel
    uploaded_at: datetime


class ChecklistItemDetail(ChecklistItemRead):
    versions: list[MaterialVersionRead]


class MaterialUploadResponse(BaseModel):
    id: UUID
    checklist_item_id: UUID
    version_number: int
    file_name: str
    file_size_bytes: int
    file_type: str
    sha256_hash: str
    label: MaterialVersionLabel
    uploaded_at: datetime
    evicted_version: dict[str, Any] | None = None


class MaterialVersionsListResponse(BaseModel):
    checklist_item_id: UUID
    item_name: str
    versions: list[MaterialVersionRead]


class MaterialLabelUpdate(BaseModel):
    label: MaterialVersionLabel


class MaterialLabelResponse(BaseModel):
    id: UUID
    label: MaterialVersionLabel
    updated_at: datetime


class ReviewRequest(BaseModel):
    action: ReviewAction
    comment: str | None = None
    correction_reason: str | None = None


class ReviewResponse(BaseModel):
    review_id: UUID
    registration_id: UUID
    reviewer_id: UUID
    previous_status: RegistrationStatus
    new_status: RegistrationStatus
    comment: str | None
    created_at: datetime


class BatchReviewRequest(BaseModel):
    """registration_ids length is capped at 50 by the service (BATCH_SIZE_EXCEEDED)."""

    registration_ids: list[UUID] = Field(min_length=1)
    action: ReviewAction
    comment: str | None = None
    correction_reason: str | None = None


class BatchReviewResultItem(BaseModel):
    registration_id: UUID
    status: str
    new_status: RegistrationStatus | None = None
    review_id: UUID | None = None
    error: str | None = None


class BatchReviewResponse(BaseModel):
    batch_id: UUID
    total_requested: int
    successful: int
    failed: int
    results: list[BatchReviewResultItem]


class ReviewRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reviewer_id: UUID
    reviewer_username: str
    previous_status: RegistrationStatus
    new_status: RegistrationStatus
    comment: str | None
    correction_reason: str | None
    batch_id: UUID | None
    created_at: datetime


class ReviewListPage(BaseModel):
    items: list[ReviewRecordRead]
    total: int
    page: int
    per_page: int
    pages: int


class WaitlistPromoteRequest(BaseModel):
    comment: str | None = None


class FundingAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_id: UUID
    approved_budget: Decimal
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    is_overspent: bool
    overspend_percentage: float
    created_at: datetime
    updated_at: datetime


class FundingAccountListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_id: UUID
    approved_budget: Decimal
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    is_overspent: bool
    created_at: datetime


class FundingAccountListPage(BaseModel):
    items: list[FundingAccountListItem]
    total: int
    page: int
    per_page: int
    pages: int


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    description: str | None = None
    override_confirmed: bool | None = None


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    override_confirmed: bool | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    funding_account_id: UUID
    type: TransactionType
    amount: Decimal
    category: str
    description: str | None
    invoice_file_path: str | None = None
    recorded_by: UUID
    created_at: datetime
    override_confirmed: bool | None = None
    overspend_percentage: float | None = None


class TransactionListPage(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    per_page: int
    pages: int


class TransactionDeleteResponse(BaseModel):
    message: str


class SensitiveVerifyResponse(BaseModel):
    registration_id: UUID
    applicant_id: UUID
    id_number: str | None
    contact_info: str | None
    verified_at: datetime
    audit_log_id: UUID


class ChecklistDeleteResponse(BaseModel):
    message: str
