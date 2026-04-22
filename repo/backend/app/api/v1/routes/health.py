from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.errors import ErrorBody, ErrorResponse
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])
_health_service = HealthService()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service and database health",
    responses={
        503: {"model": ErrorResponse, "description": "Database unavailable"},
    },
)
def health_check(db: Session = Depends(get_db)):
    try:
        _health_service.check_database(db)
    except SQLAlchemyError:
        body = ErrorResponse(
            error=ErrorBody(code="INTERNAL_ERROR", message="Database unavailable"),
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body.model_dump())
    return HealthResponse(status="ok")
