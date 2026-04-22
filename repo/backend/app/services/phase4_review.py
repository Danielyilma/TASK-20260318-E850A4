from __future__ import annotations

import math
import uuid
from datetime import timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.http_errors import bad_request
from app.core.time import utcnow
from app.models.enums import RegistrationStatus, ReviewAction, UserRole
from app.models.funding_account import FundingAccount
from app.models.registration import Registration
from app.models.review_record import ReviewRecord
from app.models.user import User
from app.schemas.registration_domain import (
    BatchReviewRequest,
    BatchReviewResponse,
    BatchReviewResultItem,
    ReviewListPage,
    ReviewRecordRead,
    ReviewRequest,
    ReviewResponse,
    WaitlistPromoteRequest,
)
from app.services.phase4_access import ensure_registration, ensure_registration_access


def _transition(current: RegistrationStatus, action: ReviewAction) -> RegistrationStatus | None:
    m: dict[tuple[RegistrationStatus, ReviewAction], RegistrationStatus] = {
        (RegistrationStatus.submitted, ReviewAction.approve): RegistrationStatus.approved,
        (RegistrationStatus.supplemented, ReviewAction.approve): RegistrationStatus.approved,
        (RegistrationStatus.submitted, ReviewAction.reject): RegistrationStatus.rejected,
        (RegistrationStatus.supplemented, ReviewAction.reject): RegistrationStatus.rejected,
        (RegistrationStatus.submitted, ReviewAction.request_correction): RegistrationStatus.needs_correction,
        (RegistrationStatus.supplemented, ReviewAction.request_correction): RegistrationStatus.needs_correction,
        (RegistrationStatus.submitted, ReviewAction.waitlist): RegistrationStatus.waitlisted,
        (RegistrationStatus.supplemented, ReviewAction.waitlist): RegistrationStatus.waitlisted,
        (RegistrationStatus.submitted, ReviewAction.cancel): RegistrationStatus.canceled,
        (RegistrationStatus.supplemented, ReviewAction.cancel): RegistrationStatus.canceled,
        (RegistrationStatus.waitlisted, ReviewAction.cancel): RegistrationStatus.canceled,
    }
    return m.get((current, action))


def _ensure_funding_account(db: Session, reg: Registration) -> None:
    found = db.scalar(select(FundingAccount.id).where(FundingAccount.registration_id == reg.id))
    if found:
        return
    now = utcnow()
    fa = FundingAccount(
        id=uuid.uuid4(),
        registration_id=reg.id,
        approved_budget=reg.requested_funding,
        total_income=Decimal("0"),
        total_expenses=Decimal("0"),
        created_at=now,
        updated_at=now,
    )
    db.add(fa)


