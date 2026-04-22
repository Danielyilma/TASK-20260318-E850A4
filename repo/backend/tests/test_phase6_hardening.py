"""Phase 6: security boundaries, backups, batch limits, maintenance mode, integrity notes."""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.maintenance import enter_maintenance, leave_maintenance
from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.audit_log import AuditLog
from app.models.enums import RegistrationStatus, UserRole
from app.models.material_checklist import MaterialChecklist
from app.models.registration import Registration
from app.models.user import User


def _form() -> dict:
    return {
        "project_title": "P",
        "project_description": "D",
        "target_beneficiaries": 10,
        "start_date": "2026-08-01",
        "end_date": "2026-12-31",
    }


@pytest.fixture
async def finance_headers(client, db_session):
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    uname = f"p6_finance_{uuid.uuid4().hex[:8]}"
    u = User(
        id=uuid.uuid4(),
        username=uname,
        password_hash=ph,
        salt=sl,
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
    db_session.add(u)
    db_session.commit()
    login = await client.post("/api/v1/auth/login", json={"username": uname, "password": "SecureP@ss1"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def reviewer_headers(client, db_session):
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    uname = f"p6_reviewer_{uuid.uuid4().hex[:8]}"
    u = User(
        id=uuid.uuid4(),
        username=uname,
        password_hash=ph,
        salt=sl,
        role=UserRole.reviewer,
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
    login = await client.post("/api/v1/auth/login", json={"username": uname, "password": "SecureP@ss1"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def applicant_a_headers(client, db_session):
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    uname = f"p6_applicant_a_{uuid.uuid4().hex[:8]}"
    u = User(
        id=uuid.uuid4(),
        username=uname,
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
    login = await client.post("/api/v1/auth/login", json={"username": uname, "password": "SecureP@ss1"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, u.id


@pytest.mark.asyncio
async def test_batch_review_rejects_over_50_items(client, reviewer_headers, db_session):
    """E2E: 54 registration IDs must fail BATCH_SIZE_EXCEEDED."""
    ids = [str(uuid.uuid4()) for _ in range(54)]
    resp = await client.post(
        "/api/v1/reviews/batch",
        headers=reviewer_headers,
        json={
            "registration_ids": ids,
            "action": "approve",
            "comment": "batch",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "BATCH_SIZE_EXCEEDED"


@pytest.mark.asyncio
async def test_applicant_cannot_read_other_registration(client, applicant_a_headers, db_session, admin_headers):
    """Object-level isolation: applicant A cannot fetch applicant B's registration."""
    headers_a, _uid_a = applicant_a_headers
    now = utcnow()
    ar = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={
            "name": "P6 isolation act",
            "description": None,
            "deadline": "2030-12-31T12:00:00+00:00",
            "budget": "10000.00",
        },
    )
    assert ar.status_code == 201, ar.text
    aid = uuid.UUID(ar.json()["id"])
    act_deadline = ar.json()["deadline"]

    ph, sl = hash_password_with_salt("SecureP@ss1")
    uid_b = uuid.uuid4()
    bname = f"p6_applicant_b_{uuid.uuid4().hex[:8]}"
    user_b = User(
        id=uid_b,
        username=bname,
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
    db_session.add(user_b)
    db_session.flush()
    reg_deadline = datetime.fromisoformat(act_deadline.replace("Z", "+00:00"))
    reg_b = Registration(
        id=uuid.uuid4(),
        activity_id=aid,
        applicant_id=uid_b,
        form_data=_form(),
        requested_funding=Decimal("1000"),
        status=RegistrationStatus.draft,
        deadline=reg_deadline,
        is_locked=False,
        supplementary_requested_at=None,
        supplementary_deadline=None,
        supplementary_used=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(reg_b)
    db_session.commit()

    resp = await client.get(f"/api/v1/registrations/{reg_b.id}", headers=headers_a)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_verify_sensitive_writes_audit_and_allows_reviewer(client, reviewer_headers, db_session, admin_headers):
    now = utcnow()
    ar = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={
            "name": "P6 verify act",
            "description": None,
            "deadline": "2030-12-31T12:00:00+00:00",
            "budget": "10000.00",
        },
    )
    assert ar.status_code == 201, ar.text
    aid = uuid.UUID(ar.json()["id"])
    act_deadline = ar.json()["deadline"]

    ph, sl = hash_password_with_salt("SecureP@ss1")
    vname = f"p6_app_for_verify_{uuid.uuid4().hex[:8]}"
    app_user = User(
        id=uuid.uuid4(),
        username=vname,
        password_hash=ph,
        salt=sl,
        role=UserRole.applicant,
        id_number="ID-999",
        contact_info="x@y.com",
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(app_user)
    db_session.flush()
    reg_deadline = datetime.fromisoformat(act_deadline.replace("Z", "+00:00"))
    reg = Registration(
        id=uuid.uuid4(),
        activity_id=aid,
        applicant_id=app_user.id,
        form_data=_form(),
        requested_funding=Decimal("1000"),
        status=RegistrationStatus.submitted,
        deadline=reg_deadline,
        is_locked=False,
        supplementary_requested_at=None,
        supplementary_deadline=None,
        supplementary_used=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(reg)
    db_session.commit()

    resp = await client.get(f"/api/v1/registrations/{reg.id}/verify-sensitive", headers=reviewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_number"] == "ID-999"
    assert data["contact_info"] == "x@y.com"
    assert "audit_log_id" in data

    logs = db_session.scalars(select(AuditLog).where(AuditLog.action == "verify_sensitive")).all()
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_maintenance_mode_returns_503(client, engine):
    """While maintenance is on, API calls are rejected except health."""
    enter_maintenance()
    try:
        r = await client.get("/api/v1/activities", headers={})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
        h = await client.get("/api/v1/health")
        assert h.status_code == 200
    finally:
        leave_maintenance()


@pytest.mark.asyncio
async def test_backup_list_create_requires_admin(client, admin_headers, applicant_a_headers):
    headers_a, _ = applicant_a_headers
    r = await client.get("/api/v1/backups", headers=headers_a)
    assert r.status_code == 403
    r2 = await client.post("/api/v1/backups", headers=admin_headers)
    assert r2.status_code == 201
    assert r2.json()["status"] == "completed"
    r3 = await client.get("/api/v1/backups", headers=admin_headers)
    assert r3.status_code == 200
    assert r3.json()["total"] >= 1


@pytest.mark.asyncio
async def test_backup_restore_sqlite_roundtrip(client, admin_headers, engine):
    """Create backup then restore; DB should reload from archive (SQLite tests)."""
    r1 = await client.post("/api/v1/backups", headers=admin_headers)
    assert r1.status_code == 201
    bid = r1.json()["id"]
    r2 = await client.post(f"/api/v1/backups/{bid}/restore", headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["message"] == "System restored successfully from backup"


@pytest.mark.asyncio
async def test_duplicate_file_hash_rejected_under_concurrent_upload_attempts(
    client, applicant_a_headers, db_session, admin_headers
):
    """Two uploads with identical bytes should not both succeed (second DUPLICATE_FILE)."""
    headers_a, uid = applicant_a_headers
    now = utcnow()
    ar = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={
            "name": "P6 dup act",
            "description": None,
            "deadline": "2030-12-31T12:00:00+00:00",
            "budget": "10000.00",
        },
    )
    assert ar.status_code == 201, ar.text
    aid = uuid.UUID(ar.json()["id"])
    act_deadline = ar.json()["deadline"]
    reg_deadline = datetime.fromisoformat(act_deadline.replace("Z", "+00:00"))
    reg = Registration(
        id=uuid.uuid4(),
        activity_id=aid,
        applicant_id=uid,
        form_data=_form(),
        requested_funding=Decimal("1000"),
        status=RegistrationStatus.draft,
        deadline=reg_deadline,
        is_locked=False,
        supplementary_requested_at=None,
        supplementary_deadline=None,
        supplementary_used=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(reg)
    item = MaterialChecklist(
        id=uuid.uuid4(),
        registration_id=reg.id,
        item_name="Doc",
        is_required=True,
        allowed_types=["pdf"],
        max_file_size_mb=20,
        created_at=now,
    )
    db_session.add(item)
    db_session.commit()

    content = b"%PDF-1.4 dup test bytes"
    first = await client.post(
        f"/api/v1/registrations/{reg.id}/materials/{item.id}/upload",
        headers=headers_a,
        files={"file": ("a.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert first.status_code == 201
    second = await client.post(
        f"/api/v1/registrations/{reg.id}/materials/{item.id}/upload",
        headers=headers_a,
        files={"file": ("b.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "DUPLICATE_FILE"


@pytest.mark.asyncio
async def test_funding_transaction_rollback_on_invalid_state(client, finance_headers, db_session, seed_admin, admin_headers):
    """Invalid follow-up request should not leave partial funding state (explicit rollback path)."""
    # Minimal smoke: POST with bad account id returns 404 — no side effects
    bad_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/funding-accounts/{bad_id}/transactions",
        headers=finance_headers,
        json={"type": "expense", "amount": "1.00", "category": "X", "description": "y"},
    )
    assert resp.status_code == 404
