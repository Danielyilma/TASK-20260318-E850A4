from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_mgmt import (
    UserAdminDetail,
    UserAdminUpdate,
    UserCreate,
    UserDeactivateResponse,
    UserListItem,
    UserListPage,
    UserUnlockResponse,
)


class UserAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, payload: UserCreate) -> UserAdminDetail:
        if self.users.get_by_username(payload.username) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exists")

        now = utcnow()
        pwd_hash, salt = hash_password_with_salt(payload.password)
        user = User(
            id=uuid.uuid4(),
            username=payload.username,
            password_hash=pwd_hash,
            salt=salt,
            role=payload.role,
            id_number=payload.id_number,
            contact_info=payload.contact_info,
            is_locked=False,
            locked_until=None,
            failed_login_attempts=0,
            first_failed_at=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.users.add(user)
        self.db.commit()
        self.db.refresh(user)
        return UserAdminDetail.model_validate(user)

    def list_users(
        self,
        *,
        page: int,
        per_page: int,
        role: UserRole | None,
        is_locked: bool | None,
        search: str | None,
    ) -> UserListPage:
        total = self.users.count_list(role=role, is_locked=is_locked, search=search)
        rows = self.users.list_page(page=page, per_page=per_page, role=role, is_locked=is_locked, search=search)
        pages = math.ceil(total / per_page) if total else 0
        return UserListPage(
            items=[UserListItem.model_validate(u) for u in rows],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get_user(self, user_id: uuid.UUID) -> UserAdminDetail:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserAdminDetail.model_validate(user)

    def update_user(self, user_id: uuid.UUID, payload: UserAdminUpdate) -> UserAdminDetail:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        now = utcnow()
        if "role" in data and data["role"] is not None:
            user.role = data["role"]
        if "contact_info" in data:
            user.contact_info = data["contact_info"]
        if "id_number" in data:
            user.id_number = data["id_number"]
        user.updated_at = now

        self.db.commit()
        self.db.refresh(user)
        return UserAdminDetail.model_validate(user)

    def deactivate_user(self, user_id: uuid.UUID) -> UserDeactivateResponse:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

        now = utcnow()
        user.is_active = False
        user.updated_at = now
        self.db.commit()
        return UserDeactivateResponse(message="User deactivated successfully")

    def unlock_user(self, user_id: uuid.UUID) -> UserUnlockResponse:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.is_locked:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User account is not locked")

        now = utcnow()
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        user.first_failed_at = None
        user.updated_at = now
        self.db.commit()

        return UserUnlockResponse(message="User account unlocked successfully", user_id=user.id)
