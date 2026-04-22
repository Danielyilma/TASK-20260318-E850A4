from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_system_admin, require_system_admin_create_user
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_mgmt import (
    UserAdminDetail,
    UserAdminUpdate,
    UserCreate,
    UserDeactivateResponse,
    UserListPage,
    UserUnlockResponse,
)
from app.services.user_admin_service import UserAdminService

router = APIRouter()


def get_user_admin_service(db: Session = Depends(get_db)) -> UserAdminService:
    return UserAdminService(db)


@router.post("/users", response_model=UserAdminDetail, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_system_admin_create_user),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserAdminDetail:
    return service.create_user(payload)


@router.get("/users", response_model=UserListPage)
def list_users(
    _: User = Depends(require_system_admin),
    service: UserAdminService = Depends(get_user_admin_service),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    role: UserRole | None = Query(default=None),
    is_locked: bool | None = Query(default=None),
    search: str | None = Query(default=None),
) -> UserListPage:
    return service.list_users(page=page, per_page=per_page, role=role, is_locked=is_locked, search=search)


@router.get("/users/{user_id}", response_model=UserAdminDetail)
def get_user(
    user_id: uuid.UUID,
    _: User = Depends(require_system_admin),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserAdminDetail:
    return service.get_user(user_id)


@router.put("/users/{user_id}", response_model=UserAdminDetail)
def update_user(
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
    _: User = Depends(require_system_admin),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserAdminDetail:
    return service.update_user(user_id, payload)


@router.delete("/users/{user_id}", response_model=UserDeactivateResponse)
def deactivate_user(
    user_id: uuid.UUID,
    _: User = Depends(require_system_admin),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserDeactivateResponse:
    return service.deactivate_user(user_id)


@router.post("/users/{user_id}/unlock", response_model=UserUnlockResponse)
def unlock_user(
    user_id: uuid.UUID,
    _: User = Depends(require_system_admin),
    service: UserAdminService = Depends(get_user_admin_service),
) -> UserUnlockResponse:
    return service.unlock_user(user_id)
