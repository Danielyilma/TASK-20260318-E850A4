from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import SessionLocal
from app.services.audit_log_service import AuditLogService


class AuditMiddleware(BaseHTTPMiddleware):
    """Persist audit rows for mutating API calls after the response is produced."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        try:
            if request.scope.get("type") != "http":
                return response
            method = request.method.upper()
            path = request.url.path
            if method not in ("POST", "PUT", "PATCH", "DELETE"):
                return response
            if not path.startswith("/api/v1"):
                return response
            if path.startswith("/api/v1/health") or path.startswith("/api/v1/auth/login"):
                return response
            ip = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization")
            db = SessionLocal()
            try:
                AuditLogService(db).log_http_request(
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    authorization=auth,
                    ip_address=ip,
                )
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            # Never break the response path for audit failures
            pass
        return response