class Phase4ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def apply_review(self, reviewer: User, registration_id: uuid.UUID, payload: ReviewRequest) -> ReviewResponse:
        if reviewer.role != UserRole.reviewer:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only reviewers can perform reviews")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(reviewer, reg)
        if payload.action == ReviewAction.request_correction and not (payload.correction_reason or "").strip():
            raise bad_request("VALIDATION_ERROR", "correction_reason is required for request_correction action")
        if payload.action == ReviewAction.request_correction and reg.supplementary_used:
            raise bad_request("SUPPLEMENTARY_EXHAUSTED", "One-time supplementary submission has already been used")

        new_status = _transition(reg.status, payload.action)
        if new_status is None:
            action_s = getattr(payload.action, "value", payload.action)
            status_s = getattr(reg.status, "value", reg.status)
            raise bad_request(
                "INVALID_STATE_TRANSITION",
                f"Cannot perform '{action_s}' on registration with status '{status_s}'",
            )

        prev = reg.status
        now = utcnow()
        if payload.action == ReviewAction.request_correction:
            reg.supplementary_requested_at = now
            reg.supplementary_deadline = now + timedelta(hours=72)
        reg.status = new_status
        reg.updated_at = now

        rec = ReviewRecord(
            id=uuid.uuid4(),
            registration_id=reg.id,
            reviewer_id=reviewer.id,
            previous_status=prev,
            new_status=new_status,
            comment=payload.comment,
            correction_reason=payload.correction_reason if payload.action == ReviewAction.request_correction else None,
            batch_id=None,
            created_at=now,
        )
        self.db.add(rec)

        if new_status == RegistrationStatus.approved:
            _ensure_funding_account(self.db, reg)

        self.db.commit()
        self.db.refresh(rec)
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService
        Phase5QualityMetricsService(self.db).compute(activity_id=reg.activity_id)
        return ReviewResponse(
            review_id=rec.id,
            registration_id=reg.id,
            reviewer_id=reviewer.id,
            previous_status=prev,
            new_status=new_status,
            comment=rec.comment,
            created_at=rec.created_at,
        )

    def batch_review(self, reviewer: User, payload: BatchReviewRequest) -> BatchReviewResponse:
        if reviewer.role != UserRole.reviewer:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only reviewers can perform batch reviews")
        if len(payload.registration_ids) > 50:
            raise bad_request("BATCH_SIZE_EXCEEDED", "Maximum 50 registrations per batch")

        batch_id = uuid.uuid4()
        results: list[BatchReviewResultItem] = []
        ok = 0
        fail = 0
        for rid in payload.registration_ids:
            reg = self.db.get(Registration, rid)
            try:
                with self.db.begin_nested():
                    if reg is None:
                        raise ValueError("Registration not found")
                    ensure_registration_access(reviewer, reg)
                    if payload.action == ReviewAction.request_correction and not (payload.correction_reason or "").strip():
                        raise ValueError("correction_reason is required for request_correction action")
                    if payload.action == ReviewAction.request_correction and reg.supplementary_used:
                        raise ValueError("One-time supplementary submission has already been used")
                    new_status = _transition(reg.status, payload.action)
                    if new_status is None:
                        action_s = getattr(payload.action, "value", payload.action)
                        status_s = getattr(reg.status, "value", reg.status)
                        raise ValueError(
                            f"Cannot perform '{action_s}' on registration with status '{status_s}'"
                        )
                    prev = reg.status
                    now = utcnow()
                    if payload.action == ReviewAction.request_correction:
                        reg.supplementary_requested_at = now
                        reg.supplementary_deadline = now + timedelta(hours=72)
                    reg.status = new_status
                    reg.updated_at = now
                    rec = ReviewRecord(
                        id=uuid.uuid4(),
                        registration_id=reg.id,
                        reviewer_id=reviewer.id,
                        previous_status=prev,
                        new_status=new_status,
                        comment=payload.comment,
                        correction_reason=payload.correction_reason
                        if payload.action == ReviewAction.request_correction
                        else None,
                        batch_id=batch_id,
                        created_at=now,
                    )
                    self.db.add(rec)
                    if new_status == RegistrationStatus.approved:
                        _ensure_funding_account(self.db, reg)
                results.append(
                    BatchReviewResultItem(
                        registration_id=rid,
                        status="success",
                        new_status=new_status,
                        review_id=rec.id,
                    )
                )
                ok += 1
            except Exception as e:  # noqa: BLE001
                fail += 1
                msg = str(e.detail) if isinstance(e, HTTPException) else str(e)
                results.append(
                    BatchReviewResultItem(
                        registration_id=rid,
                        status="failed",
                        error=msg,
                    )
                )
        self.db.commit()
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService
        act_ids = set()
        for rid in payload.registration_ids:
            reg = self.db.get(Registration, rid)
            if reg:
                act_ids.add(reg.activity_id)
        for aid in act_ids:
            Phase5QualityMetricsService(self.db).compute(activity_id=aid)

        return BatchReviewResponse(
            batch_id=batch_id,
            total_requested=len(payload.registration_ids),
            successful=ok,
            failed=fail,
            results=results,
        )

    def list_reviews(
        self, user: User, registration_id: uuid.UUID, page: int, per_page: int
    ) -> ReviewListPage:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        stmt = select(ReviewRecord).where(ReviewRecord.registration_id == reg.id)
        total = int(
            self.db.scalar(
                select(func.count()).select_from(ReviewRecord).where(ReviewRecord.registration_id == reg.id)
            )
            or 0
        )
        rows = self.db.scalars(
            stmt.order_by(ReviewRecord.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        items: list[ReviewRecordRead] = []
        for r in rows:
            rev_user = self.db.get(User, r.reviewer_id)
            items.append(
                ReviewRecordRead(
                    id=r.id,
                    reviewer_id=r.reviewer_id,
                    reviewer_username=rev_user.username if rev_user else "",
                    previous_status=r.previous_status,
                    new_status=r.new_status,
                    comment=r.comment,
                    correction_reason=r.correction_reason,
                    batch_id=r.batch_id,
                    created_at=r.created_at,
                )
            )
        pages = math.ceil(total / per_page) if total else 0
        return ReviewListPage(items=items, total=total, page=page, per_page=per_page, pages=pages)

    def get_review(self, user: User, registration_id: uuid.UUID, review_id: uuid.UUID) -> ReviewRecordRead:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        r = self.db.get(ReviewRecord, review_id)
        if r is None or r.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review record not found")
        rev_user = self.db.get(User, r.reviewer_id)
        return ReviewRecordRead(
            id=r.id,
            reviewer_id=r.reviewer_id,
            reviewer_username=rev_user.username if rev_user else "",
            previous_status=r.previous_status,
            new_status=r.new_status,
            comment=r.comment,
            correction_reason=r.correction_reason,
            batch_id=r.batch_id,
            created_at=r.created_at,
        )

    def waitlist_promote(self, reviewer: User, registration_id: uuid.UUID, payload: WaitlistPromoteRequest) -> ReviewResponse:
        if reviewer.role != UserRole.reviewer:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only reviewers can promote from waitlist")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(reviewer, reg)
        if reg.status != RegistrationStatus.waitlisted:
            raise bad_request("INVALID_STATE_TRANSITION", "Registration is not in waitlisted status")
        prev = reg.status
        now = utcnow()
        reg.status = RegistrationStatus.approved
        reg.updated_at = now
        rec = ReviewRecord(
            id=uuid.uuid4(),
            registration_id=reg.id,
            reviewer_id=reviewer.id,
            previous_status=prev,
            new_status=RegistrationStatus.approved,
            comment=payload.comment,
            correction_reason=None,
            batch_id=None,
            created_at=now,
        )
        self.db.add(rec)
        _ensure_funding_account(self.db, reg)
        self.db.commit()
        self.db.refresh(rec)
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService
        Phase5QualityMetricsService(self.db).compute(activity_id=reg.activity_id)
        return ReviewResponse(
            review_id=rec.id,
            registration_id=reg.id,
            reviewer_id=reviewer.id,
            previous_status=prev,
            new_status=RegistrationStatus.approved,
            comment=rec.comment,
            created_at=rec.created_at,
        )
