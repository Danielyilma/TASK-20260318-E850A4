from __future__ import annotations

import io
import uuid
from datetime import timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.enums import RegistrationStatus, UserRole
from app.models.registration import Registration
from app.models.user import User


def _form() -> dict:
    return {
        "project_title": "Street Library",
        "project_description": "Books",
        "target_beneficiaries": 100,
        "start_date": "2026-08-01",
        "end_date": "2026-12-31",
    }


@pytest.fixture
async def applicant_headers(client: AsyncClient, db_session: Session) -> dict[str, str]:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="phase4_applicant",
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
        json={"username": "phase4_applicant", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def reviewer_headers(client: AsyncClient, db_session: Session) -> dict[str, str]:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="phase4_reviewer",
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
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "phase4_reviewer", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def finance_headers(client: AsyncClient, db_session: Session) -> dict[str, str]:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="phase4_finance",
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
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "phase4_finance", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_registration_create_and_submit_flow(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Phase4 Act", "description": None, "deadline": deadline, "budget": 100000},
    )
    assert act.status_code == 201, act.text
    aid = act.json()["id"]

    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 5000},
    )
    assert reg.status_code == 201, reg.text
    rid = reg.json()["id"]

    chk = await client.post(
        f"/api/v1/registrations/{rid}/checklist",
        headers=admin_headers,
        json={"item_name": "ID", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    assert chk.status_code == 201, chk.text
    item_id = chk.json()["id"]

    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj trailer<<>>\n%%EOF"
    up = await client.post(
        f"/api/v1/registrations/{rid}/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("doc.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert up.status_code == 201, up.text
    vid = up.json()["id"]

    lbl = await client.patch(
        f"/api/v1/registrations/{rid}/materials/{item_id}/versions/{vid}/label",
        headers=applicant_headers,
        json={"label": "submitted"},
    )
    assert lbl.status_code == 200, lbl.text

    sub = await client.patch(f"/api/v1/registrations/{rid}/submit", headers=applicant_headers)
    assert sub.status_code == 200, sub.text
    assert sub.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_duplicate_hash_rejection(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Dup Act", "description": None, "deadline": deadline, "budget": 50000},
    )
    aid = act.json()["id"]

    r1 = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 1000},
    )
    r2 = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 1000},
    )
    rid1, rid2 = r1.json()["id"], r2.json()["id"]

    c1 = await client.post(
        f"/api/v1/registrations/{rid1}/checklist",
        headers=admin_headers,
        json={"item_name": "A", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    c2 = await client.post(
        f"/api/v1/registrations/{rid2}/checklist",
        headers=admin_headers,
        json={"item_name": "B", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    i1, i2 = c1.json()["id"], c2.json()["id"]

    content = b"%PDF-duplicate\nsame-bytes"
    assert (
        await client.post(
            f"/api/v1/registrations/{rid1}/materials/{i1}/upload",
            headers=applicant_headers,
            files={"file": ("a.pdf", io.BytesIO(content), "application/pdf")},
        )
    ).status_code == 201
    dup = await client.post(
        f"/api/v1/registrations/{rid2}/materials/{i2}/upload",
        headers=applicant_headers,
        files={"file": ("b.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert dup.status_code == 400
    assert dup.json()["error"]["code"] == "DUPLICATE_FILE"


@pytest.mark.asyncio
async def test_review_invalid_transition_draft_to_approve(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
    reviewer_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "SM Act", "description": None, "deadline": deadline, "budget": 90000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 2000},
    )
    rid = reg.json()["id"]
    resp = await client.patch(
        f"/api/v1/registrations/{rid}/review",
        headers=reviewer_headers,
        json={"action": "approve", "comment": "nope"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_overspend_confirmation_required(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
    reviewer_headers: dict[str, str],
    finance_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Fin Act", "description": None, "deadline": deadline, "budget": 200000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 10000},
    )
    rid = reg.json()["id"]
    chk = await client.post(
        f"/api/v1/registrations/{rid}/checklist",
        headers=admin_headers,
        json={"item_name": "Doc", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    item_id = chk.json()["id"]
    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3"
    up = await client.post(
        f"/api/v1/registrations/{rid}/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert up.status_code == 201
    vid = up.json()["id"]
    await client.patch(
        f"/api/v1/registrations/{rid}/materials/{item_id}/versions/{vid}/label",
        headers=applicant_headers,
        json={"label": "submitted"},
    )
    await client.patch(f"/api/v1/registrations/{rid}/submit", headers=applicant_headers)
    rv = await client.patch(
        f"/api/v1/registrations/{rid}/review",
        headers=reviewer_headers,
        json={"action": "approve", "comment": "ok"},
    )
    assert rv.status_code == 200

    fac = await client.get(f"/api/v1/registrations/{rid}/funding", headers=finance_headers)
    assert fac.status_code == 200
    account_id = fac.json()["id"]

    first = await client.post(
        f"/api/v1/funding-accounts/{account_id}/transactions",
        headers=finance_headers,
        json={"type": "expense", "amount": 6000, "category": "c", "description": "d"},
    )
    assert first.status_code == 201

    warn = await client.post(
        f"/api/v1/funding-accounts/{account_id}/transactions",
        headers=finance_headers,
        json={"type": "expense", "amount": 6000, "category": "c2", "description": "push over 110%"},
    )
    assert warn.status_code == 403
    body = warn.json()
    assert body["error"]["code"] == "OVERSPEND_CONFIRMATION_REQUIRED"

    ok = await client.post(
        f"/api/v1/funding-accounts/{account_id}/transactions",
        headers=finance_headers,
        json={
            "type": "expense",
            "amount": 6000,
            "category": "c2",
            "description": "push over 110%",
            "override_confirmed": True,
        },
    )
    assert ok.status_code == 201


@pytest.mark.asyncio
async def test_supplementary_expired_blocks_upload(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
    reviewer_headers: dict[str, str],
    db_session: Session,
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Sup Act", "description": None, "deadline": deadline, "budget": 80000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 3000},
    )
    rid = reg.json()["id"]
    chk = await client.post(
        f"/api/v1/registrations/{rid}/checklist",
        headers=admin_headers,
        json={"item_name": "ID2", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    item_id = chk.json()["id"]
    pdf = b"%PDF-sup\n"
    up = await client.post(
        f"/api/v1/registrations/{rid}/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("s.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    vid = up.json()["id"]
    await client.patch(
        f"/api/v1/registrations/{rid}/materials/{item_id}/versions/{vid}/label",
        headers=applicant_headers,
        json={"label": "submitted"},
    )
    await client.patch(f"/api/v1/registrations/{rid}/submit", headers=applicant_headers)
    await client.patch(
        f"/api/v1/registrations/{rid}/review",
        headers=reviewer_headers,
        json={
            "action": "request_correction",
            "comment": "fix",
            "correction_reason": "Please re-upload clearer scan.",
        },
    )

    row = db_session.get(Registration, uuid.UUID(rid))
    assert row is not None
    row.supplementary_deadline = utcnow() - timedelta(hours=1)
    db_session.commit()

    pdf2 = b"%PDF-sup2\n"
    blocked = await client.post(
        f"/api/v1/registrations/{rid}/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("s2.pdf", io.BytesIO(pdf2), "application/pdf")},
    )
    assert blocked.status_code == 400
    assert blocked.json()["error"]["code"] == "SUPPLEMENTARY_EXPIRED"


@pytest.mark.asyncio
async def test_verify_sensitive_unmasks_applicant(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
    reviewer_headers: dict[str, str],
    db_session: Session,
) -> None:
    u = db_session.scalars(select(User).where(User.username == "phase4_applicant")).first()
    assert u is not None
    u.id_number = "ID-VERIFY-1"
    u.contact_info = "applicant@example.com"
    db_session.commit()

    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Sens Act", "description": None, "deadline": deadline, "budget": 12000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 900},
    )
    rid = reg.json()["id"]

    # Submit so reviewer can access
    await client.patch(f"/api/v1/registrations/{rid}/submit", headers=applicant_headers)

    resp = await client.get(f"/api/v1/registrations/{rid}/verify-sensitive", headers=reviewer_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id_number"] == "ID-VERIFY-1"
    assert data["contact_info"] == "applicant@example.com"
    assert data["registration_id"] == rid
    assert data["applicant_id"]
    assert data["audit_log_id"]


@pytest.mark.asyncio
async def test_put_transaction_overspend_requires_override(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
    reviewer_headers: dict[str, str],
    finance_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Put Fin", "description": None, "deadline": deadline, "budget": 200000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 10000},
    )
    rid = reg.json()["id"]
    chk = await client.post(
        f"/api/v1/registrations/{rid}/checklist",
        headers=admin_headers,
        json={"item_name": "Doc", "is_required": True, "allowed_types": ["pdf"], "max_file_size_mb": 20},
    )
    item_id = chk.json()["id"]
    pdf = b"%PDF-put\n"
    up = await client.post(
        f"/api/v1/registrations/{rid}/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert up.status_code == 201
    vid = up.json()["id"]
    await client.patch(
        f"/api/v1/registrations/{rid}/materials/{item_id}/versions/{vid}/label",
        headers=applicant_headers,
        json={"label": "submitted"},
    )
    await client.patch(f"/api/v1/registrations/{rid}/submit", headers=applicant_headers)
    await client.patch(
        f"/api/v1/registrations/{rid}/review",
        headers=reviewer_headers,
        json={"action": "approve", "comment": "ok"},
    )

    fac = await client.get(f"/api/v1/registrations/{rid}/funding", headers=finance_headers)
    account_id = fac.json()["id"]

    first = await client.post(
        f"/api/v1/funding-accounts/{account_id}/transactions",
        headers=finance_headers,
        json={"type": "expense", "amount": 5000, "category": "c", "description": "first"},
    )
    assert first.status_code == 201
    tx_id = first.json()["id"]

    warn = await client.put(
        f"/api/v1/funding-accounts/{account_id}/transactions/{tx_id}",
        headers=finance_headers,
        json={"amount": 12000},
    )
    assert warn.status_code == 403
    assert warn.json()["error"]["code"] == "OVERSPEND_CONFIRMATION_REQUIRED"

    ok = await client.put(
        f"/api/v1/funding-accounts/{account_id}/transactions/{tx_id}",
        headers=finance_headers,
        json={"amount": 12000, "override_confirmed": True},
    )
    assert ok.status_code == 200
    assert float(ok.json()["amount"]) == 12000.0


@pytest.mark.asyncio
async def test_registration_update_rejects_over_activity_budget(
    client: AsyncClient,
    admin_headers: dict[str, str],
    applicant_headers: dict[str, str],
) -> None:
    deadline = (utcnow() + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    act = await client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Budget cap", "description": None, "deadline": deadline, "budget": 1000},
    )
    aid = act.json()["id"]
    reg = await client.post(
        "/api/v1/registrations",
        headers=applicant_headers,
        json={"activity_id": aid, "form_data": _form(), "requested_funding": 500},
    )
    rid = reg.json()["id"]
    resp = await client.put(
        f"/api/v1/registrations/{rid}",
        headers=applicant_headers,
        json={"requested_funding": 5000},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
