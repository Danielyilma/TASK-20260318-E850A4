from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings, parse_cors_origins
from app.exceptions import AppError
from app.middleware import AuditMiddleware
from app.middleware.maintenance_middleware import MaintenanceMiddleware
from app.schemas.errors import ErrorBody, ErrorResponse

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(MaintenanceMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = exc.headers.get("X-Error-Code") if exc.headers else None
    if not code:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_409_CONFLICT:
            code = "CONFLICT"
        elif exc.status_code == status.HTTP_423_LOCKED:
            code = "ACCOUNT_LOCKED"
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "VALIDATION_ERROR"
        else:
            code = "INTERNAL_ERROR"
    body = ErrorResponse(error=ErrorBody(code=code, message=str(exc.detail)))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = "Request validation failed"
    if exc.errors():
        first = exc.errors()[0]
        loc = ".".join(str(x) for x in first.get("loc", ()) if x != "body")
        message = f"{loc}: {first.get('msg', 'invalid')}" if loc else str(first.get("msg", message))
    body = ErrorResponse(error=ErrorBody(code="VALIDATION_ERROR", message=message))
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code="INTERNAL_ERROR", message="An unexpected error occurred"),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())


app.include_router(api_router, prefix="/api/v1")
