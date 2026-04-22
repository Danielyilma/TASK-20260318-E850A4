from __future__ import annotations

import math
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


class Phase5AuditQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_page(
        self,
        *,
        page: int,
        per_page: int,
        user_id: uuid.UUID | None,
        action: str | None,
        resource_type: str | None,
        resource_id: uuid.UUID | None,
        start_date: datetime | None,
        end_date: datetime | None,
        sort: str | None,
    ) -> dict:
        filters = []
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if action:
            filters.append(AuditLog.action == action)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)

        count_q = select(func.count()).select_from(AuditLog)
        if filters:
            count_q = count_q.where(*filters)
        total = int(self.db.scalar(count_q) or 0)

        q = select(AuditLog, User.username).outerjoin(User, AuditLog.user_id == User.id)
        if filters:
            q = q.where(*filters)
        order = AuditLog.created_at.desc()
        if sort and not sort.startswith("-"):
            order = AuditLog.created_at.asc()
        rows = self.db.execute(
            q.order_by(order).offset((page - 1) * per_page).limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        items = []
        for a, uname in rows:
            items.append(
                {
                    "id": str(a.id),
                    "user_id": str(a.user_id) if a.user_id else None,
                    "username": a.username or uname,
                    "action": a.action,
                    "resource_type": a.resource_type,
                    "resource_id": str(a.resource_id) if a.resource_id else None,
                    "details": a.details or {},
                    "ip_address": a.ip_address,
                    "created_at": a.created_at.isoformat().replace("+00:00", "Z"),
                }
            )
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    def get(self, log_id: uuid.UUID) -> AuditLog:
        row = self.db.get(AuditLog, log_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Audit log not found")
        return row
