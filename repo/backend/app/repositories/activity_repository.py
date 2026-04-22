from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.registration import Registration
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def add(self, activity: Activity) -> Activity:
        self.db.add(activity)
        self.db.flush()
        return activity

    def get_by_id(self, activity_id: uuid.UUID, *, include_deleted: bool = False) -> Activity | None:
        activity = self.db.get(Activity, activity_id)
        if activity is None:
            return None
        if not include_deleted and activity.deleted_at is not None:
            return None
        return activity

    def count_registrations(self, activity_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Registration).where(Registration.activity_id == activity_id)
        return int(self.db.execute(stmt).scalar_one())

    def count_list(self, *, is_active: bool | None, search: str | None) -> int:
        stmt = select(func.count()).select_from(Activity).where(Activity.deleted_at.is_(None))
        if is_active is not None:
            stmt = stmt.where(Activity.is_active.is_(bool(is_active)))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Activity.name).like(like))
        return int(self.db.execute(stmt).scalar_one())

    def list_page(
        self,
        *,
        page: int,
        per_page: int,
        is_active: bool | None,
        search: str | None,
    ) -> list[Activity]:
        stmt = select(Activity).where(Activity.deleted_at.is_(None))
        if is_active is not None:
            stmt = stmt.where(Activity.is_active.is_(bool(is_active)))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Activity.name).like(like))
        stmt = stmt.order_by(Activity.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        return list(self.db.execute(stmt).scalars().all())
