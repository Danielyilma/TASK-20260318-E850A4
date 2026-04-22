from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_system_admin
from app.models.user import User
from app.schemas.backup_domain import BackupCreateResponse, BackupListPage, BackupRestoreResponse
from app.services.backup_service import BackupService

router = APIRouter(tags=["backups"])


def _svc(db: Session = Depends(get_db)) -> BackupService:
    return BackupService(db)


@router.get("/backups", response_model=BackupListPage)
def list_backups(
    _: Annotated[User, Depends(require_system_admin)],
    svc: BackupService = Depends(_svc),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    backup_type: str | None = Query(default=None),
) -> BackupListPage:
    return svc.list_page(page=page, per_page=per_page, status=status, backup_type=backup_type)


@router.post("/backups", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
def create_backup(
    _: Annotated[User, Depends(require_system_admin)],
    svc: BackupService = Depends(_svc),
) -> BackupCreateResponse:
    return svc.create_manual()


@router.post("/backups/{backup_id}/restore", response_model=BackupRestoreResponse)
def restore_backup(
    backup_id: uuid.UUID,
    _: Annotated[User, Depends(require_system_admin)],
    svc: BackupService = Depends(_svc),
) -> BackupRestoreResponse:
    return svc.restore(backup_id)
