from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_system_admin
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityDeleteResponse,
    ActivityListPage,
    ActivityRead,
    ActivityUpdate,
)
from app.services.activity_service import ActivityService

router = APIRouter()


def get_activity_service(db: Session = Depends(get_db)) -> ActivityService:
    return ActivityService(db)


@router.post(
    "/activities",
    response_model=ActivityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    payload: ActivityCreate,
    _: User = Depends(require_system_admin),
    service: ActivityService = Depends(get_activity_service),
) -> ActivityRead:
    return service.create(payload)


@router.get("/activities", response_model=ActivityListPage)
def list_activities(
    _: User = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
) -> ActivityListPage:
    return service.list_activities(page=page, per_page=per_page, is_active=is_active, search=search)


@router.get("/activities/{activity_id}", response_model=ActivityRead)
def get_activity(
    activity_id: uuid.UUID,
    _: User = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
) -> ActivityRead:
    return service.get(activity_id)


@router.put("/activities/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: uuid.UUID,
    payload: ActivityUpdate,
    _: User = Depends(require_system_admin),
    service: ActivityService = Depends(get_activity_service),
) -> ActivityRead:
    return service.update(activity_id, payload)


@router.delete("/activities/{activity_id}", response_model=ActivityDeleteResponse)
def delete_activity(
    activity_id: uuid.UUID,
    _: User = Depends(require_system_admin),
    service: ActivityService = Depends(get_activity_service),
) -> ActivityDeleteResponse:
    return service.soft_delete(activity_id)
