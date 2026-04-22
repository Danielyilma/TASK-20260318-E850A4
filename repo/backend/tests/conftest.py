import os
from collections.abc import Generator

# Ensure deterministic auth settings before importing the application package graph.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("SYSTEM_ADMIN_USERNAME", "admin")
os.environ.setdefault("SYSTEM_ADMIN_PASSWORD", "AdminP@ss1")
os.environ.setdefault("UPLOAD_ROOT", "/tmp/arfamp-test-uploads")
os.environ.setdefault("BACKUP_ROOT", "/tmp/arfamp-test-backups")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import importlib

from app.core.database import get_db
from app.main import app
from app.models.base import Base

importlib.import_module("app.models")  # register ORM tables on Base.metadata for create_all


@pytest.fixture(autouse=True)
def _reset_runtime_state() -> Generator[None, None, None]:
    from app.core.config import get_settings
    from app.core.token_blocklist import clear_blocklist

    get_settings.cache_clear()
    clear_blocklist()
    yield
    get_settings.cache_clear()
    clear_blocklist()


@pytest.fixture(scope="function")
def engine():
    database_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        pool_kw = {}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            pool_kw = {"poolclass": StaticPool}
        eng = create_engine(database_url, connect_args=connect_args, **pool_kw)

        @event.listens_for(eng, "connect")
        def _sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-redef]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    else:
        eng = create_engine(database_url)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_admin(db_session: Session):
    import uuid

    from app.core.config import get_settings
    from app.core.security import hash_password_with_salt
    from app.core.time import utcnow
    from app.models.enums import UserRole
    from app.models.user import User

    settings = get_settings()
    now = utcnow()
    pwd_hash, salt = hash_password_with_salt(settings.system_admin_password)
    user = User(
        id=uuid.uuid4(),
        username=settings.system_admin_username,
        password_hash=pwd_hash,
        salt=salt,
        role=UserRole.system_admin,
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
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
async def client(engine) -> AsyncClient:
    TestingSessionLocal = sessionmaker(bind=engine)

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_headers(client: AsyncClient, seed_admin) -> dict[str, str]:
    from app.core.config import get_settings

    settings = get_settings()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.system_admin_username, "password": settings.system_admin_password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
