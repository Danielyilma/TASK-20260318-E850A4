from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.token_blocklist import is_jti_revoked
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

__all__ = [
    "get_current_user",
    "get_db",
    "require_system_admin",
    "require_system_admin_create_user",
    "require_applicant",
    "require_reviewer",
    "require_financial_admin",
    "require_financial_or_system_admin",
]

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    jti = payload.get("jti")
    if not jti or is_jti_revoked(str(jti)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    user = UserRepository(db).get_by_id(uuid.UUID(str(sub)))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    return user


def require_system_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.system_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def require_system_admin_create_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.system_admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can create users",
        )
    return user


def require_applicant(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.applicant:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only applicants can perform this action")
    return user


def require_reviewer(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.reviewer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only reviewers can perform reviews")
    return user


def require_financial_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.financial_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only financial administrators can perform this action")
    return user


def require_financial_or_system_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role not in (UserRole.financial_admin, UserRole.system_admin):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user
