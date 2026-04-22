import uuid
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.activity import Activity
from app.models.enums import UserRole
from app.models.user import User


def test_activity_requires_name(db_session: Session) -> None:
    now = utcnow()
    activity = Activity(
        id=uuid.uuid4(),
        name=None,  # type: ignore[arg-type]
        description=None,
        deadline=now + timedelta(days=1),
        budget=100,
        is_active=True,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(activity)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_user_requires_username(db_session: Session) -> None:
    now = utcnow()
    user = User(
        id=uuid.uuid4(),
        username=None,  # type: ignore[arg-type]
        password_hash="x",
        salt="",
        role=UserRole.applicant,
        id_number=None,
        contact_info=None,
        is_locked=False,
        locked_until=None,
        failed_login_attempts=0,
        first_failed_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
