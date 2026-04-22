from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.maintenance import is_maintenance_mode


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Reject traffic while a restore is running; health stays available for probes."""

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if path.startswith("/api/v1/health"):
            return await call_next(request)
        if is_maintenance_mode():
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "System is temporarily unavailable for maintenance (restore in progress)",
                    }
                },
            )
        return await call_next(request)
