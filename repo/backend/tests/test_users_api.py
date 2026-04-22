from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user_as_system_admin(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "new_reviewer",
            "password": "SecureP@ss1",
            "role": "reviewer",
            "id_number": "R-1",
            "contact_info": "rev@example.com",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["username"] == "new_reviewer"
    assert body["role"] == "reviewer"
    assert body["is_locked"] is False


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    resp = await client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert body["page"] == 1
    assert body["per_page"] == 20
    assert isinstance(body["total"], int)


@pytest.mark.asyncio
async def test_create_user_conflict_duplicate_username(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "username": "dup_user_x",
        "password": "SecureP@ss1",
        "role": "applicant",
    }
    first = await client.post("/api/v1/users", headers=admin_headers, json=payload)
    assert first.status_code == 201, first.text

    second = await client.post("/api/v1/users", headers=admin_headers, json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_get_user_detail(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={"username": "detail_user", "password": "SecureP@ss1", "role": "applicant"},
    )
    assert created.status_code == 201, created.text
    uid = created.json()["id"]

    resp = await client.get(f"/api/v1/users/{uid}", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == "detail_user"


@pytest.mark.asyncio
async def test_unlock_not_locked_returns_409(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={"username": "unlock_target", "password": "SecureP@ss1", "role": "applicant"},
    )
    assert created.status_code == 201, created.text
    uid = created.json()["id"]

    resp = await client.post(f"/api/v1/users/{uid}/unlock", headers=admin_headers)
    assert resp.status_code == 409
    assert "not locked" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_applicant_cannot_create_user(client: AsyncClient, db_session: Session) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    applicant = User(
        id=uuid.uuid4(),
        username="applicant_creator",
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
        json={"username": "applicant_creator", "password": "SecureP@ss1"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "should_fail", "password": "SecureP@ss1", "role": "applicant"},
    )
    assert resp.status_code == 403
    assert "system administrators" in resp.json()["error"]["message"].lower()
