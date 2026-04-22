from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.activity import Activity
from app.models.enums import RegistrationStatus, UserRole
from app.models.registration import Registration
from app.models.user import User


def _future_deadline() -> str:
    return (utcnow() + timedelta(days=30)).isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_create_activity(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "2026 Community Development Grant",
        "description": "Annual grant for community projects",
        "deadline": _future_deadline(),
        "budget": 500000.00,
    }
    resp = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == payload["name"]
    assert body["budget"] == 500000.0
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_get_activities(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "Listable Activity",
        "description": None,
        "deadline": _future_deadline(),
        "budget": 1000.00,
    }
    created = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    assert created.status_code == 201

    resp = await client.get("/api/v1/activities", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["per_page"] == 20
    assert isinstance(body["items"], list)
    assert any(item["name"] == "Listable Activity" for item in body["items"])


@pytest.mark.asyncio
async def test_get_single_activity(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "Single Activity",
        "description": "d",
        "deadline": _future_deadline(),
        "budget": 2500.50,
    }
    created = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    activity_id = created.json()["id"]

    resp = await client.get(f"/api/v1/activities/{activity_id}", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == activity_id


@pytest.mark.asyncio
async def test_update_activity(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "Updatable Activity",
        "description": None,
        "deadline": _future_deadline(),
        "budget": 100.00,
    }
    created = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    activity_id = created.json()["id"]

    new_deadline = (utcnow() + timedelta(days=40)).isoformat().replace("+00:00", "Z")
    resp = await client.put(
        f"/api/v1/activities/{activity_id}",
        json={"name": "Updated Name", "deadline": new_deadline, "budget": 200.00},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Updated Name"
    assert body["budget"] == 200.0


@pytest.mark.asyncio
async def test_delete_activity(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "Deletable Activity",
        "description": None,
        "deadline": _future_deadline(),
        "budget": 50.00,
    }
    created = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    activity_id = created.json()["id"]

    resp = await client.delete(f"/api/v1/activities/{activity_id}", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["message"] == "Activity deleted successfully"

    missing = await client.get(f"/api/v1/activities/{activity_id}", headers=admin_headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_create_activity_rejects_non_positive_budget(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "name": "Bad Budget",
        "description": None,
        "deadline": _future_deadline(),
        "budget": -10,
    }
    resp = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_activity_requires_future_deadline(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    past = (utcnow() - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    payload = {
        "name": "Past Deadline",
        "description": None,
        "deadline": past,
        "budget": 10,
    }
    resp = await client.post("/api/v1/activities", json=payload, headers=admin_headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_delete_activity_conflict_when_registrations_exist(
    client: AsyncClient, admin_headers: dict[str, str], db_session: Session
) -> None:
    activity_id = uuid.uuid4()
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    applicant = User(
        id=uuid.uuid4(),
        username="applicant_one",
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
    db_session.add(
        Activity(
            id=activity_id,
            name="Blocked Delete",
            description=None,
            deadline=utcnow() + timedelta(days=30),
            budget=Decimal("10"),
            is_active=True,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.flush()
    db_session.add(applicant)
    db_session.flush()
    db_session.add(
        Registration(
            id=uuid.uuid4(),
            activity_id=activity_id,
            applicant_id=applicant.id,
            form_data={
                "project_title": "t",
                "project_description": "d",
                "target_beneficiaries": 1,
                "start_date": "2026-08-01",
                "end_date": "2026-12-31",
            },
            requested_funding=Decimal("100"),
            status=RegistrationStatus.draft,
            deadline=utcnow() + timedelta(days=30),
            is_locked=False,
            supplementary_requested_at=None,
            supplementary_deadline=None,
            supplementary_used=False,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    resp = await client.delete(f"/api/v1/activities/{activity_id}", headers=admin_headers)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_activities_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/activities")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_activity_forbidden_for_non_admin(client: AsyncClient, db_session: Session) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    applicant = User(
        id=uuid.uuid4(),
        username="applicant_two",
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
    db_session.add(applicant)
    db_session.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "applicant_two", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    payload = {
        "name": "Should Fail",
        "description": None,
        "deadline": _future_deadline(),
        "budget": 10,
    }
    resp = await client.post("/api/v1/activities", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": "WrongPassword!1"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"
