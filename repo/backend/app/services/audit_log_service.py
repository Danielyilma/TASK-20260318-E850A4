from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.core.token_blocklist import is_jti_revoked
from app.core.security import decode_access_token
from app.models.audit_log import AuditLog
from app.models.user import User


_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def extract_resource_from_path(path: str) -> tuple[str | None, uuid.UUID | None]:
    """Infer resource_type and primary resource UUID from /api/v1/... paths."""
    if not path.startswith("/api/v1"):
        return None, None
    rest = path[len("/api/v1") :].strip("/")
    parts = [p for p in rest.split("/") if p]
    if not parts:
        return None, None
    resource_type = parts[0].replace("-", "_")
    # normalize funding_accounts -> funding_account style for API naming
    if resource_type == "funding_accounts":
        resource_type = "funding_account"
    if resource_type == "data_collection":
        resource_type = "data_collection_batch"
    for p in parts[1:]:
        try:
            return resource_type, uuid.UUID(p)
        except ValueError:
            continue
    return resource_type, None


def infer_action(method: str, path: str) -> str:
    path_l = path.lower()
    if "/review" in path_l or "/reviews/batch" in path_l:
        return "review"
    if "/materials/" in path_l and "/upload" in path_l:
        return "upload"
    if "/transactions" in path_l:
        return "transaction"
    if "/invoice" in path_l:
        return "invoice_upload"
    if "/verify-sensitive" in path_l:
        return "verify_sensitive"
    if "/checklist" in path_l:
        return "checklist"
    if "/execute" in path_l:
        return "batch_execute"
    if "/logout" in path_l:
        return "logout"
    if "/change-password" in path_l:
        return "password_change"
    if method == "POST" and "/registrations" in path_l and path_l.rstrip("/").endswith("registrations"):
        return "registration_create"
    return method.lower()


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def append(
        self,
        *,
        user_id: uuid.UUID | None,
        username: str | None,
        action: str,
        resource_type: str | None,
        resource_id: uuid.UUID | None,
        details: dict[str, Any] | None,
        ip_address: str,
    ) -> AuditLog:
        row = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            created_at=utcnow(),
        )
        self.db.add(row)
        return row

    def resolve_user_from_bearer(self, authorization: str | None) -> tuple[uuid.UUID | None, str | None]:
        if not authorization or not authorization.lower().startswith("bearer "):
            return None, None
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
        except Exception:
            return None, None
        jti = payload.get("jti")
        if not jti or is_jti_revoked(str(jti)):
            return None, None
        sub = payload.get("sub")
        if not sub:
            return None, None
        try:
            uid = uuid.UUID(str(sub))
        except ValueError:
            return None, None
        u = self.db.get(User, uid)
        if u is None:
            return uid, None
        return uid, u.username

    def log_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        authorization: str | None,
        ip_address: str,
    ) -> None:
        if method not in ("POST", "PUT", "PATCH", "DELETE"):
            return
        if not path.startswith("/api/v1"):
            return
        skip_prefixes = (
            "/api/v1/health",
            "/api/v1/auth/login",
        )
        if any(path.startswith(p) for p in skip_prefixes):
            return
        uid, username = self.resolve_user_from_bearer(authorization)
        rt, rid = extract_resource_from_path(path)
        action = infer_action(method, path)
        self.append(
            user_id=uid,
            username=username,
            action=action,
            resource_type=rt,
            resource_id=rid,
            details={"method": method, "path": path, "status_code": status_code},
            ip_address=ip_address,
        )
        self.db.commit()
