from __future__ import annotations

from fastapi import HTTPException, status


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=message,
        headers={"X-Error-Code": code},
    )


def bad_request(code: str, message: str) -> HTTPException:
    return api_error(status.HTTP_400_BAD_REQUEST, code, message)


def forbidden(code: str, message: str) -> HTTPException:
    return api_error(status.HTTP_403_FORBIDDEN, code, message)
