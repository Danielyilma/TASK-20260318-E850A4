from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_financial_admin, require_financial_or_system_admin
from app.core.http_errors import bad_request
from app.models.enums import TransactionType
from app.models.user import User
from app.schemas.registration_domain import TransactionCreate, TransactionUpdate
from app.services.phase4_funding import Phase4FundingService

router = APIRouter(tags=["funding"])


def _parse_iso_dt(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise bad_request("VALIDATION_ERROR", "Invalid ISO datetime for date filter") from exc


def _svc(db: Session = Depends(get_db)) -> Phase4FundingService:
    return Phase4FundingService(db)


@router.get("/registrations/{registration_id}/funding")
def get_funding_for_registration(
    registration_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    return svc.get_by_registration(user, registration_id)


@router.get("/funding-accounts")
def list_funding_accounts(
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    is_overspent: bool | None = None,
    activity_id: uuid.UUID | None = None,
):
    return svc.list_accounts(user, page=page, per_page=per_page, is_overspent=is_overspent, activity_id=activity_id)


@router.get("/funding-accounts/{account_id}")
def get_funding_account(
    account_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    return svc.get_account(user, account_id)


@router.post("/funding-accounts/{account_id}/transactions", status_code=status.HTTP_201_CREATED)
def post_transaction(
    account_id: uuid.UUID,
    payload: TransactionCreate,
    user: Annotated[User, Depends(require_financial_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    kind, data = svc.create_transaction(user, account_id, payload)
    if kind == "warn":
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "OVERSPEND_CONFIRMATION_REQUIRED",
                    "message": data["message"],
                },
                **{k: v for k, v in data.items() if k != "message"},
            },
        )
    return data


@router.put("/funding-accounts/{account_id}/transactions/{transaction_id}")
def put_transaction(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    user: Annotated[User, Depends(require_financial_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    kind, data = svc.update_transaction(user, account_id, transaction_id, payload)
    if kind == "warn":
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "OVERSPEND_CONFIRMATION_REQUIRED",
                    "message": data["message"],
                },
                **{k: v for k, v in data.items() if k != "message"},
            },
        )
    return data


@router.get("/funding-accounts/{account_id}/transactions")
def list_transactions(
    account_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    type_filter: TransactionType | None = Query(default=None, alias="type"),
    category: str | None = None,
    sort: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    return svc.list_transactions(
        user,
        account_id,
        page=page,
        per_page=per_page,
        type_filter=type_filter,
        category=category,
        sort=sort,
        start_date=_parse_iso_dt(start_date),
        end_date=_parse_iso_dt(end_date),
    )


@router.get("/funding-accounts/{account_id}/transactions/{transaction_id}")
def get_transaction(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    return svc.get_transaction(user, account_id, transaction_id)


@router.delete("/funding-accounts/{account_id}/transactions/{transaction_id}")
def delete_transaction(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    return svc.delete_transaction(user, account_id, transaction_id)


@router.post("/funding-accounts/{account_id}/transactions/{transaction_id}/invoice", status_code=status.HTTP_201_CREATED)
async def post_invoice(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_admin)],
    file: UploadFile = File(...),
    svc: Phase4FundingService = Depends(_svc),
):
    return await svc.upload_invoice(user, account_id, transaction_id, file)


@router.get("/funding-accounts/{account_id}/transactions/{transaction_id}/invoice")
def get_invoice(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    user: Annotated[User, Depends(require_financial_or_system_admin)],
    svc: Phase4FundingService = Depends(_svc),
):
    path = svc.download_invoice(user, account_id, transaction_id)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
