from __future__ import annotations

from fastapi import HTTPException, status

from app.core.http_errors import forbidden
from app.models.enums import RegistrationStatus, UserRole
from app.models.registration import Registration
from app.models.user import User


def can_view_registration(user: User, reg: Registration) -> bool:
    if user.role == UserRole.system_admin:
        return True
    if user.role == UserRole.applicant and reg.applicant_id == user.id:
        return True
    if user.role == UserRole.reviewer:
        return True
    if user.role == UserRole.financial_admin and reg.status == RegistrationStatus.approved:
        return True
    return False


def ensure_registration(reg: Registration | None) -> Registration:
    if reg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Registration not found")
    return reg


def ensure_registration_access(user: User, reg: Registration) -> None:
    if not can_view_registration(user, reg):
        raise forbidden("FORBIDDEN", "You do not have access to this registration")


def registration_filters_for_user(user: User) -> list:
    if user.role == UserRole.applicant:
        return [Registration.applicant_id == user.id]
    if user.role == UserRole.financial_admin:
        return [Registration.status == RegistrationStatus.approved]
    if user.role in (UserRole.reviewer, UserRole.system_admin):
        return []
    raise forbidden("FORBIDDEN", "Insufficient permissions")


def ensure_owner_applicant(user: User, reg: Registration) -> None:
    if user.role != UserRole.applicant or reg.applicant_id != user.id:
        raise forbidden("FORBIDDEN", "You do not own this registration")
