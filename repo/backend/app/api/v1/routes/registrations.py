from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    require_applicant,
    require_reviewer,
    require_system_admin,
)
from app.models.enums import RegistrationStatus
from app.models.user import User
from app.schemas.registration_domain import (
    ChecklistItemCreate,
    ChecklistItemUpdate,
    MaterialLabelUpdate,
    RegistrationCreate,
    RegistrationUpdate,
    ReviewRequest,
    WaitlistPromoteRequest,
)
from app.services.phase4_checklist import Phase4ChecklistService
from app.services.phase4_materials import Phase4MaterialService
from app.services.phase4_registration import Phase4RegistrationService
from app.services.phase4_review import Phase4ReviewService
from app.services.phase4_sensitive import Phase4SensitiveService

router = APIRouter(tags=["registrations"])


def _reg_svc(db: Session = Depends(get_db)) -> Phase4RegistrationService:
    return Phase4RegistrationService(db)


def _chk_svc(db: Session = Depends(get_db)) -> Phase4ChecklistService:
    return Phase4ChecklistService(db)


def _mat_svc(db: Session = Depends(get_db)) -> Phase4MaterialService:
    return Phase4MaterialService(db)


def _rev_svc(db: Session = Depends(get_db)) -> Phase4ReviewService:
    return Phase4ReviewService(db)


def _sen_svc(db: Session = Depends(get_db)) -> Phase4SensitiveService:
    return Phase4SensitiveService(db)


@router.post("/registrations", status_code=status.HTTP_201_CREATED)
def post_registration(
    payload: RegistrationCreate,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.create(applicant, payload)


@router.get("/registrations")
def list_registrations(
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: RegistrationStatus | None = Query(default=None, alias="status"),
    activity_id: uuid.UUID | None = Query(default=None),
    sort: str | None = None,
):
    return svc.list_page(user, page=page, per_page=per_page, status_filter=status_filter, activity_id=activity_id, sort=sort)


@router.get("/registrations/{registration_id}")
def get_registration(
    registration_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.get(user, registration_id)


@router.get("/registrations/{registration_id}/verify-sensitive")
def verify_sensitive(
    request: Request,
    registration_id: uuid.UUID,
    reviewer: Annotated[User, Depends(require_reviewer)],
    svc: Phase4SensitiveService = Depends(_sen_svc),
):
    ip = request.client.host if request.client else "unknown"
    return svc.verify_sensitive(reviewer, registration_id, ip_address=ip)


@router.put("/registrations/{registration_id}")
def put_registration(
    registration_id: uuid.UUID,
    payload: RegistrationUpdate,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.update(applicant, registration_id, payload)


@router.delete("/registrations/{registration_id}")
def delete_registration(
    registration_id: uuid.UUID,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.delete(applicant, registration_id)


@router.patch("/registrations/{registration_id}/submit")
def submit_registration(
    registration_id: uuid.UUID,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.submit(applicant, registration_id)


@router.patch("/registrations/{registration_id}/cancel")
def cancel_registration(
    registration_id: uuid.UUID,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4RegistrationService = Depends(_reg_svc),
):
    return svc.cancel(applicant, registration_id)


@router.post("/registrations/{registration_id}/checklist", status_code=status.HTTP_201_CREATED)
def post_checklist(
    registration_id: uuid.UUID,
    payload: ChecklistItemCreate,
    admin: Annotated[User, Depends(require_system_admin)],
    svc: Phase4ChecklistService = Depends(_chk_svc),
):
    return svc.add_item(admin, registration_id, payload)


@router.get("/registrations/{registration_id}/checklist")
def get_checklist(
    registration_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4ChecklistService = Depends(_chk_svc),
):
    return svc.list_items(user, registration_id)


@router.get("/registrations/{registration_id}/checklist/{item_id}")
def get_checklist_item(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4ChecklistService = Depends(_chk_svc),
):
    return svc.get_item(user, registration_id, item_id)


@router.put("/registrations/{registration_id}/checklist/{item_id}")
def put_checklist_item(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ChecklistItemUpdate,
    admin: Annotated[User, Depends(require_system_admin)],
    svc: Phase4ChecklistService = Depends(_chk_svc),
):
    return svc.update_item(admin, registration_id, item_id, payload)


@router.delete("/registrations/{registration_id}/checklist/{item_id}")
def delete_checklist_item(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    admin: Annotated[User, Depends(require_system_admin)],
    svc: Phase4ChecklistService = Depends(_chk_svc),
):
    return svc.delete_item(admin, registration_id, item_id)


@router.post("/registrations/{registration_id}/materials/{item_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_material(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    applicant: Annotated[User, Depends(require_applicant)],
    file: UploadFile = File(...),
    svc: Phase4MaterialService = Depends(_mat_svc),
):
    return await svc.upload(applicant, registration_id, item_id, file)


@router.get("/registrations/{registration_id}/materials/{item_id}/versions")
def list_material_versions(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4MaterialService = Depends(_mat_svc),
):
    return svc.list_versions(user, registration_id, item_id)


@router.patch("/registrations/{registration_id}/materials/{item_id}/versions/{version_id}/label")
def patch_material_label(
    registration_id: uuid.UUID,
    item_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: MaterialLabelUpdate,
    applicant: Annotated[User, Depends(require_applicant)],
    svc: Phase4MaterialService = Depends(_mat_svc),
):
    return svc.patch_label(applicant, registration_id, item_id, version_id, payload.label)


@router.patch("/registrations/{registration_id}/review")
def patch_review(
    registration_id: uuid.UUID,
    payload: ReviewRequest,
    reviewer: Annotated[User, Depends(require_reviewer)],
    svc: Phase4ReviewService = Depends(_rev_svc),
):
    return svc.apply_review(reviewer, registration_id, payload)


@router.get("/registrations/{registration_id}/reviews")
def list_reviews(
    registration_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4ReviewService = Depends(_rev_svc),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    return svc.list_reviews(user, registration_id, page, per_page)


@router.get("/registrations/{registration_id}/reviews/{review_id}")
def get_review(
    registration_id: uuid.UUID,
    review_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4ReviewService = Depends(_rev_svc),
):
    return svc.get_review(user, registration_id, review_id)


@router.patch("/registrations/{registration_id}/waitlist-promote")
def waitlist_promote(
    registration_id: uuid.UUID,
    payload: WaitlistPromoteRequest,
    reviewer: Annotated[User, Depends(require_reviewer)],
    svc: Phase4ReviewService = Depends(_rev_svc),
):
    return svc.waitlist_promote(reviewer, registration_id, payload)
