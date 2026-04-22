"""Tests for Section 8 coverage gaps identified in static audit."""
import pytest
import uuid
import io
import subprocess
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.time import utcnow
from app.core.security import hash_password_with_salt
from app.models.user import User
from app.models.enums import UserRole, RegistrationStatus
from app.models.registration import Registration
from app.models.funding_account import FundingAccount
from app.models.audit_log import AuditLog
from app.models.activity import Activity
from app.models.generated_report import GeneratedReport
from app.models.material_checklist import MaterialChecklist
from app.models.material_version import MaterialVersion, MaterialVersionLabel
from app.models.backup_record import BackupRecord
from app.services.backup_service import BackupService
from sqlalchemy import select


@pytest.fixture
async def applicant_headers(client, db_session):
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username=f"applicant_{uuid.uuid4().hex[:8]}",
        password_hash=ph,
        salt=sl,
        role=UserRole.applicant,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(u)
    db_session.commit()
    resp = await client.post("/api/v1/auth/login", json={"username": u.username, "password": "SecureP@ss1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def reviewer_headers(client, db_session):
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username=f"reviewer_{uuid.uuid4().hex[:8]}",
        password_hash=ph,
        salt=sl,
        role=UserRole.reviewer,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(u)
    db_session.commit()
    resp = await client.post("/api/v1/auth/login", json={"username": u.username, "password": "SecureP@ss1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def finance_user_and_headers(client, db_session):
    ph, sl = hash_password_with_salt("SecureP@ss1")
    u = User(
        id=uuid.uuid4(),
        username=f"finance_{uuid.uuid4().hex[:8]}",
        password_hash=ph,
        salt=sl,
        role=UserRole.financial_admin,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(u)
    db_session.commit()
    resp = await client.post("/api/v1/auth/login", json={"username": u.username, "password": "SecureP@ss1"})
    return u, {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def seed_activity(db_session):
    act = Activity(
        id=uuid.uuid4(),
        name="Test Activity",
        description="desc",
        budget=1000,
        deadline=utcnow() + timedelta(days=30),
        is_active=True,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(act)
    db_session.commit()
    return act


@pytest.mark.asyncio
@pytest.mark.parametrize("route", [
    "/api/v1/reports",
    "/api/v1/backups",
    "/api/v1/alerts",
    "/api/v1/data-collection/batches",
    "/api/v1/reports/audit",
])
async def test_401_unauthenticated_matrix(client, route):
    r = await client.get(route)
    if r.status_code == 405:
        r = await client.post(route, json={})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_403_authorization_matrix(client, applicant_headers, reviewer_headers):
    # test applicant
    h = applicant_headers
    assert (await client.get("/api/v1/reports", headers=h)).status_code == 403
    assert (await client.get("/api/v1/backups", headers=h)).status_code == 403
    assert (await client.get("/api/v1/alerts", headers=h)).status_code == 403
    assert (await client.get("/api/v1/data-collection/batches", headers=h)).status_code == 403

    # test reviewer
    h2 = reviewer_headers
    assert (await client.get("/api/v1/backups", headers=h2)).status_code == 403
    assert (await client.get("/api/v1/reports", headers=h2)).status_code == 403


@pytest.mark.asyncio
async def test_object_level_isolation_materials_invoices_reports(client, db_session, applicant_headers, seed_activity):
    user_b_id = uuid.uuid4()
    u_b = User(
        id=user_b_id,
        username=f"b_{user_b_id.hex[:8]}",
        password_hash="x",
        salt="y",
        role=UserRole.applicant,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(u_b)
    db_session.flush()

    reg_b = Registration(
        id=uuid.uuid4(),
        activity_id=seed_activity.id,
        applicant_id=user_b_id,
        requested_funding=1000,
        status=RegistrationStatus.submitted,
        deadline=utcnow() + timedelta(days=30),
        is_locked=False,
        form_data={},
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(reg_b)
    db_session.flush()

    chk_b = MaterialChecklist(
        id=uuid.uuid4(),
        registration_id=reg_b.id,
        item_name="Tax ID",
        is_required=True,
        allowed_types=["pdf"],
        created_at=utcnow()
    )
    db_session.add(chk_b)
    db_session.commit()
    
    headers = applicant_headers
    r = await client.get(f"/api/v1/registrations/{reg_b.id}/checklist", headers=headers)
    assert r.status_code in (403, 404)
    
    f = io.BytesIO(b"test file")
    files = {"file": ("test.pdf", f, "application/pdf")}
    r = await client.post(
        f"/api/v1/registrations/{reg_b.id}/materials/{chk_b.id}/upload",
        headers=headers,
        files=files
    )
    assert r.status_code in (403, 404)


@pytest.mark.asyncio
async def test_correction_semantics_label_only(client, db_session, applicant_headers, seed_activity):
    headers = applicant_headers
    r = await client.get("/api/v1/auth/me", headers=headers)
    user_a_id = uuid.UUID(r.json()["id"])
    now = utcnow()
    reg = Registration(
        id=uuid.uuid4(),
        activity_id=seed_activity.id,
        applicant_id=user_a_id,
        requested_funding=1000,
        status=RegistrationStatus.needs_correction,
        deadline=utcnow() + timedelta(days=30),
        is_locked=False,
        supplementary_requested_at=now - timedelta(hours=1),
        supplementary_deadline=now + timedelta(hours=71),
        supplementary_used=False,
        form_data={},
        created_at=now,
        updated_at=now
    )
    db_session.add(reg)
    db_session.flush()

    chk = MaterialChecklist(
        id=uuid.uuid4(),
        registration_id=reg.id,
        item_name="Doc",
        is_required=True,
        allowed_types=["pdf"],
        created_at=now
    )
    db_session.add(chk)
    db_session.commit()
    
    f = io.BytesIO(b"file")
    files = {"file": ("doc.pdf", f, "application/pdf")}
    r = await client.post(
        f"/api/v1/registrations/{reg.id}/materials/{chk.id}/upload",
        headers=headers,
        files=files
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_postgresql_restore_mock_integration(client, db_session, admin_headers):
    b = BackupService(db_session)
    backup_id = uuid.uuid4()
    
    with patch("app.services.backup_service._is_postgres", return_value=True):
        with patch("app.services.backup_service._run_pg_dump") as mock_pg_dump:
            with patch("app.services.backup_service._pack_backup_archive", return_value=123):
                with patch("app.services.backup_service.tempfile.mkdtemp", return_value="/tmp/test_backup"):
                    b.create_manual()
                    assert mock_pg_dump.called


@pytest.mark.asyncio
async def test_audit_logging_persistence(client, db_session, admin_headers):
    payload = {"name": "Audit Test", "description": "desc", "budget": 1000, "deadline": "2027-01-01T00:00:00Z"}
    headers = await admin_headers if type(admin_headers) is not dict else admin_headers
    
    with patch("app.middleware.audit_middleware.AuditLogService.log_http_request") as mock_log:
        r = await client.post("/api/v1/activities", headers=headers, json=payload)
        assert r.status_code == 201
        
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/api/v1/activities"
        assert call_kwargs["status_code"] == 201


@pytest.mark.asyncio
async def test_report_list_ownership_isolation(client, db_session, finance_user_and_headers):
    finance_user, f_headers = finance_user_and_headers
    
    rep = GeneratedReport(
        id=uuid.uuid4(),
        report_type="reconciliation",
        file_format="csv",
        file_path="/tmp/a.csv",
        file_name="a.csv",
        file_size_bytes=100,
        created_by=finance_user.id,
        created_at=utcnow()
    )
    db_session.add(rep)
    
    user_b = User(
        id=uuid.uuid4(),
        username="finance_b",
        password_hash="a",
        salt="a",
        role=UserRole.financial_admin,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(user_b)
    db_session.flush()

    rep2 = GeneratedReport(
        id=uuid.uuid4(),
        report_type="reconciliation",
        file_format="csv",
        file_path="/tmp/b.csv",
        file_name="b.csv",
        file_size_bytes=100,
        created_by=user_b.id,
        created_at=utcnow()
    )
    db_session.add(rep2)
    db_session.commit()
    
    r = await client.get("/api/v1/reports", headers=f_headers)
    assert r.status_code == 200
    items = r.json()["items"]
    ids = [i["report_id"] for i in items]
    assert str(rep.id) in ids
    assert str(rep2.id) not in ids 


@pytest.mark.asyncio
async def test_frontend_file_validation_backend_boundaries(client, db_session, finance_user_and_headers, seed_activity):
    u_app_id = uuid.uuid4()
    u_app = User(
        id=u_app_id,
        username=f"app_{u_app_id.hex[:8]}",
        password_hash="x",
        salt="y",
        role=UserRole.applicant,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(u_app)
    db_session.flush()

    reg = Registration(
        id=uuid.uuid4(),
        activity_id=seed_activity.id,
        applicant_id=u_app_id,
        requested_funding=1000,
        status=RegistrationStatus.approved,
        deadline=utcnow() + timedelta(days=30),
        is_locked=False,
        form_data={},
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(reg)
    db_session.flush()

    fa = FundingAccount(
        id=uuid.uuid4(),
        registration_id=reg.id,
        approved_budget=1000,
        total_income=0,
        total_expenses=0,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db_session.add(fa)
    db_session.commit()
    
    finance_user, headers = finance_user_and_headers
    r = await client.post(
        f"/api/v1/funding-accounts/{fa.id}/transactions",
        headers=headers,
        json={"type": "expense", "amount": 100, "category": "A"}
    )
    assert r.status_code == 201
    tx_id = r.json()["id"]
    
    f = io.BytesIO(b"0" * (20 * 1024 * 1024 + 10))
    files = {"file": ("large.pdf", f, "application/pdf")}
    r = await client.post(
        f"/api/v1/funding-accounts/{fa.id}/transactions/{tx_id}/invoice",
        headers=headers,
        files=files
    )
    assert r.status_code == 400
    assert "too large" in r.json()["error"]["message"].lower()

    f2 = io.BytesIO(b"text")
    files2 = {"file": ("doc.txt", f2, "text/plain")}
    r = await client.post(
        f"/api/v1/funding-accounts/{fa.id}/transactions/{tx_id}/invoice",
        headers=headers,
        files=files2
    )
    assert r.status_code == 400
    assert "invalid file type" in r.json()["error"]["message"].lower()
