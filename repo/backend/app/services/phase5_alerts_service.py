from __future__ import annotations

import math
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.http_errors import api_error
from app.core.time import utcnow
from app.models.alert_record import AlertRecord
from app.models.enums import AlertSeverity
from app.models.funding_account import FundingAccount
from app.models.user import User


class Phase5AlertsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def maybe_create_overspend_alert(db: Session, fa: FundingAccount) -> None:
        threshold = fa.approved_budget * Decimal("1.10")
        if fa.total_expenses <= threshold:
            return
        existing = db.scalars(
            select(AlertRecord).where(
                AlertRecord.alert_type == "overspend_warning",
                AlertRecord.resource_type == "funding_account",
                AlertRecord.resource_id == fa.id,
                AlertRecord.acknowledged.is_(False),
            )
        ).first()
        if existing:
            return
        row = AlertRecord(
            id=uuid.uuid4(),
            alert_type="overspend_warning",
            severity=AlertSeverity.warning.value,
            message=f"Funding account {fa.id} exceeded 110% of approved budget",
            resource_type="funding_account",
            resource_id=fa.id,
            acknowledged=False,
            acknowledged_by=None,
            acknowledged_at=None,
            created_at=utcnow(),
        )
        db.add(row)

    def list_page(
        self,
        *,
        page: int,
        per_page: int,
        severity: str | None,
        acknowledged: bool | None,
        alert_type: str | None,
    ) -> dict:
        filters = []
        if severity:
            filters.append(AlertRecord.severity == severity)
        if acknowledged is not None:
            filters.append(AlertRecord.acknowledged == acknowledged)
        if alert_type:
            filters.append(AlertRecord.alert_type == alert_type)
        q = select(AlertRecord)
        if filters:
            q = q.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(q.subquery())) or 0)
        rows = self.db.scalars(
            q.order_by(AlertRecord.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        items = [
            {
                "id": str(r.id),
                "alert_type": r.alert_type,
                "severity": r.severity,
                "message": r.message,
                "resource_type": r.resource_type,
                "resource_id": str(r.resource_id) if r.resource_id else None,
                "acknowledged": r.acknowledged,
                "created_at": r.created_at.isoformat().replace("+00:00", "Z"),
            }
            for r in rows
        ]
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    def get(self, alert_id: uuid.UUID) -> AlertRecord:
        row = self.db.get(AlertRecord, alert_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return row

    def acknowledge(self, admin: User, alert_id: uuid.UUID) -> dict:
        row = self.get(alert_id)
        if row.acknowledged:
            raise api_error(status.HTTP_409_CONFLICT, "CONFLICT", "Alert already acknowledged")
        now = utcnow()
        row.acknowledged = True
        row.acknowledged_by = admin.id
        row.acknowledged_at = now
        self.db.commit()
        return {
            "id": str(row.id),
            "acknowledged": True,
            "acknowledged_by": str(admin.id),
            "acknowledged_at": now.isoformat().replace("+00:00", "Z"),
        }
