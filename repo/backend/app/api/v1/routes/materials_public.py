from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.phase4_materials import Phase4MaterialService

router = APIRouter(tags=["materials"])


def _svc(db: Session = Depends(get_db)) -> Phase4MaterialService:
    return Phase4MaterialService(db)


@router.get("/materials/{version_id}/download")
def download_material(
    version_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Phase4MaterialService = Depends(_svc),
):
    mv, path = svc.download_path(user, version_id)
    return FileResponse(
        path,
        filename=mv.file_name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{mv.file_name}"'},
    )
