from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.http_errors import bad_request, forbidden
from app.core.time import as_utc, utcnow
from app.models.activity import Activity
from app.models.enums import MaterialVersionLabel, RegistrationStatus
from app.models.material_checklist import MaterialChecklist
from app.models.material_version import MaterialVersion
from app.models.registration import Registration
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.schemas.registration_domain import (
    RegistrationCancelResponse,
    RegistrationCreate,
    RegistrationDeleteResponse,
    RegistrationListItem,
    RegistrationListPage,
    RegistrationRead,
    RegistrationSubmitResponse,
    RegistrationUpdate,
)
from app.services.phase4_access import (
    ensure_registration,
    ensure_registration_access,
    ensure_owner_applicant,
    registration_filters_for_user,
)


def update_registration_lock(reg: Registration, activity: Activity, now) -> None:
    dl = as_utc(activity.deadline) or activity.deadline
    if now <= dl:
        reg.is_locked = False
        return
    if (
        reg.status in (RegistrationStatus.needs_correction, RegistrationStatus.supplemented)
        and reg.supplementary_deadline
        and now <= (as_utc(reg.supplementary_deadline) or reg.supplementary_deadline)
    ):
        reg.is_locked = False
        return
    reg.is_locked = True


class Phase4RegistrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activities = ActivityRepository(db)

    def create(self, applicant: User, payload: RegistrationCreate) -> RegistrationRead:
        if getattr(applicant.role, "value", applicant.role) != "applicant":
            raise forbidden("FORBIDDEN", "Only applicants can create registrations")
        activity = self.activities.get_by_id(payload.activity_id)
        if activity is None or not activity.is_active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        now = utcnow()
        if now > as_utc(activity.deadline):
            raise bad_request("DEADLINE_PASSED", "Activity deadline has passed")
        if payload.requested_funding > activity.budget:
            raise bad_request("VALIDATION_ERROR", "requested_funding cannot exceed activity budget")

        reg = Registration(
            id=uuid.uuid4(),
            activity_id=payload.activity_id,
            applicant_id=applicant.id,
            form_data=payload.form_data,
            requested_funding=payload.requested_funding,
            status=RegistrationStatus.draft,
            deadline=activity.deadline,
            is_locked=False,
            supplementary_requested_at=None,
            supplementary_deadline=None,
            supplementary_used=False,
            created_at=now,
            updated_at=now,
        )
        update_registration_lock(reg, activity, now)
        self.db.add(reg)
        self.db.commit()
        self.db.refresh(reg)
        return RegistrationRead.model_validate(reg)

    def list_page(
        self,
        user: User,
        *,
        page: int,
        per_page: int,
        status_filter: RegistrationStatus | None,
        activity_id: uuid.UUID | None,
        sort: str | None,
    ) -> RegistrationListPage:
        filters = list(registration_filters_for_user(user))
        if status_filter is not None:
            filters.append(Registration.status == status_filter)
        if activity_id is not None:
            filters.append(Registration.activity_id == activity_id)

        count_stmt = select(func.count()).select_from(Registration)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self.db.scalar(count_stmt) or 0)

        order = Registration.created_at.desc()
        if sort:
            desc = sort.startswith("-")
            name = sort[1:] if desc else sort
            col = getattr(Registration, name, None)
            if col is not None:
                order = col.desc() if desc else col.asc()

        rows_stmt = select(Registration)
        if filters:
            rows_stmt = rows_stmt.where(*filters)
        rows_stmt = rows_stmt.order_by(order).offset((page - 1) * per_page).limit(per_page)
        rows = list(self.db.scalars(rows_stmt).all())
        pages = math.ceil(total / per_page) if total else 0
        return RegistrationListPage(
            items=[RegistrationListItem.model_validate(r) for r in rows],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get(self, user: User, registration_id: uuid.UUID) -> RegistrationRead:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        activity = self.activities.get_by_id(reg.activity_id)
        if activity:
            update_registration_lock(reg, activity, utcnow())
            self.db.commit()
            self.db.refresh(reg)
        return RegistrationRead.model_validate(reg)

    def update(self, user: User, registration_id: uuid.UUID, payload: RegistrationUpdate) -> RegistrationRead:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_owner_applicant(user, reg)
        if reg.status != RegistrationStatus.draft:
            raise bad_request("INVALID_STATE_TRANSITION", "Registration can only be updated in draft status")
        activity = self.activities.get_by_id(reg.activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        now = utcnow()
        if now > as_utc(activity.deadline):
            raise bad_request("DEADLINE_PASSED", "Activity deadline has passed")

        if payload.form_data is not None:
            reg.form_data = payload.form_data
        if payload.requested_funding is not None:
            reg.requested_funding = payload.requested_funding
        reg.updated_at = now
        update_registration_lock(reg, activity, now)
        self.db.commit()
        self.db.refresh(reg)
        return RegistrationRead.model_validate(reg)

    def delete(self, user: User, registration_id: uuid.UUID) -> RegistrationDeleteResponse:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_owner_applicant(user, reg)
        if reg.status != RegistrationStatus.draft:
            raise bad_request("INVALID_STATE_TRANSITION", "Only draft registrations can be deleted")
        self.db.delete(reg)
        self.db.commit()
        return RegistrationDeleteResponse(message="Registration deleted successfully")

    def submit(self, user: User, registration_id: uuid.UUID) -> RegistrationSubmitResponse:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_owner_applicant(user, reg)
        if reg.status != RegistrationStatus.draft:
            raise bad_request("INVALID_STATE_TRANSITION", "Registration is not in draft status")
        activity = self.activities.get_by_id(reg.activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        now = utcnow()
        update_registration_lock(reg, activity, now)
        if reg.is_locked:
            raise bad_request("DEADLINE_PASSED", "Activity deadline has passed")
        if now > as_utc(activity.deadline):
            raise bad_request("DEADLINE_PASSED", "Activity deadline has passed")

        items = self.db.scalars(
            select(MaterialChecklist).where(MaterialChecklist.registration_id == reg.id)
        ).all()
        for it in items:
            if not it.is_required:
                continue
            vers = self.db.scalars(
                select(MaterialVersion).where(MaterialVersion.checklist_item_id == it.id)
            ).all()
            if not any(v.label == MaterialVersionLabel.submitted for v in vers):
                raise bad_request("VALIDATION_ERROR", "Required materials are missing")

        reg.status = RegistrationStatus.submitted
        reg.updated_at = now
        self.db.commit()
        self.db.refresh(reg)
        return RegistrationSubmitResponse(id=reg.id, status=reg.status, updated_at=reg.updated_at)

    def cancel(self, user: User, registration_id: uuid.UUID) -> RegistrationCancelResponse:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_owner_applicant(user, reg)
        if reg.status not in (
            RegistrationStatus.submitted,
            RegistrationStatus.supplemented,
            RegistrationStatus.waitlisted,
        ):
            raise bad_request(
                "INVALID_STATE_TRANSITION",
                "Registration cannot be canceled from current status",
            )
        now = utcnow()
        reg.status = RegistrationStatus.canceled
        reg.updated_at = now
        self.db.commit()
        self.db.refresh(reg)
        return RegistrationCancelResponse(id=reg.id, status=reg.status, updated_at=reg.updated_at)
