from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.enums import MaterialVersionLabel, UserRole
from app.models.material_checklist import MaterialChecklist
from app.models.material_version import MaterialVersion
from app.models.registration import Registration
from app.models.user import User
from app.schemas.registration_domain import (
    ChecklistItemCreate,
    ChecklistItemDetail,
    ChecklistItemRead,
    ChecklistItemUpdate,
    ChecklistListItem,
    ChecklistListResponse,
    ChecklistDeleteResponse,
    MaterialVersionRead,
)
from app.services.phase4_access import ensure_registration, ensure_registration_access


class Phase4ChecklistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_item(self, admin: User, registration_id: uuid.UUID, payload: ChecklistItemCreate) -> ChecklistItemRead:
        if admin.role != UserRole.system_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        now = utcnow()
        item = MaterialChecklist(
            id=uuid.uuid4(),
            registration_id=reg.id,
            item_name=payload.item_name,
            is_required=payload.is_required,
            allowed_types=list(payload.allowed_types),
            max_file_size_mb=payload.max_file_size_mb,
            created_at=now,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return ChecklistItemRead.model_validate(item)

    def list_items(self, user: User, registration_id: uuid.UUID) -> ChecklistListResponse:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        items = self.db.scalars(
            select(MaterialChecklist).where(MaterialChecklist.registration_id == reg.id).order_by(MaterialChecklist.created_at)
        ).all()
        out: list[ChecklistListItem] = []
        for it in items:
            vers = self.db.scalars(
                select(MaterialVersion).where(MaterialVersion.checklist_item_id == it.id).order_by(MaterialVersion.version_number.desc())
            ).all()
            latest_label = vers[0].label.value if vers else None
            out.append(
                ChecklistListItem(
                    id=it.id,
                    item_name=it.item_name,
                    is_required=it.is_required,
                    allowed_types=list(it.allowed_types),
                    max_file_size_mb=it.max_file_size_mb,
                    versions_count=len(vers),
                    latest_version_label=latest_label,
                    created_at=it.created_at,
                )
            )
        return ChecklistListResponse(items=out, total=len(out))

    def get_item(self, user: User, registration_id: uuid.UUID, item_id: uuid.UUID) -> ChecklistItemDetail:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        item = self.db.get(MaterialChecklist, item_id)
        if item is None or item.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
        vers = self.db.scalars(
            select(MaterialVersion).where(MaterialVersion.checklist_item_id == item.id).order_by(MaterialVersion.version_number)
        ).all()
        return ChecklistItemDetail(
            id=item.id,
            registration_id=item.registration_id,
            item_name=item.item_name,
            is_required=item.is_required,
            allowed_types=list(item.allowed_types),
            max_file_size_mb=item.max_file_size_mb,
            created_at=item.created_at,
            versions=[MaterialVersionRead.model_validate(v) for v in vers],
        )

    def update_item(
        self, admin: User, registration_id: uuid.UUID, item_id: uuid.UUID, payload: ChecklistItemUpdate
    ) -> ChecklistItemRead:
        if admin.role != UserRole.system_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        item = self.db.get(MaterialChecklist, item_id)
        if item is None or item.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
        data = payload.model_dump(exclude_unset=True)
        if "item_name" in data and data["item_name"] is not None:
            item.item_name = data["item_name"]
        if "is_required" in data:
            item.is_required = data["is_required"]
        if "allowed_types" in data and data["allowed_types"] is not None:
            item.allowed_types = list(data["allowed_types"])
        if "max_file_size_mb" in data and data["max_file_size_mb"] is not None:
            item.max_file_size_mb = data["max_file_size_mb"]
        self.db.commit()
        self.db.refresh(item)
        return ChecklistItemRead.model_validate(item)

    def delete_item(self, admin: User, registration_id: uuid.UUID, item_id: uuid.UUID) -> ChecklistDeleteResponse:
        if admin.role != UserRole.system_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        item = self.db.get(MaterialChecklist, item_id)
        if item is None or item.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
        cnt = int(
            self.db.scalar(
                select(func.count()).select_from(MaterialVersion).where(MaterialVersion.checklist_item_id == item.id)
            )
            or 0
        )
        if cnt > 0:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Cannot delete checklist item with uploaded materials",
                headers={"X-Error-Code": "CONFLICT"},
            )
        self.db.delete(item)
        self.db.commit()
        return ChecklistDeleteResponse(message="Checklist item deleted successfully")
