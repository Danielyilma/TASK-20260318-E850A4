import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.database import SessionLocal
from app.core.config import get_settings, parse_cors_origins
from app.exceptions import AppError
from app.middleware import AuditMiddleware
from app.middleware.maintenance_middleware import MaintenanceMiddleware
from app.schemas.errors import ErrorBody, ErrorResponse
from app.services.backup_service import BackupService

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(MaintenanceMiddleware)

_backup_scheduler_started = False


def _run_backup_scheduler() -> None:
    while True:
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=settings.backup_daily_hour_utc, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)
        sleep_seconds = max(30, int((next_run - now).total_seconds()))
        time.sleep(sleep_seconds)
        db = SessionLocal()
        try:
            svc = BackupService(db)
            svc.create_daily_auto()
            svc.prune_old_backups(retention_days=settings.backup_retention_days)
        except Exception:
            # Keep scheduler alive even when one backup attempt fails.
            pass
        finally:
            db.close()


@app.on_event("startup")
def start_backup_scheduler() -> None:
    global _backup_scheduler_started
    if _backup_scheduler_started or not settings.backup_daily_enabled:
        return
    _backup_scheduler_started = True
    t = threading.Thread(target=_run_backup_scheduler, name="backup-scheduler", daemon=True)
    t.start()


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = exc.headers.get("X-Error-Code") if exc.headers else None
    if not code:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_409_CONFLICT:
            code = "CONFLICT"
        elif exc.status_code == status.HTTP_423_LOCKED:
            code = "ACCOUNT_LOCKED"
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "VALIDATION_ERROR"
        else:
            code = "INTERNAL_ERROR"
    body = ErrorResponse(error=ErrorBody(code=code, message=str(exc.detail)))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = "Request validation failed"
    if exc.errors():
        first = exc.errors()[0]
        loc = ".".join(str(x) for x in first.get("loc", ()) if x != "body")
        message = f"{loc}: {first.get('msg', 'invalid')}" if loc else str(first.get("msg", message))
    body = ErrorResponse(error=ErrorBody(code="VALIDATION_ERROR", message=message))
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code="INTERNAL_ERROR", message="An unexpected error occurred"),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())


app.include_router(api_router, prefix="/api/v1")
