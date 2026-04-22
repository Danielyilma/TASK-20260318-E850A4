from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Activity Registration Platform API"
    database_url: str = "postgresql://app:app@localhost:5432/app"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    config_encryption_key: str | None = None

    system_admin_username: str = "admin"
    system_admin_password: str = "AdminP@ss1"

    upload_root: str = "data/uploads"
    backup_root: str = "data/backups"
    backup_daily_enabled: bool = True
    backup_daily_hour_utc: int = Field(default=2, ge=0, le=23)
    backup_retention_days: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def decrypt_sensitive_settings(self):
        from app.core.security import decrypt_config_secret

        self.jwt_secret_key = decrypt_config_secret(self.jwt_secret_key, self.config_encryption_key)
        self.system_admin_password = decrypt_config_secret(self.system_admin_password, self.config_encryption_key)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def parse_cors_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]
