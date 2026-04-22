from __future__ import annotations

import uuid
from pathlib import Path

import hashlib
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.http_errors import bad_request
from app.core.time import as_utc, utcnow
from app.models.enums import MaterialVersionLabel, RegistrationStatus, UserRole
from app.models.material_checklist import MaterialChecklist
from app.models.material_version import MaterialVersion
from app.models.registration import Registration
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.schemas.registration_domain import (
    MaterialLabelResponse,
    MaterialUploadResponse,
    MaterialVersionsListResponse,
    MaterialVersionRead,
)
from app.services.phase4_access import ensure_registration, ensure_registration_access
from app.services.phase4_registration import update_registration_lock


class Phase4MaterialService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activities = ActivityRepository(db)

    def _total_bytes_registration(self, registration_id: uuid.UUID) -> int:
        stmt = (
            select(func.coalesce(func.sum(MaterialVersion.file_size_bytes), 0))
            .join(MaterialChecklist, MaterialVersion.checklist_item_id == MaterialChecklist.id)
            .where(MaterialChecklist.registration_id == registration_id)
        )
        return int(self.db.scalar(stmt) or 0)

    def _hash_exists(self, h: str) -> bool:
        c = self.db.scalar(select(func.count()).select_from(MaterialVersion).where(MaterialVersion.sha256_hash == h)) or 0
        return int(c) > 0

    async def upload(
        self, user: User, registration_id: uuid.UUID, item_id: uuid.UUID, file: UploadFile
    ) -> MaterialUploadResponse:
        if user.role != UserRole.applicant:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only applicants can upload materials")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        if reg.applicant_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You do not own this registration")
        item = self.db.get(MaterialChecklist, item_id)
        if item is None or item.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registration or checklist item not found")

        activity = self.activities.get_by_id(reg.activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        now = utcnow()
        update_registration_lock(reg, activity, now)

        if reg.status in (RegistrationStatus.needs_correction, RegistrationStatus.supplemented):
            if reg.supplementary_deadline is None or now > (as_utc(reg.supplementary_deadline) or reg.supplementary_deadline):
                raise bad_request("SUPPLEMENTARY_EXPIRED", "The 72-hour supplementary window has expired")
        elif reg.is_locked or now > as_utc(activity.deadline):
            raise bad_request("DEADLINE_PASSED", "Upload deadline has passed")

        raw = await file.read()
        size = len(raw)
        if size > 20 * 1024 * 1024:
            raise bad_request("FILE_TOO_LARGE", "File size exceeds 20MB limit")

        ext = (file.filename or "bin").rsplit(".", 1)[-1].lower()
        if ext not in item.allowed_types:
            raise bad_request(
                "FILE_TYPE_NOT_ALLOWED",
                f"File type '{ext}' is not allowed. Accepted: {', '.join(item.allowed_types)}",
            )

        digest = hashlib.sha256(raw).hexdigest()
        if self._hash_exists(digest):
            raise bad_request("DUPLICATE_FILE", "This file has already been uploaded in the system (SHA-256 match)")

        current_total = self._total_bytes_registration(reg.id)
        if current_total + size > 200 * 1024 * 1024:
            raise bad_request("FILE_TOO_LARGE", "Total upload size for this registration exceeds 200MB")

        settings = get_settings()
        root = Path(settings.upload_root)
        root.mkdir(parents=True, exist_ok=True)
        sub = root / str(reg.id) / str(item.id)
        sub.mkdir(parents=True, exist_ok=True)

        vers = self.db.scalars(
            select(MaterialVersion).where(MaterialVersion.checklist_item_id == item.id).order_by(MaterialVersion.version_number)
        ).all()
        evicted = None
        if len(vers) >= 3:
            oldest = min(vers, key=lambda v: v.version_number)
            try:
                Path(oldest.file_path).unlink(missing_ok=True)
            except OSError:
                pass
            evicted = {"id": str(oldest.id), "version_number": oldest.version_number, "file_name": oldest.file_name}
            self.db.delete(oldest)
            self.db.flush()
            vers = self.db.scalars(
                select(MaterialVersion).where(MaterialVersion.checklist_item_id == item.id).order_by(MaterialVersion.version_number)
            ).all()

        next_num = max((v.version_number for v in vers), default=0) + 1
        vid = uuid.uuid4()
        fname = f"{vid}.{ext}"
        fpath = sub / fname
        fpath.write_bytes(raw)

        mv = MaterialVersion(
            id=vid,
            checklist_item_id=item.id,
            version_number=next_num,
            file_path=str(fpath),
            file_name=file.filename or fname,
            file_size_bytes=size,
            file_type=ext,
            sha256_hash=digest,
            label=MaterialVersionLabel.pending_submission,
            uploaded_at=now,
            uploaded_by=user.id,
            updated_at=now,
        )
        self.db.add(mv)

        if reg.status in (RegistrationStatus.needs_correction, RegistrationStatus.supplemented):
            reg.status = RegistrationStatus.supplemented
            # Supplementary flow is consumed once entered, but uploads remain allowed until deadline.
            reg.supplementary_used = True
        reg.updated_at = now
        
        from sqlalchemy.exc import IntegrityError
        try:
            self.db.commit()
            self.db.refresh(mv)
        except IntegrityError:
            self.db.rollback()
            raise bad_request("DUPLICATE_FILE", "This file has already been uploaded in the system (SHA-256 match)")

        resp = MaterialUploadResponse(
            id=mv.id,
            checklist_item_id=item.id,
            version_number=mv.version_number,
            file_name=mv.file_name,
            file_size_bytes=mv.file_size_bytes,
            file_type=mv.file_type,
            sha256_hash=mv.sha256_hash,
            label=mv.label,
            uploaded_at=mv.uploaded_at,
            evicted_version=evicted,
        )
        return resp

    def list_versions(self, user: User, registration_id: uuid.UUID, item_id: uuid.UUID) -> MaterialVersionsListResponse:
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(user, reg)
        item = self.db.get(MaterialChecklist, item_id)
        if item is None or item.registration_id != reg.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registration or checklist item not found")
        vers = self.db.scalars(
            select(MaterialVersion).where(MaterialVersion.checklist_item_id == item.id).order_by(MaterialVersion.version_number)
        ).all()
        return MaterialVersionsListResponse(
            checklist_item_id=item.id,
            item_name=item.item_name,
            versions=[MaterialVersionRead.model_validate(v) for v in vers],
        )

    def download_path(self, user: User, version_id: uuid.UUID) -> tuple[MaterialVersion, Path]:
        mv = self.db.get(MaterialVersion, version_id)
        if mv is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Material version not found")
        item = self.db.get(MaterialChecklist, mv.checklist_item_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Material version not found")
        reg = self.db.get(Registration, item.registration_id)
        if reg is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Material version not found")
        ensure_registration_access(user, reg)
        path = Path(mv.file_path)
        if not path.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Material version not found")
        return mv, path

    def patch_label(
        self, user: User, registration_id: uuid.UUID, item_id: uuid.UUID, version_id: uuid.UUID, label: MaterialVersionLabel
    ) -> MaterialLabelResponse:
        if user.role != UserRole.applicant:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only applicants can update labels")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        if reg.applicant_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You do not own this registration")
        mv = self.db.get(MaterialVersion, version_id)
        item = self.db.get(MaterialChecklist, item_id)
        if mv is None or item is None or item.registration_id != reg.id or mv.checklist_item_id != item.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Material version not found")
        now = utcnow()
        activity = self.activities.get_by_id(reg.activity_id)
        if activity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Activity not found")
        update_registration_lock(reg, activity, now)
        if reg.status in (RegistrationStatus.needs_correction, RegistrationStatus.supplemented):
            if reg.supplementary_deadline is None or now > (as_utc(reg.supplementary_deadline) or reg.supplementary_deadline):
                raise bad_request("SUPPLEMENTARY_EXPIRED", "The 72-hour supplementary window has expired")
        elif reg.is_locked or now > as_utc(activity.deadline):
            raise bad_request("DEADLINE_PASSED", "Upload deadline has passed")
        if reg.status not in (RegistrationStatus.draft, RegistrationStatus.needs_correction, RegistrationStatus.supplemented):
            raise bad_request("INVALID_STATE_TRANSITION", "Material labels can only be changed in editable states")
        mv.label = label
        mv.updated_at = now
        reg.updated_at = now
        self.db.commit()
        self.db.refresh(mv)
        return MaterialLabelResponse(id=mv.id, label=mv.label, updated_at=mv.updated_at)
