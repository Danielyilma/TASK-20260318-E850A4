from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.activity import Activity
from app.repositories.activity_repository import ActivityRepository
from app.schemas.activity import (
    ActivityCreate,
    ActivityDeleteResponse,
    ActivityListItem,
    ActivityListPage,
    ActivityRead,
    ActivityUpdate,
)


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activities = ActivityRepository(db)

    def create(self, payload: ActivityCreate) -> ActivityRead:
        now = utcnow()
        activity = Activity(
            id=uuid.uuid4(),
            name=payload.name,
            description=payload.description,
            deadline=payload.deadline,
            budget=payload.budget,
            is_active=True,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
        self.activities.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return ActivityRead.model_validate(activity)

    def list_activities(
        self,
        *,
        page: int,
        per_page: int,
        is_active: bool | None,
        search: str | None,
    ) -> ActivityListPage:
        total = self.activities.count_list(is_active=is_active, search=search)
        rows = self.activities.list_page(page=page, per_page=per_page, is_active=is_active, search=search)
        pages = math.ceil(total / per_page) if total else 0
        return ActivityListPage(
            items=[ActivityListItem.model_validate(a) for a in rows],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get(self, activity_id: uuid.UUID) -> ActivityRead:
        activity = self.activities.get_by_id(activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        return ActivityRead.model_validate(activity)

    def update(self, activity_id: uuid.UUID, payload: ActivityUpdate) -> ActivityRead:
        activity = self.activities.get_by_id(activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")

        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        now = utcnow()
        if "name" in data:
            activity.name = data["name"]
        if "description" in data:
            activity.description = data["description"]
        if "deadline" in data:
            activity.deadline = data["deadline"]
        if "budget" in data:
            activity.budget = Decimal(str(data["budget"]))
        activity.updated_at = now

        self.db.commit()
        self.db.refresh(activity)
        return ActivityRead.model_validate(activity)

    def soft_delete(self, activity_id: uuid.UUID) -> ActivityDeleteResponse:
        activity = self.activities.get_by_id(activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")

        if self.activities.count_registrations(activity_id) > 0:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Cannot delete activity with existing registrations",
            )

        now = utcnow()
        activity.is_active = False
        activity.deleted_at = now
        activity.updated_at = now
        self.db.commit()
        return ActivityDeleteResponse(message="Activity deleted successfully")
