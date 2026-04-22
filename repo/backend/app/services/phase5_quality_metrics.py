from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.business_rules import OVERSPEND_THRESHOLD_MULTIPLIER
from app.core.time import utcnow
from app.models.enums import RegistrationStatus
from app.models.registration import Registration
from app.models.review_record import ReviewRecord
from app.repositories.activity_repository import ActivityRepository


class Phase5QualityMetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activities = ActivityRepository(db)

    def _registration_filters(
        self,
        activity_id: uuid.UUID | None,
        start: datetime | None,
        end: datetime | None,
    ):
        filters = []
        if activity_id is not None:
            filters.append(Registration.activity_id == activity_id)
        if start is not None:
            filters.append(Registration.updated_at >= start)
        if end is not None:
            filters.append(Registration.updated_at <= end)
        return filters

    def compute(
        self,
        *,
        activity_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        rf = self._registration_filters(activity_id, start_date, end_date)
        base = select(Registration)
        if rf:
            base = base.where(*rf)

        total_registrations = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)

        def count_status(st: RegistrationStatus) -> int:
            q = select(func.count()).select_from(Registration).where(Registration.status == st)
            if rf:
                q = q.where(*rf)
            return int(self.db.scalar(q) or 0)

        approved = count_status(RegistrationStatus.approved)
        rejected = count_status(RegistrationStatus.rejected)
        needs_correction = count_status(RegistrationStatus.needs_correction)
        waitlisted = count_status(RegistrationStatus.waitlisted)

        total_reviewed = approved + rejected + needs_correction + waitlisted
        approval_rate = round((approved / total_reviewed) * 100, 2) if total_reviewed else 0.0

        def _review_count(*extra_filters) -> int:
            q = select(func.count()).select_from(ReviewRecord)
            if activity_id is not None:
                q = q.join(Registration, ReviewRecord.registration_id == Registration.id).where(
                    Registration.activity_id == activity_id
                )
            if start_date is not None:
                q = q.where(ReviewRecord.created_at >= start_date)
            if end_date is not None:
                q = q.where(ReviewRecord.created_at <= end_date)
            for f in extra_filters:
                q = q.where(f)
            return int(self.db.scalar(q) or 0)

        total_reviews = _review_count()
        correction_events = _review_count(ReviewRecord.new_status == RegistrationStatus.needs_correction)
        correction_rate = round((correction_events / total_reviews) * 100, 2) if total_reviews else 0.0

        from app.models.funding_account import FundingAccount

        fa_stmt = select(FundingAccount)
        if activity_id is not None:
            fa_stmt = fa_stmt.join(Registration, FundingAccount.registration_id == Registration.id).where(
                Registration.activity_id == activity_id
            )
        accounts = self.db.scalars(fa_stmt).all()
        total_accounts = len(accounts)
        overspent = sum(1 for fa in accounts if fa.total_expenses > fa.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER)
        overspending_rate = round((overspent / total_accounts) * 100, 2) if total_accounts else 0.0

        res = {
            "total_registrations": total_registrations,
            "total_reviewed": total_reviewed,
            "approved": approved,
            "rejected": rejected,
            "needs_correction": needs_correction,
            "waitlisted": waitlisted,
            "approval_rate": approval_rate,
            "correction_rate": correction_rate,
            "overspending_rate": overspending_rate,
            "computed_at": utcnow().isoformat().replace("+00:00", "Z"),
        }

        from app.services.phase5_alerts_service import Phase5AlertsService
        if activity_id is not None:
            Phase5AlertsService(self.db).evaluate_quality_metrics(activity_id, res)
        return res

    def for_activity(self, activity_id: uuid.UUID) -> dict:
        if self.activities.get_by_id(activity_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        return self.compute(activity_id=activity_id)
