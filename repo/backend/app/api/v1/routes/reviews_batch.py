from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_reviewer
from app.models.user import User
from app.schemas.registration_domain import BatchReviewRequest
from app.services.phase4_review import Phase4ReviewService

router = APIRouter(tags=["reviews"])


def _svc(db: Session = Depends(get_db)) -> Phase4ReviewService:
    return Phase4ReviewService(db)


@router.post("/reviews/batch")
def post_reviews_batch(
    payload: BatchReviewRequest,
    reviewer: Annotated[User, Depends(require_reviewer)],
    svc: Phase4ReviewService = Depends(_svc),
):
    return svc.batch_review(reviewer, payload)
