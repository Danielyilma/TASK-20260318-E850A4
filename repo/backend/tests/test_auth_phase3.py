from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == settings.system_admin_username
    assert body["user"]["role"] == "system_admin"


@pytest.mark.asyncio
async def test_brute_force_lockout_returns_423_on_next_login(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    wrong = {"username": settings.system_admin_username, "password": "WrongP@ss1"}

    for _ in range(10):
        resp = await client.post("/api/v1/auth/login", json=wrong)
        assert resp.status_code == 401, resp.text

    locked = await client.post("/api/v1/auth/login", json=wrong)
    assert locked.status_code == 423, locked.text
    err = locked.json()["error"]
    assert err["code"] == "ACCOUNT_LOCKED"
    assert "Try again after" in err["message"]


@pytest.mark.asyncio
async def test_get_users_forbidden_for_applicant(client: AsyncClient, db_session: Session) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("ApplicantP@ss1")
    applicant = User(
        id=uuid.uuid4(),
        username="rbac_applicant",
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
        json={"username": "rbac_applicant", "password": "ApplicantP@ss1"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_put_auth_me_updates_profile(client: AsyncClient, db_session: Session) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="me_user",
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

    login = await client.post("/api/v1/auth/login", json={"username": "me_user", "password": "SecureP@ss1"})
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.put(
        "/api/v1/auth/me",
        json={"contact_info": "new@example.com", "id_number": "ID-99"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["contact_info"] == "new@example.com"
    assert body["id_number"] == "ID-99"


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": settings.system_admin_password, "new_password": "NewAdminP@ss2"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["message"] == "Password changed successfully"

    old = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    assert old.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": "NewAdminP@ss2"},
    )
    assert new_login.status_code == 200, new_login.text


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongP@ss1", "new_password": "OtherNewP@ss2"},
        headers=headers,
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_change_password_weak_new_password(client: AsyncClient, seed_admin) -> None:
    settings = get_settings()
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": settings.system_admin_password, "new_password": "short"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "complexity" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(client: AsyncClient, db_session: Session) -> None:
    now = utcnow()
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username="inactive_u",
        password_hash=ph,
        salt=sl,
        role=UserRole.applicant,
        id_number=None,
        contact_info=None,
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(u)
    db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactive_u", "password": "SecureP@ss1"},
    )
    assert resp.status_code == 401
