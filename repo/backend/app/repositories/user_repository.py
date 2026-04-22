from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def count_list(self, *, role: UserRole | None, is_locked: bool | None, search: str | None) -> int:
        stmt = select(func.count()).select_from(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_locked is not None:
            stmt = stmt.where(User.is_locked.is_(bool(is_locked)))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(User.username).like(like))
        return int(self.db.execute(stmt).scalar_one())

    def list_page(
        self,
        *,
        page: int,
        per_page: int,
        role: UserRole | None,
        is_locked: bool | None,
        search: str | None,
    ) -> list[User]:
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_locked is not None:
            stmt = stmt.where(User.is_locked.is_(bool(is_locked)))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(User.username).like(like))
        stmt = stmt.order_by(User.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        return list(self.db.execute(stmt).scalars().all())
