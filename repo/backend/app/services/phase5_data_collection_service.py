from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.data_collection_batch import DataCollectionBatch
from app.models.enums import MaterialVersionLabel, RegistrationStatus
from app.models.material_checklist import MaterialChecklist
from app.models.material_version import MaterialVersion
from app.models.quality_validation_result import QualityValidationResult
from app.models.registration import Registration
from app.models.user import User


class Phase5DataCollectionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, admin: User, name: str, scope_whitelist: dict[str, Any]) -> DataCollectionBatch:
        now = utcnow()
        batch = DataCollectionBatch(
            id=uuid.uuid4(),
            name=name,
            scope_whitelist=scope_whitelist,
            status="pending",
            created_by=admin.id,
            created_at=now,
            completed_at=None,
            error_message=None,
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_page(self, *, page: int, per_page: int, status: str | None) -> dict:
        q = select(DataCollectionBatch)
        if status:
            q = q.where(DataCollectionBatch.status == status)
        total = int(self.db.scalar(select(func.count()).select_from(q.subquery())) or 0)
        rows = self.db.scalars(
            q.order_by(DataCollectionBatch.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        return {"items": rows, "total": total, "page": page, "per_page": per_page, "pages": pages}

    def get_batch(self, batch_id: uuid.UUID) -> DataCollectionBatch:
        b = self.db.get(DataCollectionBatch, batch_id)
        if b is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Batch not found")
        return b

    def execute(self, _admin: User, batch_id: uuid.UUID) -> dict:
        batch = self.get_batch(batch_id)
        if batch.status != "pending":
            from app.core.http_errors import bad_request

            raise bad_request("INVALID_STATE_TRANSITION", "Batch is not in pending status")
        wl = batch.scope_whitelist or {}
        try:
            act_ids = [uuid.UUID(str(x)) for x in wl.get("activity_ids", [])]
        except ValueError:
            from app.core.http_errors import bad_request
            raise bad_request("VALIDATION_ERROR", "Invalid UUID in activity_ids whitelist")

        now = utcnow()
        batch.status = "in_progress"
        self.db.commit()

        try:
            statuses: list[RegistrationStatus] = []
            for s in wl.get("statuses", []):
                try:
                    statuses.append(RegistrationStatus(str(s)))
                except ValueError:
                    continue
            vtypes = list(wl.get("validation_types", []))

            q = select(Registration)
            filters = []
            if act_ids:
                filters.append(Registration.activity_id.in_(act_ids))
            if statuses:
                filters.append(Registration.status.in_(statuses))
            if filters:
                q = q.where(*filters)
            registrations = list(self.db.scalars(q).all())

            valid_ct = 0
            invalid_ct = 0
            for reg in registrations:
                for vt in vtypes:
                    ok, err = self._run_validation(reg, vt)
                    r = QualityValidationResult(
                        id=uuid.uuid4(),
                        batch_id=batch.id,
                        registration_id=reg.id,
                        validation_type=vt,
                        is_valid=ok,
                        error_details=err,
                        created_at=utcnow(),
                    )
                    self.db.add(r)
                    if ok:
                        valid_ct += 1
                    else:
                        invalid_ct += 1

            batch.status = "completed"
            batch.completed_at = utcnow()
            batch.error_message = None
            self.db.commit()
            total_validated = valid_ct + invalid_ct
            return {
                "batch_id": str(batch.id),
                "status": "completed",
                "total_validated": total_validated,
                "valid": valid_ct,
                "invalid": invalid_ct,
                "completed_at": batch.completed_at.isoformat().replace("+00:00", "Z"),
            }
        except Exception as e:
            self.db.rollback()
            batch = self.get_batch(batch_id)
            batch.status = "failed"
            batch.error_message = str(e)
            self.db.commit()
            raise

    def _run_validation(self, reg: Registration, vt: str) -> tuple[bool, str | None]:
        fd = reg.form_data or {}
        if vt == "type_check":
            if not isinstance(fd.get("project_title"), str):
                return False, "project_title must be string"
            tb = fd.get("target_beneficiaries")
            if not isinstance(tb, int):
                return False, "target_beneficiaries must be integer"
            return True, None
        if vt == "range_check":
            try:
                if float(reg.requested_funding) <= 0:
                    return False, "requested_funding must be positive"
            except Exception:
                return False, "requested_funding invalid"
            return True, None
        if vt == "mandatory_check":
            items = self.db.scalars(
                select(MaterialChecklist).where(MaterialChecklist.registration_id == reg.id)
            ).all()
            for it in items:
                if not it.is_required:
                    continue
                versions = self.db.scalars(
                    select(MaterialVersion).where(MaterialVersion.checklist_item_id == it.id)
                ).all()
                if not any(
                    (v.label == MaterialVersionLabel.submitted or str(v.label) == "submitted") for v in versions
                ):
                    return False, f"Missing required material: {it.item_name}"
            return True, None
        return True, None

    def list_results(
        self, batch_id: uuid.UUID, *, page: int, per_page: int, is_valid: bool | None
    ) -> dict:
        self.get_batch(batch_id)
        q = select(QualityValidationResult).where(QualityValidationResult.batch_id == batch_id)
        if is_valid is not None:
            q = q.where(QualityValidationResult.is_valid == is_valid)
        total = int(self.db.scalar(select(func.count()).select_from(q.subquery())) or 0)
        rows = self.db.scalars(
            q.order_by(QualityValidationResult.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        items = [
            {
                "id": str(r.id),
                "batch_id": str(r.batch_id),
                "registration_id": str(r.registration_id),
                "validation_type": r.validation_type,
                "is_valid": r.is_valid,
                "error_details": r.error_details,
                "created_at": r.created_at.isoformat().replace("+00:00", "Z"),
            }
            for r in rows
        ]
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}
