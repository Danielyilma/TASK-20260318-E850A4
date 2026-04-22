from __future__ import annotations

from datetime import timedelta

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, hash_password_with_salt, verify_password
from app.core.time import as_utc, utcnow
from app.core.token_blocklist import is_jti_revoked, revoke_jti
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthMeResponse,
    AuthMeUpdate,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    LoginUser,
)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def _record_failed_login(self, user: User) -> None:
        now = utcnow()
        first = as_utc(user.first_failed_at)

        if first is not None and (now - first) > timedelta(minutes=5):
            user.failed_login_attempts = 0
            user.first_failed_at = None

        if user.failed_login_attempts == 0:
            user.first_failed_at = now

        user.failed_login_attempts += 1

        first = as_utc(user.first_failed_at)
        if user.failed_login_attempts >= 10 and first is not None:
            if (now - first) <= timedelta(minutes=5):
                user.is_locked = True
                user.locked_until = now + timedelta(minutes=30)

        user.updated_at = now

    def login(self, payload: LoginRequest) -> LoginResponse:
        user = self.users.get_by_username(payload.username)
        if user is None or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        now = utcnow()
        locked_until = as_utc(user.locked_until)
        if user.is_locked and locked_until is not None and locked_until <= now:
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0
            user.first_failed_at = None
            locked_until = None

        if locked_until is not None and locked_until > now:
            locked_until_iso = locked_until.isoformat().replace("+00:00", "Z")
            raise HTTPException(
                status.HTTP_423_LOCKED,
                detail=f"Account is locked. Try again after {locked_until_iso}",
                headers={"X-Error-Code": "ACCOUNT_LOCKED"},
            )

        if not verify_password(payload.password, user.password_hash, user.salt or ""):
            self._record_failed_login(user)
            self.db.commit()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        user.failed_login_attempts = 0
        user.first_failed_at = None
        user.is_locked = False
        user.locked_until = None
        user.updated_at = now

        settings = get_settings()
        token, expires_at, _jti = create_access_token(user_id=user.id, settings=settings)
        self.db.commit()
        return LoginResponse(
            user=LoginUser.model_validate(user),
            access_token=token,
            expires_at=expires_at,
        )

    def logout(self, token: str) -> None:
        try:
            payload = decode_access_token(token)
        except jwt.PyJWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
        revoke_jti(str(jti))

    def build_me_response(self, user: User) -> AuthMeResponse:
        id_number, contact_info = self._mask_sensitive(user)
        return AuthMeResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            id_number=id_number,
            contact_info=contact_info,
            is_locked=user.is_locked,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _mask_sensitive(self, user: User) -> tuple[str | None, str | None]:
        if user.role in (UserRole.system_admin, UserRole.applicant):
            return user.id_number, user.contact_info
        return "****", "****"

    def update_me(self, user: User, payload: AuthMeUpdate) -> AuthMeResponse:
        now = utcnow()
        if payload.contact_info is not None:
            user.contact_info = payload.contact_info
        if payload.id_number is not None:
            user.id_number = payload.id_number
        user.updated_at = now
        self.db.commit()
        self.db.refresh(user)
        return self.build_me_response(user)

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash, user.salt or ""):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

        pwd_hash, salt = hash_password_with_salt(payload.new_password)
        user.password_hash = pwd_hash
        user.salt = salt
        user.updated_at = utcnow()
        self.db.commit()
