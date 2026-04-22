from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AuthMeResponse,
    AuthMeUpdate,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService

router = APIRouter()
bearer_required = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    resp = AuthService(db).login(payload)
    ip = request.client.host if request.client else "unknown"
    AuditLogService(db).append(
        user_id=resp.user.id,
        username=resp.user.username,
        action="login",
        resource_type="session",
        resource_id=None,
        details={"outcome": "success"},
        ip_address=ip,
    )
    db.commit()
    return resp


@router.post("/logout", response_model=LogoutResponse)
def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_required)],
    db: Session = Depends(get_db),
) -> LogoutResponse:
    AuthService(db).logout(credentials.credentials)
    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=AuthMeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthMeResponse:
    return AuthService(db).build_me_response(user)


@router.put("/me", response_model=AuthMeResponse)
def update_me(
    payload: AuthMeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    return AuthService(db).update_me(user, payload)


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    AuthService(db).change_password(user, payload)
    return ChangePasswordResponse(message="Password changed successfully")
