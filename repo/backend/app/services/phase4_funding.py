from __future__ import annotations

from app.core.business_rules import OVERSPEND_THRESHOLD_MULTIPLIER

import math
import uuid
from decimal import Decimal
from pathlib import Path

from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.http_errors import forbidden
from app.core.time import utcnow
from app.models.enums import RegistrationStatus, TransactionType, UserRole
from app.models.funding_account import FundingAccount
from app.models.registration import Registration
from app.models.transaction_record import TransactionRecord
from app.models.user import User
from app.schemas.registration_domain import (
    FundingAccountListItem,
    FundingAccountListPage,
    FundingAccountRead,
    TransactionCreate,
    TransactionDeleteResponse,
    TransactionListPage,
    TransactionRead,
    TransactionUpdate,
)
from app.services.phase4_access import ensure_registration


def _funding_read(fa: FundingAccount) -> FundingAccountRead:
    balance = fa.total_income - fa.total_expenses
    threshold = fa.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER
    pct = float((fa.total_expenses / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
    is_overspent = fa.total_expenses > threshold
    return FundingAccountRead(
        id=fa.id,
        registration_id=fa.registration_id,
        approved_budget=fa.approved_budget,
        total_income=fa.total_income,
        total_expenses=fa.total_expenses,
        balance=balance,
        is_overspent=is_overspent,
        overspend_percentage=round(pct, 2),
        created_at=fa.created_at,
        updated_at=fa.updated_at,
    )


def _funding_list_item(fa: FundingAccount) -> FundingAccountListItem:
    balance = fa.total_income - fa.total_expenses
    threshold = fa.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER
    pct = float((fa.total_expenses / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
    is_overspent = fa.total_expenses > threshold
    return FundingAccountListItem(
        id=fa.id,
        registration_id=fa.registration_id,
        approved_budget=fa.approved_budget,
        total_income=fa.total_income,
        total_expenses=fa.total_expenses,
        balance=balance,
        is_overspent=is_overspent,
        created_at=fa.created_at,
    )


class Phase4FundingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _require_finance(self, user: User) -> None:
        if user.role not in (UserRole.financial_admin, UserRole.system_admin):
            raise forbidden("FORBIDDEN", "Insufficient permissions")

    def get_by_registration(self, user: User, registration_id: uuid.UUID) -> FundingAccountRead:
        self._require_finance(user)
        reg = self.db.get(Registration, registration_id)
        if reg is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registration not found")
        fa = self.db.scalars(
            select(FundingAccount).where(FundingAccount.registration_id == registration_id)
        ).first()
        if fa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registration or funding account not found")
        return _funding_read(fa)

    def list_accounts(
        self,
        user: User,
        *,
        page: int,
        per_page: int,
        is_overspent: bool | None,
        activity_id: uuid.UUID | None,
    ) -> FundingAccountListPage:
        self._require_finance(user)
        filters = []
        if is_overspent is not None:
            if is_overspent:
                filters.append(FundingAccount.total_expenses > FundingAccount.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER)
            else:
                filters.append(FundingAccount.total_expenses <= FundingAccount.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER)
        if activity_id is not None:
            filters.append(Registration.activity_id == activity_id)

        base = select(FundingAccount).join(Registration, FundingAccount.registration_id == Registration.id)
        if filters:
            base = base.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        rows = self.db.scalars(
            base.order_by(FundingAccount.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        return FundingAccountListPage(
            items=[_funding_list_item(fa) for fa in rows],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get_account(self, user: User, account_id: uuid.UUID) -> FundingAccountRead:
        self._require_finance(user)
        fa = self.db.get(FundingAccount, account_id)
        if fa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Funding account not found")
        return _funding_read(fa)

    def create_transaction(
        self, user: User, account_id: uuid.UUID, payload: TransactionCreate
    ) -> tuple[str, TransactionRead | dict]:
        if user.role != UserRole.financial_admin:
            raise forbidden("FORBIDDEN", "Only financial administrators can record transactions")
        fa = self.db.get(FundingAccount, account_id)
        if fa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Funding account not found")

        projected = fa.total_expenses
        if payload.type == TransactionType.expense:
            projected = fa.total_expenses + payload.amount
        threshold = fa.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER
        if payload.type == TransactionType.expense and projected > threshold and not (payload.override_confirmed or False):
            pct = float((projected / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
            return (
                "warn",
                {
                    "overspend_warning": True,
                    "current_total_expenses": float(fa.total_expenses),
                    "approved_budget": float(fa.approved_budget),
                    "overspend_percentage": round(pct, 2),
                    "threshold": 10.0,
                    "message": "This transaction would bring total expenses to over 110% of the approved budget. Secondary confirmation required.",
                    "pending_transaction": {
                        "type": payload.type.value,
                        "amount": float(payload.amount),
                        "category": payload.category,
                        "description": payload.description,
                    },
                    "confirmation_required": True,
                },
            )

        now = utcnow()
        tx = TransactionRecord(
            id=uuid.uuid4(),
            funding_account_id=fa.id,
            type=payload.type,
            amount=payload.amount,
            category=payload.category,
            description=payload.description,
            invoice_file_path=None,
            recorded_by=user.id,
            created_at=now,
        )
        self.db.add(tx)
        if payload.type == TransactionType.expense:
            fa.total_expenses = fa.total_expenses + payload.amount
        else:
            fa.total_income = fa.total_income + payload.amount
        fa.updated_at = now
        self.db.commit()
        self.db.refresh(tx)
        self.db.refresh(fa)
        from app.services.phase5_alerts_service import Phase5AlertsService
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService

        Phase5AlertsService.maybe_create_overspend_alert(self.db, fa)
        reg = self.db.get(Registration, fa.registration_id)
        if reg:
            Phase5QualityMetricsService(self.db).compute(activity_id=reg.activity_id)
        self.db.commit()
        read = TransactionRead.model_validate(tx)
        if payload.override_confirmed and payload.type == TransactionType.expense:
            pct = float((fa.total_expenses / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
            return (
                "ok",
                read.model_copy(update={"override_confirmed": True, "overspend_percentage": round(pct, 2)}),
            )
        return "ok", read

    def update_transaction(
        self, user: User, account_id: uuid.UUID, tx_id: uuid.UUID, payload: TransactionUpdate
    ) -> tuple[str, TransactionRead | dict]:
        if user.role != UserRole.financial_admin:
            raise forbidden("FORBIDDEN", "Only financial administrators can record transactions")
        tx = self.db.get(TransactionRecord, tx_id)
        fa = self.db.get(FundingAccount, account_id)
        if tx is None or fa is None or tx.funding_account_id != fa.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        def _as_tx_type(value: TransactionType | str) -> TransactionType:
            if isinstance(value, TransactionType):
                return value
            return TransactionType(str(value))

        patch = payload.model_dump(exclude_unset=True)
        new_type = _as_tx_type(patch.get("type", tx.type))
        new_amount = patch.get("amount", tx.amount)
        new_category = patch.get("category", tx.category)
        if "description" in patch:
            new_description = patch["description"]
        else:
            new_description = tx.description

        te = fa.total_expenses
        ti = fa.total_income
        if _as_tx_type(tx.type) == TransactionType.expense:
            te -= tx.amount
        else:
            ti -= tx.amount

        projected_te = te + new_amount if new_type == TransactionType.expense else te
        threshold = fa.approved_budget * OVERSPEND_THRESHOLD_MULTIPLIER
        override = bool(patch.get("override_confirmed", False))
        if new_type == TransactionType.expense and projected_te > threshold and not override:
            pct = float((projected_te / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
            return (
                "warn",
                {
                    "overspend_warning": True,
                    "current_total_expenses": float(fa.total_expenses),
                    "approved_budget": float(fa.approved_budget),
                    "overspend_percentage": round(pct, 2),
                    "threshold": 10.0,
                    "message": "Updated amount would bring total expenses to over 110% of the approved budget. Secondary confirmation required.",
                    "pending_transaction": {
                        "type": new_type.value,
                        "amount": float(new_amount),
                        "category": new_category,
                        "description": new_description,
                    },
                    "confirmation_required": True,
                },
            )

        now = utcnow()
        fa.total_expenses = te
        fa.total_income = ti
        if new_type == TransactionType.expense:
            fa.total_expenses += new_amount
        else:
            fa.total_income += new_amount
        fa.updated_at = now

        tx.type = new_type
        tx.amount = new_amount
        tx.category = new_category
        tx.description = new_description

        self.db.commit()
        self.db.refresh(tx)
        self.db.refresh(fa)
        from app.services.phase5_alerts_service import Phase5AlertsService
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService

        Phase5AlertsService.maybe_create_overspend_alert(self.db, fa)
        reg = self.db.get(Registration, fa.registration_id)
        if reg:
            Phase5QualityMetricsService(self.db).compute(activity_id=reg.activity_id)
        self.db.commit()
        read = TransactionRead.model_validate(tx)
        if override and new_type == TransactionType.expense:
            pct = float((fa.total_expenses / fa.approved_budget - Decimal("1")) * Decimal("100")) if fa.approved_budget > 0 else 0.0
            return "ok", read.model_copy(update={"override_confirmed": True, "overspend_percentage": round(pct, 2)})
        return "ok", read

    def list_transactions(
        self,
        user: User,
        account_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
        type_filter: TransactionType | None,
        category: str | None,
        sort: str | None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TransactionListPage:
        self._require_finance(user)
        fa = self.db.get(FundingAccount, account_id)
        if fa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Funding account not found")
        filters = [TransactionRecord.funding_account_id == fa.id]
        if type_filter is not None:
            filters.append(TransactionRecord.type == type_filter)
        if category:
            filters.append(TransactionRecord.category == category)
        if start_date is not None:
            filters.append(TransactionRecord.created_at >= start_date)
        if end_date is not None:
            filters.append(TransactionRecord.created_at <= end_date)
        total = int(
            self.db.scalar(select(func.count()).select_from(TransactionRecord).where(*filters)) or 0
        )
        order = TransactionRecord.created_at.desc()
        if sort:
            desc = sort.startswith("-")
            name = sort[1:] if desc else sort
            col = getattr(TransactionRecord, name, None)
            if col is not None:
                order = col.desc() if desc else col.asc()
        rows = self.db.scalars(
            select(TransactionRecord)
            .where(*filters)
            .order_by(order)
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
        pages = math.ceil(total / per_page) if total else 0
        return TransactionListPage(
            items=[TransactionRead.model_validate(t) for t in rows],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get_transaction(self, user: User, account_id: uuid.UUID, tx_id: uuid.UUID) -> TransactionRead:
        self._require_finance(user)
        tx = self.db.get(TransactionRecord, tx_id)
        if tx is None or tx.funding_account_id != account_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return TransactionRead.model_validate(tx)

    def delete_transaction(self, user: User, account_id: uuid.UUID, tx_id: uuid.UUID) -> TransactionDeleteResponse:
        if user.role != UserRole.financial_admin:
            raise forbidden("FORBIDDEN", "Only financial administrators can record transactions")
        tx = self.db.get(TransactionRecord, tx_id)
        fa = self.db.get(FundingAccount, account_id)
        if tx is None or fa is None or tx.funding_account_id != fa.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        now = utcnow()
        if tx.type == TransactionType.expense:
            fa.total_expenses = fa.total_expenses - tx.amount
        else:
            fa.total_income = fa.total_income - tx.amount
        fa.updated_at = now
        self.db.delete(tx)
        
        from app.services.phase5_alerts_service import Phase5AlertsService
        from app.services.phase5_quality_metrics import Phase5QualityMetricsService
        Phase5AlertsService.maybe_create_overspend_alert(self.db, fa)
        reg = self.db.get(Registration, fa.registration_id)
        if reg:
            Phase5QualityMetricsService(self.db).compute(activity_id=reg.activity_id)
            
        self.db.commit()
        return TransactionDeleteResponse(message="Transaction deleted successfully")

    async def upload_invoice(
        self, user: User, account_id: uuid.UUID, tx_id: uuid.UUID, file: UploadFile
    ) -> dict:
        if user.role != UserRole.financial_admin:
            raise forbidden("FORBIDDEN", "Only financial administrators can record transactions")
        tx = self.db.get(TransactionRecord, tx_id)
        fa = self.db.get(FundingAccount, account_id)
        if tx is None or fa is None or tx.funding_account_id != fa.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        raw = await file.read()
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="File too large")
        ext = (file.filename or "bin").rsplit(".", 1)[-1].lower()
        if ext not in ("pdf", "jpg", "png"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid file type")
        settings = get_settings()
        root = Path(settings.upload_root) / "invoices" / str(account_id)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{tx_id}.{ext}"
        path.write_bytes(raw)
        tx.invoice_file_path = str(path)
        uploaded_at = utcnow()
        self.db.commit()
        return {
            "transaction_id": str(tx.id),
            "invoice_file_name": file.filename or path.name,
            "invoice_file_size_bytes": len(raw),
            "uploaded_at": uploaded_at.isoformat().replace("+00:00", "Z"),
        }

    def download_invoice(self, user: User, account_id: uuid.UUID, tx_id: uuid.UUID) -> Path:
        self._require_finance(user)
        tx = self.db.get(TransactionRecord, tx_id)
        if tx is None or tx.funding_account_id != account_id or not tx.invoice_file_path:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        p = Path(tx.invoice_file_path)
        if not p.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return p
