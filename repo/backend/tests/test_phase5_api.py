from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.activity import Activity
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_login_validation_error_has_error_envelope(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/login", json={})
    assert r.status_code in (400, 422)
    data = r.json()
    if r.status_code == 400 and "error" in data:
        assert "code" in data["error"]


@pytest.mark.asyncio
async def test_similarity_returns_501_shape(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/similarity/check",
        headers=admin_headers,
        json={"registration_id": str(uuid.uuid4()), "check_type": "content_similarity"},
    )
    assert r.status_code == 501
    body = r.json()
    assert body["error"]["code"] == "NOT_IMPLEMENTED"


@pytest.mark.asyncio
async def test_metrics_quality_ok(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.get("/api/v1/metrics/quality", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    for key in (
        "total_registrations",
        "approval_rate",
        "correction_rate",
        "overspending_rate",
        "computed_at",
    ):
        assert key in data


@pytest.mark.asyncio
async def test_audit_logs_include_login(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.get("/api/v1/audit-logs", headers=admin_headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(x.get("action") == "login" for x in items)


@pytest.mark.asyncio
async def test_alerts_list_paginated(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.get("/api/v1/alerts", headers=admin_headers)
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_data_collection_batch_create_and_execute(
    client: AsyncClient, admin_headers: dict[str, str], db_session: Session
) -> None:
    now = utcnow()
    aid = uuid.uuid4()
    db_session.add(
        Activity(
            id=aid,
            name="P5 Act",
            description=None,
            deadline=now + timedelta(days=30),
            budget=Decimal("50000"),
            is_active=True,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    b = await client.post(
        "/api/v1/data-collection/batches",
        headers=admin_headers,
        json={
            "name": "Test batch",
            "scope_whitelist": {
                "activity_ids": [str(aid)],
                "statuses": ["draft"],
                "validation_types": ["type_check"],
            },
        },
    )
    assert b.status_code == 201, b.text
    bid = b.json()["id"]
    ex = await client.patch(f"/api/v1/data-collection/batches/{bid}/execute", headers=admin_headers)
    assert ex.status_code == 200, ex.text
    assert ex.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_report_audit_csv_download(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/reports/audit",
        headers=admin_headers,
        json={"format": "csv"},
    )
    assert r.status_code == 201, r.text
    rid = r.json()["report_id"]
    dl = await client.get(f"/api/v1/reports/{rid}/download", headers=admin_headers)
    assert dl.status_code == 200
    assert len(dl.content) > 0


@pytest.mark.asyncio
async def test_metrics_forbidden_for_applicant(
    client: AsyncClient, db_session: Session
) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="p5_applicant_only",
        password_hash=ph,
        salt=sl,
        role=UserRole.applicant,
        id_number=None,
        contact_info=None,
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(u)
    db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "p5_applicant_only", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    r = await client.get("/api/v1/metrics/quality", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_report_download_financial_owner_only(client: AsyncClient, admin_headers: dict[str, str], db_session: Session) -> None:
    now = utcnow()
    ph1, sl1 = hash_password_with_salt("SecureP@ss1")
    ph2, sl2 = hash_password_with_salt("SecureP@ss1")
    u1 = User(
        id=uuid.uuid4(),
        username=f"p5_fin_owner_{uuid.uuid4().hex[:6]}",
        password_hash=ph1,
        salt=sl1,
        role=UserRole.financial_admin,
        id_number=None,
        contact_info=None,
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    u2 = User(
        id=uuid.uuid4(),
        username=f"p5_fin_other_{uuid.uuid4().hex[:6]}",
        password_hash=ph2,
        salt=sl2,
        role=UserRole.financial_admin,
        id_number=None,
        contact_info=None,
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([u1, u2])
    db_session.commit()
    l1 = await client.post("/api/v1/auth/login", json={"username": u1.username, "password": "SecureP@ss1"})
    l2 = await client.post("/api/v1/auth/login", json={"username": u2.username, "password": "SecureP@ss1"})
    h1 = {"Authorization": f"Bearer {l1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {l2.json()['access_token']}"}

    created = await client.post("/api/v1/reports/reconciliation", headers=h1, json={"format": "pdf"})
    assert created.status_code == 201, created.text
    rid = created.json()["report_id"]

    owner_dl = await client.get(f"/api/v1/reports/{rid}/download", headers=h1)
    assert owner_dl.status_code == 200
    other_dl = await client.get(f"/api/v1/reports/{rid}/download", headers=h2)
    assert other_dl.status_code == 403
    admin_dl = await client.get(f"/api/v1/reports/{rid}/download", headers=admin_headers)
    assert admin_dl.status_code == 200


@pytest.mark.asyncio
async def test_invalid_iso_dates_return_400(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    bad_quality = await client.get("/api/v1/metrics/quality?start_date=nope", headers=admin_headers)
    assert bad_quality.status_code == 400
    assert bad_quality.json()["error"]["code"] == "VALIDATION_ERROR"
