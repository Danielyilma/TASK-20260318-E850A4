from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.funding_account import FundingAccount
from app.models.registration import Registration
from app.models.transaction_record import TransactionRecord


class Phase5FundingStatisticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def aggregate(
        self,
        *,
        activity_id: uuid.UUID | None,
        category: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        group_by: str,
    ) -> dict:
        group_by = (group_by or "category").lower()
        if group_by not in ("category", "month", "quarter"):
            group_by = "category"

        fa_stmt = select(FundingAccount)
        if activity_id is not None:
            fa_stmt = fa_stmt.join(Registration, FundingAccount.registration_id == Registration.id).where(
                Registration.activity_id == activity_id
            )
        accounts = list(self.db.scalars(fa_stmt).all())
        total_accounts = len(accounts)
        total_approved = sum((fa.approved_budget for fa in accounts), Decimal("0"))
        total_income = sum((fa.total_income for fa in accounts), Decimal("0"))
        total_expenses = sum((fa.total_expenses for fa in accounts), Decimal("0"))
        balance = total_income - total_expenses
        overspent_accounts = sum(1 for fa in accounts if fa.total_expenses > fa.approved_budget)
        overspending_rate = (
            round(float((Decimal(overspent_accounts) / Decimal(total_accounts)) * Decimal("100")), 2)
            if total_accounts
            else 0.0
        )

        inc_sum = func.coalesce(
            func.sum(case((TransactionRecord.type == "income", TransactionRecord.amount), else_=0)),
            0,
        )
        exp_sum = func.coalesce(
            func.sum(case((TransactionRecord.type == "expense", TransactionRecord.amount), else_=0)),
            0,
        )

        def _tx_base():
            return (
                select(TransactionRecord)
                .join(FundingAccount, TransactionRecord.funding_account_id == FundingAccount.id)
                .join(Registration, FundingAccount.registration_id == Registration.id)
            )

        filters = []
        if activity_id is not None:
            filters.append(Registration.activity_id == activity_id)
        if category:
            filters.append(TransactionRecord.category == category)
        if start_date is not None:
            filters.append(TransactionRecord.created_at >= start_date)
        if end_date is not None:
            filters.append(TransactionRecord.created_at <= end_date)

        by_category: list[dict] = []
        if group_by == "category":
            q = (
                select(
                    TransactionRecord.category,
                    inc_sum.label("ti"),
                    exp_sum.label("te"),
                    func.count(TransactionRecord.id),
                )
                .join(FundingAccount, TransactionRecord.funding_account_id == FundingAccount.id)
                .join(Registration, FundingAccount.registration_id == Registration.id)
                .group_by(TransactionRecord.category)
            )
            if filters:
                q = q.where(*filters)
            for cat, inc, exp, cnt in self.db.execute(q).all():
                by_category.append(
                    {
                        "category": cat,
                        "total_income": float(inc or 0),
                        "total_expenses": float(exp or 0),
                        "transaction_count": int(cnt or 0),
                    }
                )

        by_time: list[dict] = []
        if group_by in ("month", "quarter"):
            dialect = self.db.get_bind().dialect.name
            if dialect == "postgresql":
                if group_by == "month":
                    period_expr = func.to_char(func.date_trunc("month", TransactionRecord.created_at), "YYYY-MM")
                else:
                    period_expr = func.concat(
                        func.extract("year", TransactionRecord.created_at),
                        "-Q",
                        func.extract("quarter", TransactionRecord.created_at),
                    )
            else:
                # SQLite fallback for tests/local static runs.
                if group_by == "month":
                    period_expr = func.strftime("%Y-%m", TransactionRecord.created_at)
                else:
                    period_expr = func.strftime("%Y", TransactionRecord.created_at)
            q2 = (
                select(
                    period_expr.label("period"),
                    inc_sum.label("ti"),
                    exp_sum.label("te"),
                    func.count(TransactionRecord.id),
                )
                .join(FundingAccount, TransactionRecord.funding_account_id == FundingAccount.id)
                .join(Registration, FundingAccount.registration_id == Registration.id)
                .group_by(period_expr)
            )
            if filters:
                q2 = q2.where(*filters)
            for period, inc, exp, cnt in self.db.execute(q2).all():
                by_time.append(
                    {
                        "period": str(period),
                        "total_income": float(inc or 0),
                        "total_expenses": float(exp or 0),
                        "transaction_count": int(cnt or 0),
                    }
                )

        return {
            "summary": {
                "total_accounts": total_accounts,
                "total_approved_budget": float(total_approved),
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "total_balance": float(balance),
                "overspent_accounts": overspent_accounts,
                "overspending_rate": overspending_rate,
            },
            "by_category": by_category,
            "by_time": by_time,
        }

    def for_account(self, account_id: uuid.UUID) -> dict:
        fa = self.db.get(FundingAccount, account_id)
        if fa is None:
            from fastapi import HTTPException, status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Funding account not found")
        pct = (
            float((fa.total_expenses / fa.approved_budget - Decimal("1")) * Decimal("100"))
            if fa.approved_budget > 0
            else 0.0
        )
        exp_sum = func.coalesce(
            func.sum(case((TransactionRecord.type == "expense", TransactionRecord.amount), else_=0)),
            0,
        )
        q = (
            select(TransactionRecord.category, exp_sum, func.count(TransactionRecord.id))
            .where(TransactionRecord.funding_account_id == fa.id)
            .group_by(TransactionRecord.category)
        )
        by_cat = []
        for cat, exp, cnt in self.db.execute(q).all():
            by_cat.append(
                {
                    "category": cat,
                    "total_expenses": float(exp or 0),
                    "transaction_count": int(cnt or 0),
                }
            )
        return {
            "account_id": str(fa.id),
            "approved_budget": float(fa.approved_budget),
            "total_income": float(fa.total_income),
            "total_expenses": float(fa.total_expenses),
            "balance": float(fa.total_income - fa.total_expenses),
            "overspend_percentage": round(pct, 2),
            "is_overspent": fa.total_expenses > fa.approved_budget,
            "by_category": by_cat,
        }
