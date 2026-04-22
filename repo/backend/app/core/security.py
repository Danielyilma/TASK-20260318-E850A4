from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings, get_settings


def decrypt_config_secret(value: str, key: str | None) -> str:
    """
    Decrypt values formatted as ENC(<fernet-token>) or return plain value.
    """
    if not isinstance(value, str):
        return value
    if not value.startswith("ENC(") or not value.endswith(")"):
        return value
    if not key:
        raise ValueError("CONFIG_ENCRYPTION_KEY is required to decrypt ENC(...) settings")
    token = value[4:-1].encode("utf-8")
    try:
        return Fernet(key.encode("utf-8")).decrypt(token).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ValueError("Failed to decrypt encrypted configuration value") from exc


def generate_salt() -> str:
    """Return a unique per-user salt stored alongside the password hash."""
    return secrets.token_hex(32)


def hash_password_with_salt(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash password using bcrypt; salt string is stored separately for auditing/extension."""
    salt_value = salt or generate_salt()
    combined = (password + salt_value).encode("utf-8")
    hashed = bcrypt.hashpw(combined, bcrypt.gensalt()).decode("utf-8")
    return hashed, salt_value


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    try:
        if not salt:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        combined = (password + salt).encode("utf-8")
        return bcrypt.checkpw(combined, password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, user_id: uuid.UUID, settings: Settings | None = None) -> tuple[str, datetime, str]:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expires,
        "iat": now,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires, jti


def decode_access_token(token: str, *, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], leeway=10)
