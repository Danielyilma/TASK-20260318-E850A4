from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password_with_salt
from app.core.time import utcnow
from app.models.enums import UserRole
from app.models.user import User


def seed() -> None:
    settings = get_settings()
    session = SessionLocal()
    try:
        existing = session.scalars(select(User).where(User.username == settings.system_admin_username)).first()
        if existing is not None:
            return

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
        session.add(user)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    seed()
