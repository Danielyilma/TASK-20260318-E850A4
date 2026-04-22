from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_financial_or_system_admin, require_system_admin
from app.core.http_errors import bad_request
from app.models.user import User
from app.services.phase5_alerts_service import Phase5AlertsService
from app.services.phase5_audit_query import Phase5AuditQueryService
from app.services.phase5_data_collection_service import Phase5DataCollectionService
from app.services.phase5_funding_statistics import Phase5FundingStatisticsService
from app.services.phase5_quality_metrics import Phase5QualityMetricsService
from app.services.phase5_reports_service import Phase5ReportsService

router = APIRouter(tags=["phase5"])


def _parse_iso_dt(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise bad_request("VALIDATION_ERROR", "Invalid ISO datetime for date filter") from exc


# --- Quality metrics ---
@router.get("/metrics/quality")
def get_quality_metrics(
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
    start_date: str | None = None,
    end_date: str | None = None,
):
    svc = Phase5QualityMetricsService(db)
    return svc.compute(start_date=_parse_iso_dt(start_date), end_date=_parse_iso_dt(end_date))


@router.get("/metrics/quality/{activity_id}")
def get_quality_metrics_activity(
    activity_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    return Phase5QualityMetricsService(db).for_activity(activity_id)


# --- Funding statistics ---
@router.get("/statistics/funding")
def get_funding_statistics(
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    db: Session = Depends(get_db),
    activity_id: uuid.UUID | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    group_by: str = Query(default="category"),
):
    return Phase5FundingStatisticsService(db).aggregate(
        activity_id=activity_id,
        category=category,
        start_date=_parse_iso_dt(start_date),
        end_date=_parse_iso_dt(end_date),
        group_by=group_by,
    )


@router.get("/statistics/funding/{account_id}")
def get_funding_statistics_account(
    account_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    db: Session = Depends(get_db),
):
    return Phase5FundingStatisticsService(db).for_account(account_id)


# --- Alerts ---
@router.get("/alerts")
def list_alerts(
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    severity: str | None = None,
    acknowledged: bool | None = None,
    alert_type: str | None = None,
):
    return Phase5AlertsService(db).list_page(
        page=page, per_page=per_page, severity=severity, acknowledged=acknowledged, alert_type=alert_type
    )


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    r = Phase5AlertsService(db).get(alert_id)
    return {
        "id": str(r.id),
        "alert_type": r.alert_type,
        "severity": r.severity,
        "message": r.message,
        "resource_type": r.resource_type,
        "resource_id": str(r.resource_id) if r.resource_id else None,
        "acknowledged": r.acknowledged,
        "acknowledged_by": str(r.acknowledged_by) if r.acknowledged_by else None,
        "acknowledged_at": r.acknowledged_at.isoformat().replace("+00:00", "Z") if r.acknowledged_at else None,
        "created_at": r.created_at.isoformat().replace("+00:00", "Z"),
    }


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    return Phase5AlertsService(db).acknowledge(admin, alert_id)


# --- Audit logs ---
@router.get("/audit-logs")
def list_audit_logs(
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort: str | None = None,
):
    return Phase5AuditQueryService(db).list_page(
        page=page,
        per_page=per_page,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=_parse_iso_dt(start_date),
        end_date=_parse_iso_dt(end_date),
        sort=sort,
    )


@router.get("/audit-logs/{log_id}")
def get_audit_log(
    log_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    a = Phase5AuditQueryService(db).get(log_id)
    u = db.get(User, a.user_id) if a.user_id else None
    return {
        "id": str(a.id),
        "user_id": str(a.user_id) if a.user_id else None,
        "username": a.username or (u.username if u else None),
        "action": a.action,
        "resource_type": a.resource_type,
        "resource_id": str(a.resource_id) if a.resource_id else None,
        "details": a.details or {},
        "ip_address": a.ip_address,
        "created_at": a.created_at.isoformat().replace("+00:00", "Z"),
    }


# --- Data collection ---
class DataCollectionBatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scope_whitelist: dict[str, Any]


def _batch_to_dict(b) -> dict:
    return {
        "id": str(b.id),
        "name": b.name,
        "scope_whitelist": b.scope_whitelist,
        "status": b.status,
        "created_by": str(b.created_by),
        "created_at": b.created_at.isoformat().replace("+00:00", "Z"),
        "completed_at": b.completed_at.isoformat().replace("+00:00", "Z") if b.completed_at else None,
        "error_message": b.error_message,
    }


@router.post("/data-collection/batches", status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: DataCollectionBatchCreate,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    b = Phase5DataCollectionService(db).create(admin, payload.name, payload.scope_whitelist)
    return _batch_to_dict(b)


@router.get("/data-collection/batches")
def list_batches(
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
):
    data = Phase5DataCollectionService(db).list_page(page=page, per_page=per_page, status=status)
    return {
        "items": [_batch_to_dict(b) for b in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "per_page": data["per_page"],
        "pages": data["pages"],
    }


@router.get("/data-collection/batches/{batch_id}")
def get_batch(
    batch_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    return _batch_to_dict(Phase5DataCollectionService(db).get_batch(batch_id))


@router.patch("/data-collection/batches/{batch_id}/execute")
def execute_batch(
    batch_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    return Phase5DataCollectionService(db).execute(admin, batch_id)


@router.get("/data-collection/batches/{batch_id}/results")
def batch_results(
    batch_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    is_valid: bool | None = None,
):
    return Phase5DataCollectionService(db).list_results(batch_id, page=page, per_page=per_page, is_valid=is_valid)


# --- Reports ---
class ReconciliationReportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    activity_id: uuid.UUID | None = None
    start_date: str | None = None
    end_date: str | None = None
    file_format: str = Field(alias="format")


class AuditReportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    start_date: str | None = None
    end_date: str | None = None
    user_id: uuid.UUID | None = None
    action_filter: str | None = None
    file_format: str = Field(alias="format")


class ComplianceReportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    activity_id: uuid.UUID
    file_format: str = Field(alias="format")


def _report_created(rep) -> dict:
    return {
        "report_id": str(rep.id),
        "report_type": rep.report_type,
        "status": rep.status,
        "file_name": rep.file_name,
        "file_size_bytes": rep.file_size_bytes,
        "created_at": rep.created_at.isoformat().replace("+00:00", "Z"),
    }


@router.post("/reports/reconciliation", status_code=status.HTTP_201_CREATED)
def post_reconciliation_report(
    payload: ReconciliationReportRequest,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    db: Session = Depends(get_db),
):
    rep = Phase5ReportsService(db).generate_reconciliation(
        user,
        activity_id=payload.activity_id,
        start_date=_parse_iso_dt(payload.start_date),
        end_date=_parse_iso_dt(payload.end_date),
        file_format=payload.file_format,
    )
    return _report_created(rep)


@router.post("/reports/audit", status_code=status.HTTP_201_CREATED)
def post_audit_report(
    payload: AuditReportRequest,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    rep = Phase5ReportsService(db).generate_audit_report(
        admin,
        start_date=_parse_iso_dt(payload.start_date),
        end_date=_parse_iso_dt(payload.end_date),
        user_id=payload.user_id,
        action_filter=payload.action_filter,
        file_format=payload.file_format,
    )
    return _report_created(rep)


@router.post("/reports/compliance", status_code=status.HTTP_201_CREATED)
def post_compliance_report(
    payload: ComplianceReportRequest,
    admin: Annotated[User, Depends(require_system_admin)],
    db: Session = Depends(get_db),
):
    rep = Phase5ReportsService(db).generate_compliance(
        admin, activity_id=payload.activity_id, file_format=payload.file_format
    )
    return _report_created(rep)


@router.get("/reports")
def list_reports(
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    report_type: str | None = None,
    report_format: str | None = Query(default=None, alias="format"),
):
    return Phase5ReportsService(db).list_reports(
        page=page, per_page=per_page, report_type=report_type, file_format=report_format
    )


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    db: Session = Depends(get_db),
):
    path = Phase5ReportsService(db).download_path(report_id, user)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


# --- Similarity (reserved) ---
class SimilarityCheckRequest(BaseModel):
    registration_id: uuid.UUID
    check_type: str


@router.post("/similarity/check")
def similarity_check(
    _payload: SimilarityCheckRequest,
    _admin: Annotated[User, Depends(require_system_admin)],
):
    return JSONResponse(
        status_code=501,
        content={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Similarity/duplicate check is reserved but currently disabled",
            }
        },
    )

